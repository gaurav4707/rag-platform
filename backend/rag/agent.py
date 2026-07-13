"""Conversational RAG Agent.

Orchestrates tool execution and generates grounded responses using the Prompt Builder.
"""

import json
import logging
from typing import Any, AsyncGenerator, cast

from backend.models.rag_models import ChatResult, RetrievalResult
from backend.rag.tool_registry import get_tools
from backend.rag.prompts import build_prompt
from backend.rag.citations import build_sources
from backend.rag.llm import get_llm
from backend.rag.retriever import retrieve_context

logger = logging.getLogger(__name__)

_llm = None


def _get_llm():
    """Get or create the LLM instance (singleton)."""
    global _llm
    if _llm is None:
        _llm = get_llm()
    return _llm


def invoke(question: str) -> ChatResult:
    """Process a question and return a complete ChatResult.

    Flow:
    1. Call retrieve_context tool to get RetrievalResult
    2. Build prompt using Prompt Builder
    3. Send prompt to LLM for answer generation
    4. Build citations from RetrievalResult
    5. Return ChatResult with answer, sources, and tool calls
    """
    logger.debug("Processing question: %s", question[:100])

    # Step 1: Retrieve context using the tool
    tool = cast(Any, retrieve_context)
    serialized, retrieval_result = tool.func(question)

    # Step 2: Build prompt using Prompt Builder
    prompt = build_prompt(question, retrieval_result)

    # Step 3: Generate answer using LLM
    llm = _get_llm()
    response = llm.invoke(prompt)
    content = response.content if hasattr(response, "content") else response
    answer = content if isinstance(content, str) else str(content)

    # Step 4: Build citations from RetrievalResult
    sources = build_sources(retrieval_result) if retrieval_result else []

    # Step 5: Build tool calls metadata
    tool_calls = [{
        "tool_name": "retrieve_context",
        "input": {"query": question},
        "output": f"Retrieved {len(retrieval_result.chunks)} chunks" if retrieval_result else "No results",
    }] if retrieval_result else []

    logger.debug("Generated answer length: %d characters", len(answer))

    return ChatResult(
        answer=answer,
        sources=sources,
        tool_calls=tool_calls,
    )


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

    # Step 1: Retrieve context (synchronous tool call)
    tool = cast(Any, retrieve_context)
    serialized, retrieval_result = tool.func(question)

    # Step 2: Yield tool call event
    tool_call_data = type("ToolCall", (), {
        "tool_name": "retrieve_context",
        "input": {"query": question},
        "output": f"Retrieved {len(retrieval_result.chunks)} chunks" if retrieval_result else "No results",
        "artifact": retrieval_result,
    })()
    yield "tool_calls", tool_call_data

    # Step 3: Build prompt
    prompt = build_prompt(question, retrieval_result)

    # Step 4: Stream answer from LLM - yield each token immediately
    llm = _get_llm()
    async for chunk in llm.astream(prompt):
        if chunk.content:
            message_chunk = type("MessageChunk", (), {
                "text": chunk.content,
            })()
            yield "messages", message_chunk

    # Step 5: Yield final metadata event with sources
    sources = build_sources(retrieval_result) if retrieval_result else []
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
        "tool_calls": [{
            "tool_name": "retrieve_context",
            "input": {"query": question},
            "output": f"Retrieved {len(retrieval_result.chunks)} chunks" if retrieval_result else "No results",
        }] if retrieval_result else [],
    }