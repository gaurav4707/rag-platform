"""Tool Executor for Agentic RAG system.

Orchestrates multi-tool execution loop with safety limits and structured results.
"""

from __future__ import annotations

import uuid
import time
import logging
from dataclasses import dataclass, field
from typing import Any, AsyncGenerator

from langchain_core.tools import BaseTool
from langchain_core.messages import HumanMessage, AIMessage, ToolMessage

from backend.rag.tool_registry import get_tools
from backend.models.rag_models import RetrievalResult, ChatResult, SourceItem
from backend.rag.prompts import build_prompt, build_system_prompt
from backend.rag.citations import build_sources
from backend.rag.retrieval_utils import merge_retrieval_results
from backend.providers import get_llm
from backend.config import MAX_TOOL_ITERATIONS, MAX_TOOLS_PER_RESPONSE

logger = logging.getLogger(__name__)


@dataclass
class ToolExecutionResult:
    """Structured result of a single tool execution."""
    success: bool
    content: str
    artifact: Any
    duration_ms: float
    error: str | None = None
    tool_name: str = ""
    tool_input: dict | None = None


@dataclass
class ConversationState:
    """Tracks conversation state during a single request."""
    messages: list = field(default_factory=list)
    tool_calls: list[dict] = field(default_factory=list)
    retrieval_results: list[RetrievalResult] = field(default_factory=list)
    tool_execution_results: list[ToolExecutionResult] = field(default_factory=list)

    def add_user_message(self, content: str) -> None:
        self.messages.append(HumanMessage(content=content))

    def add_assistant_message(self, content: str, tool_calls: list | None = None) -> None:
        msg = AIMessage(content=content)
        if tool_calls:
            msg.tool_calls = tool_calls
        self.messages.append(msg)

    def add_tool_message(self, tool_call_id: str, content: Any, artifact: Any = None) -> None:
        # Tool content can be non-string (e.g., list/dict). Ensure we pass a string to ToolMessage.
        content_str = content if isinstance(content, str) else str(content or "")
        self.messages.append(ToolMessage(content=content_str, tool_call_id=tool_call_id))

    def get_messages_for_llm(self) -> list:
        """Return messages formatted for LLM consumption."""
        return self.messages


class ToolExecutor:
    """Executes multi-tool orchestration loop with safety limits."""

    def __init__(
        self,
        max_iterations: int | None = None,
        max_tools_per_response: int | None = None,
    ):
        self.max_iterations = max_iterations or MAX_TOOL_ITERATIONS
        self.max_tools_per_response = max_tools_per_response or MAX_TOOLS_PER_RESPONSE
        self._llm = None
        self._tools = None
        self._tool_map = None

    @property
    def llm(self):
        if self._llm is None:
            self._llm = get_llm()
        return self._llm

    @property
    def tools(self) -> list[BaseTool]:
        if self._tools is None:
            self._tools = get_tools()
        return self._tools

    @property
    def tool_map(self) -> dict[str, Any]:
        if self._tool_map is None:
            self._tool_map = {tool.name: tool for tool in self.tools}
        return self._tool_map

    def execute(
        self,
        question: str,
    ) -> ChatResult:
        """Execute the full orchestration loop and return final ChatResult."""
        logger.debug("Starting tool execution for question: %s", question[:100])

        state = ConversationState()
        state.add_user_message(question)

        iteration = 0
        while iteration < self.max_iterations:
            iteration += 1
            logger.debug("Tool loop iteration %d/%d", iteration, self.max_iterations)

            # Bind tools to LLM for this iteration
            llm_with_tools = self.llm.bind_tools(self.tools)

            # Get LLM response
            response = llm_with_tools.invoke(state.get_messages_for_llm())

            # Check if LLM wants to call tools
            tool_calls = getattr(response, "tool_calls", None)
            if not tool_calls:
                # No tool calls - final answer
                logger.debug("LLM returned final answer (no tool calls)")
                return self._build_final_result(state, str(response.content))

            # Limit tools per response
            if len(tool_calls) > self.max_tools_per_response:
                logger.warning(
                    "LLM requested %d tools, limiting to %d",
                    len(tool_calls),
                    self.max_tools_per_response,
                )
                tool_calls = tool_calls[:self.max_tools_per_response]

            # Execute all tool calls
            for tool_call in tool_calls:
                tool_name = tool_call["name"]
                tool_input = tool_call.get("args", {})
                tool_call_id = tool_call.get("id", "")

                logger.debug("Executing tool: %s with input: %s", tool_name, tool_input)

                execution_result = self._execute_tool(tool_name, tool_input)
                state.tool_execution_results.append(execution_result)

                # Record for final output
                state.tool_calls.append({
                    "tool_name": tool_name,
                    "input": tool_input,
                    "output": execution_result.content,
                })

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
                content=response.content if isinstance(response.content, str) else "",
                tool_calls=tool_calls,
            )

        # Max iterations exceeded
        logger.warning("Max tool iterations (%d) exceeded", self.max_iterations)
        return self._build_error_result(
            state,
            f"Maximum tool iterations ({self.max_iterations}) exceeded. Stopping execution."
        )

    def _execute_tool(self, tool_name: str, tool_input: dict) -> ToolExecutionResult:
        """Execute a single tool and return structured result."""
        start_time = time.perf_counter()

        tool = self.tool_map.get(tool_name)
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

    def _build_final_result(self, state: ConversationState, answer: str) -> ChatResult:
        """Build final ChatResult from conversation state."""
        merged_retrieval = merge_retrieval_results(state.retrieval_results)

        if not answer.strip():
            logger.info("_build_final_result: LLM answer empty, generating via prompt")
            question = state.messages[0].content if state.messages else ""
            if isinstance(merged_retrieval, RetrievalResult):
                prompt = build_prompt(question, merged_retrieval)
            else:
                tool_results = ""
                for tc in state.tool_calls:
                    tool_results += f"Tool: {tc['tool_name']}\nInput: {tc['input']}\nResult: {tc['output']}\n\n"
                prompt = (
                    build_system_prompt()
                    + "\n\nUser Question:\n" + question
                    + ("\n\nTool Results:\n" + tool_results if tool_results else "")
                    + "\n\nAnswer:"
                )
            result = self.llm.invoke(prompt)
            answer = result.content if isinstance(result.content, str) else str(result.content or "")

        if isinstance(merged_retrieval, RetrievalResult):
            sources = build_sources(merged_retrieval)
        else:
            if merged_retrieval is not None:
                logger.warning(
                    "Expected RetrievalResult for citations, got %s. Skipping citation generation.",
                    type(merged_retrieval).__name__,
                )
            sources = []

        logger.debug(
            "Final result: answer_len=%d, sources=%d, tool_calls=%d",
            len(answer),
            len(sources),
            len(state.tool_calls),
        )

        return ChatResult(
            answer=answer,
            sources=sources,
            tool_calls=state.tool_calls,
        )

    def _build_error_result(self, state: ConversationState, error_msg: str) -> ChatResult:
        """Build ChatResult for error cases."""
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

        return ChatResult(
            answer=error_msg,
            sources=sources,
            tool_calls=state.tool_calls,
        )


# Singleton instance for backward compatibility
_default_executor: ToolExecutor | None = None


def get_tool_executor() -> ToolExecutor:
    """Get or create the default ToolExecutor instance."""
    global _default_executor
    if _default_executor is None:
        _default_executor = ToolExecutor()
    return _default_executor


def _reset_executor() -> None:
    """Reset the default executor singleton.

    Exists only for test isolation. Production code should never call this.
    """
    global _default_executor
    _default_executor = None


def execute_agent(question: str) -> ChatResult:
    """Convenience function for single-shot execution."""
    executor = get_tool_executor()
    return executor.execute(question)