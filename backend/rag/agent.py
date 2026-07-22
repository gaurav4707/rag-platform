"""Conversational RAG Agent.

Orchestrates tool execution and generates grounded responses using the Prompt Builder.
"""

import logging
import uuid
from typing import Any, AsyncGenerator

from langchain_core.messages import ToolMessage

from backend.models.rag_models import ChatResult, RetrievalResult, SourceItem
from backend.rag.tool_executor import ToolExecutor, ConversationState, ToolExecutionResult, get_tool_executor
from backend.rag.prompts import build_prompt, build_system_prompt
from backend.rag.citations import build_sources
from backend.rag.retrieval_utils import merge_retrieval_results
from backend.providers import get_llm

logger = logging.getLogger(__name__)


def invoke(question: str) -> ChatResult:
    """Process a question and return a complete ChatResult.

    Flow:
    1. ToolExecutor handles multi-tool orchestration loop
    2. Returns final ChatResult with answer, sources, and tool calls
    """
    logger.debug("Processing question: %s", question[:100])
    executor = get_tool_executor()
    return executor.execute(question)


async def stream_events(question: str) -> AsyncGenerator[tuple[str, object], None]:
    """Stream events for the chat response as an async generator.

    Yields tuples of (kind, data) where kind is one of:
    - "tool_calls": ToolCall object with tool_name, input, output, artifact
    - "messages": MessageChunk object with text content
    - "metadata": dict with sources and tool_calls

    This is a true async generator - it yields events as they are produced
    by the LLM stream, without buffering the entire response.
    """
    logger.debug("Streaming question: %s", question[:100])

    executor = get_tool_executor()
    llm = get_llm()
    tools = executor.tools
    tool_map = executor.tool_map

    state = ConversationState()
    state.add_user_message(question)

    iteration = 0
    max_iterations = executor.max_iterations
    max_tools_per_response = executor.max_tools_per_response

    while iteration < max_iterations:
        iteration += 1
        logger.debug("Tool loop iteration %d/%d", iteration, max_iterations)

        # Bind tools to LLM for this iteration
        llm_with_tools = llm.bind_tools(tools)

        # Get LLM response
        response = llm_with_tools.invoke(state.get_messages_for_llm())

        # Check if LLM wants to call tools
        tool_calls = getattr(response, "tool_calls", None)
        logger.debug(
            "LLM response: iteration=%d type=%s content_repr=%r tool_calls=%s",
            iteration,
            type(response).__name__,
            response.content,
            [tc["name"] for tc in (tool_calls or [])],
        )
        if not tool_calls:
# No tool calls - final answer, stream it
            logger.debug("LLM returned final answer (no tool calls)")
            final_answer = response.content if isinstance(response.content, str) else str(response.content or "")
            async for item in _stream_final_answer(state, final_answer, llm):
                yield item
            return

        # Limit tools per response
        if len(tool_calls) > max_tools_per_response:
            logger.warning(
                "LLM requested %d tools, limiting to %d",
                len(tool_calls),
                max_tools_per_response,
            )
            tool_calls = tool_calls[:max_tools_per_response]

        # Execute all tool calls
        for tool_call in tool_calls:
            tool_name = tool_call["name"]
            tool_input = tool_call.get("args", {})
            tool_call_id = tool_call.get("id", "")

            logger.debug("Executing tool: %s with input: %s", tool_name, tool_input)

            execution_result = _execute_tool_direct(tool_map, tool_name, tool_input)
            state.tool_execution_results.append(execution_result)

            # Record for final output
            state.tool_calls.append({
                "tool_name": tool_name,
                "input": tool_input,
                "output": execution_result.content,
            })

            # Yield tool call event for streaming
            tool_call_data = type("ToolCall", (), {
                "tool_name": tool_name,
                "input": tool_input,
                "output": execution_result.content,
                "artifact": execution_result.artifact,
            })()
            yield "tool_calls", tool_call_data

            # Add tool result to conversation
            state.add_tool_message(
                tool_call_id=tool_call_id,
                content=execution_result.content,
                artifact=execution_result.artifact,
            )

            # Track retrieval results for citations
            if tool_name == "retrieve_context" and execution_result.artifact:
                state.retrieval_results.append(execution_result.artifact)

        # Add assistant message with tool calls to conversation
        state.add_assistant_message(
            content=str(response.content or ""),
            tool_calls=tool_calls,
        )

    # Max iterations exceeded
    logger.warning("Max tool iterations (%d) exceeded", max_iterations)
    error_msg = f"Maximum tool iterations ({max_iterations}) exceeded. Stopping execution."
    async for event in _stream_error_result(state, error_msg):
        yield event
    return


def _execute_tool_direct(tool_map: dict, tool_name: str, tool_input: dict) -> ToolExecutionResult:
    """Execute a single tool directly (for streaming context)."""
    import time
    start_time = time.perf_counter()

    tool = tool_map.get(tool_name)
    if tool is None:
        return ToolExecutionResult(
            success=False,
            content=f"Error: Unknown tool '{tool_name}'",
            artifact=None,
            duration_ms=(time.perf_counter() - start_time) * 1000,
            error=f"Tool '{tool_name}' not found in registry",
            tool_name=tool_name,
            tool_input=tool_input,
        )

    try:
        # Use ToolCall format so LangChain returns a ToolMessage with artifact
        tool_call = {
            "type": "tool_call",
            "name": tool_name,
            "args": tool_input,
            "id": str(uuid.uuid4()),
        }
        result = tool.invoke(tool_call)

        if isinstance(result, ToolMessage):
            content = result.content if isinstance(result.content, str) else str(result.content)
            artifact = result.artifact
        elif isinstance(result, tuple) and len(result) == 2:
            content = result[0] if isinstance(result[0], str) else str(result[0])
            artifact = result[1]
        else:
            content = str(result)
            artifact = result

        duration_ms = (time.perf_counter() - start_time) * 1000
        logger.debug("Tool '%s' completed in %.1fms", tool_name, duration_ms)

        return ToolExecutionResult(
            success=True,
            content=content,
            artifact=artifact,
            duration_ms=duration_ms,
            tool_name=tool_name,
            tool_input=tool_input,
        )

    except Exception as e:
        duration_ms = (time.perf_counter() - start_time) * 1000
        logger.exception("Tool '%s' failed: %s", tool_name, e)
        return ToolExecutionResult(
            success=False,
            content=f"Error executing tool '{tool_name}': {str(e)}",
            artifact=None,
            duration_ms=duration_ms,
            error=str(e),
            tool_name=tool_name,
            tool_input=tool_input,
        )


async def _stream_final_answer(
    state: ConversationState,
    answer: str,
    llm: Any,
) -> AsyncGenerator[tuple[str, object], None]:
    """Stream the final answer and yield metadata."""
    merged_retrieval = merge_retrieval_results(state.retrieval_results)

    if answer.strip():
        logger.info(
            "_stream_final_answer: using LLM answer len=%d repr=%r",
            len(answer),
            answer[:200],
        )
        message_chunk = type("MessageChunk", (), {"text": answer})()
        yield "messages", message_chunk
    else:
        logger.info("_stream_final_answer: LLM answer empty, generating via prompt")
        user_question = state.messages[0].content if state.messages else ""

        if isinstance(merged_retrieval, RetrievalResult):
            prompt = build_prompt(user_question, merged_retrieval)
        else:
            tool_results = ""
            for tc in state.tool_calls:
                tool_results += f"Tool: {tc['tool_name']}\nInput: {tc['input']}\nResult: {tc['output']}\n\n"
            prompt = (
                build_system_prompt()
                + "\n\nUser Question:\n" + user_question
                + ("\n\nTool Results:\n" + tool_results if tool_results else "")
                + "\n\nAnswer:"
            )

        async for chunk in llm.astream(prompt):
            if chunk.content:
                message_chunk = type("MessageChunk", (), {"text": chunk.content})()
                yield "messages", message_chunk

    # Yield final metadata with sources
    if isinstance(merged_retrieval, RetrievalResult):
        sources = build_sources(merged_retrieval)
    else:
        if merged_retrieval is not None:
            logger.warning(
                "Expected RetrievalResult for citations, got %s. Skipping citation generation.",
                type(merged_retrieval).__name__,
            )
        sources = []
    yield "metadata", {
        "sources": [
            {
                "document": s.document,
                "page": s.page,
                "document_id": s.document_id,
                "score": s.score,
            }
            for s in sources
        ],
        "tool_calls": state.tool_calls,
    }


async def _stream_error_result(
    state: ConversationState,
    error_msg: str,
) -> AsyncGenerator[tuple[str, object], None]:
    """Stream error result with metadata."""
    merged_retrieval = merge_retrieval_results(state.retrieval_results)
    if isinstance(merged_retrieval, RetrievalResult):
        sources = build_sources(merged_retrieval)
    else:
        if merged_retrieval is not None:
            logger.warning(
                "Expected RetrievalResult for citations, got %s. Skipping citation generation.",
                type(merged_retrieval).__name__,
            )
        sources = []

    # Yield error as final message
    message_chunk = type("MessageChunk", (), {
        "text": error_msg,
    })()
    yield "messages", message_chunk

    yield "metadata", {
        "sources": [
            {
                "document": s.document,
                "page": s.page,
                "document_id": s.document_id,
                "score": s.score,
            }
            for s in sources
        ],
        "tool_calls": state.tool_calls,
    }