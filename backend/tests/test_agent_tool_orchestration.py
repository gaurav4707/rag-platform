"""Tests for multi-tool orchestration in the Agent."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from langchain_core.messages import AIMessage, HumanMessage, ToolMessage
from langchain_core.tools import BaseTool

from backend.models.rag_models import ChatResult, RetrievalResult, RetrievedChunk
from backend.rag.agent import invoke, stream_events
from backend.rag.tool_executor import (
    ToolExecutor,
    ConversationState,
    ToolExecutionResult,
    get_tool_executor,
    execute_agent,
)
from backend.rag.retrieval_utils import merge_retrieval_results, deduplicate_chunks
from backend.rag.tools import get_tools
from backend.config import MAX_TOOL_ITERATIONS, MAX_TOOLS_PER_RESPONSE

from langchain_core.documents import Document


# =============================================================================
# Fixtures
# =============================================================================

@pytest.fixture
def clear_llm_cache():
    """Clear the LLM singleton cache and reset executor before and after each test."""
    from backend.rag.tool_executor import _reset_executor
    _reset_executor()
    try:
        from backend.providers.llm import get_llm
        get_llm.cache_clear()
    except ImportError:
        pass
    yield
    _reset_executor()
    try:
        from backend.providers.llm import get_llm
        get_llm.cache_clear()
    except ImportError:
        pass


@pytest.fixture
def mock_retrieval_result():
    """Create a mock RetrievalResult with sample chunks."""
    chunks = [
        RetrievedChunk(
            document=Document(
                page_content="Test content 1",
                metadata={"document_id": "doc1", "filename": "test1.pdf", "page": 1, "chunk_index": 0}
            ),
            score=0.1,
        ),
        RetrievedChunk(
            document=Document(
                page_content="Test content 2",
                metadata={"document_id": "doc2", "filename": "test2.pdf", "page": 2, "chunk_index": 1}
            ),
            score=0.2,
        ),
    ]
    return RetrievalResult(
        original_query="test query",
        retrieval_query="test query",
        chunks=chunks,
        retrieval_metadata={"strategy": "similarity"},
    )


@pytest.fixture
def mock_tool_executor():
    """Create a ToolExecutor with mocked LLM and tools."""
    executor = ToolExecutor(max_iterations=5, max_tools_per_response=3)
    # Mock the LLM property
    executor._llm = MagicMock()
    return executor


# =============================================================================
# ToolExecutor Tests
# =============================================================================

class TestToolExecutor:
    """Tests for the ToolExecutor class."""

    def test_executor_initialization(self, mock_tool_executor):
        """Test executor initializes with correct defaults."""
        assert mock_tool_executor.max_iterations == 5
        assert mock_tool_executor.max_tools_per_response == 3
        assert mock_tool_executor.tools is not None
        assert len(mock_tool_executor.tools) == 3
        assert "retrieve_context" in mock_tool_executor.tool_map
        assert "list_documents" in mock_tool_executor.tool_map
        assert "search_by_filename" in mock_tool_executor.tool_map

    def test_get_tool_executor_singleton(self):
        """Test singleton pattern for tool executor."""
        executor1 = get_tool_executor()
        executor2 = get_tool_executor()
        assert executor1 is executor2

    def test_execute_no_tools_needed(self, mock_tool_executor, mock_retrieval_result):
        """Test execution when LLM doesn't call any tools."""
        mock_llm = MagicMock()
        mock_response = AIMessage(content="This is a general knowledge answer.")
        mock_response.tool_calls = []
        mock_llm.bind_tools.return_value.invoke.return_value = mock_response
        mock_tool_executor._llm = mock_llm

        result = mock_tool_executor.execute("What is 2+2?")

        assert isinstance(result, ChatResult)
        assert result.answer == "This is a general knowledge answer."
        assert result.tool_calls == []
        mock_llm.bind_tools.assert_called_once()

    def test_execute_single_tool_call(self, mock_tool_executor, mock_retrieval_result):
        """Test execution with single tool call."""
        mock_llm = MagicMock()

        # First call: LLM requests tool
        mock_response1 = AIMessage(content="", tool_calls=[
            {"name": "list_documents", "args": {}, "id": "call_1"}
        ])
        # Second call: LLM returns final answer
        mock_response2 = AIMessage(content="Here are your documents.")

        mock_llm.bind_tools.return_value.invoke.side_effect = [mock_response1, mock_response2]
        mock_tool_executor._llm = mock_llm

        # Mock the list_documents tool
        with patch("backend.rag.tools.list_documents.list_indexed_documents") as mock_list:
            mock_list.return_value = [
                {"document_id": "doc1", "filename": "test.pdf", "status": "indexed"}
            ]

            result = mock_tool_executor.execute("List my documents")

            assert isinstance(result, ChatResult)
            assert "documents" in result.answer.lower() or "test.pdf" in result.answer.lower()
            assert len(result.tool_calls) == 1
            assert result.tool_calls[0]["tool_name"] == "list_documents"

    def test_execute_two_tool_sequence(self, mock_tool_executor, mock_retrieval_result):
        """Test execution with two sequential tool calls (search_by_filename -> retrieve_context)."""
        mock_llm = MagicMock()

        # First call: LLM requests search_by_filename
        mock_response1 = AIMessage(content="", tool_calls=[
            {"name": "search_by_filename", "args": {"filename": "architecture"}, "id": "call_1"}
        ])
        # Second call: LLM requests retrieve_context
        mock_response2 = AIMessage(content="", tool_calls=[
            {"name": "retrieve_context", "args": {"query": "architecture overview"}, "id": "call_2"}
        ])
        # Third call: LLM returns final answer
        mock_response3 = AIMessage(content="Summary of architecture document...")

        mock_llm.bind_tools.return_value.invoke.side_effect = [
            mock_response1, mock_response2, mock_response3
        ]
        mock_tool_executor._llm = mock_llm

        # Mock search_by_filename tool
        with patch("backend.rag.tools.search_by_filename.search_documents_by_filename") as mock_search:
            mock_search.return_value = [
                {"document_id": "doc1", "filename": "architecture.pdf", "file_hash": "hash1", "status": "indexed"}
            ]
            # Mock retrieve_context tool
            with patch("backend.rag.retriever.retrieve_context") as mock_retrieve:
                mock_retrieve.func.return_value = ("serialized", mock_retrieval_result)

                result = mock_tool_executor.execute("Summarize architecture.pdf")

                assert isinstance(result, ChatResult)
                assert len(result.tool_calls) == 2
                assert result.tool_calls[0]["tool_name"] == "search_by_filename"
                assert result.tool_calls[1]["tool_name"] == "retrieve_context"

    def test_execute_max_iterations_exceeded(self):
        """Test that execution stops after max iterations."""
        executor = ToolExecutor(max_iterations=2, max_tools_per_response=1)
        mock_llm = MagicMock()

        # LLM keeps requesting tools indefinitely
        mock_response = AIMessage(content="", tool_calls=[
            {"name": "list_documents", "args": {}, "id": "call_1"}
        ])

        mock_llm.bind_tools.return_value.invoke.return_value = mock_response
        executor._llm = mock_llm

        with patch("backend.rag.tools.list_documents.list_indexed_documents") as mock_list:
            mock_list.return_value = []

            result = executor.execute("Keep listing documents")

            assert "Maximum tool iterations (2) exceeded" in result.answer
            assert len(result.tool_calls) == 2

    def test_execute_max_tools_per_response_limit(self):
        """Test that tools per response are limited."""
        executor = ToolExecutor(max_iterations=5, max_tools_per_response=3)
        mock_llm = MagicMock()

        # LLM requests 10 tools in one response
        mock_response1 = AIMessage(content="", tool_calls=[
            {"name": "list_documents", "args": {}, "id": f"call_{i}"}
            for i in range(10)
        ])
        mock_response2 = AIMessage(content="Done.")

        mock_llm.bind_tools.return_value.invoke.side_effect = [mock_response1, mock_response2]
        executor._llm = mock_llm

        with patch("backend.rag.tools.list_documents.list_indexed_documents") as mock_list:
            mock_list.return_value = []

            result = executor.execute("List documents many times")

            # Should only execute 3 tools (max_tools_per_response)
            assert len(result.tool_calls) == 3

    def test_execute_unknown_tool_handled_gracefully(self, mock_tool_executor):
        """Test that unknown tool returns error to LLM instead of crashing."""
        mock_llm = MagicMock()

        mock_response1 = AIMessage(content="", tool_calls=[
            {"name": "magic_tool", "args": {}, "id": "call_1"}
        ])
        mock_response2 = AIMessage(content="That tool doesn't exist.")

        mock_llm.bind_tools.return_value.invoke.side_effect = [mock_response1, mock_response2]
        mock_tool_executor._llm = mock_llm

        result = mock_tool_executor.execute("Use magic tool")

        assert "Unknown tool" in result.tool_calls[0]["output"]
        assert result.tool_calls[0]["tool_name"] == "magic_tool"

    def test_execute_tool_exception_handled(self, mock_tool_executor):
        """Test that tool exceptions are caught and returned to LLM."""
        mock_llm = MagicMock()

        mock_response1 = AIMessage(content="", tool_calls=[
            {"name": "retrieve_context", "args": {"query": "test"}, "id": "call_1"}
        ])
        mock_response2 = AIMessage(content="The tool failed but I'll continue.")

        mock_llm.bind_tools.return_value.invoke.side_effect = [mock_response1, mock_response2]
        mock_tool_executor._llm = mock_llm

        # Patch the tool's func directly since it's bound at import time
        retrieve_tool = mock_tool_executor.tool_map["retrieve_context"]
        original_func = retrieve_tool.func
        retrieve_tool.func = MagicMock(side_effect=Exception("Vector store down"))

        try:
            result = mock_tool_executor.execute("Search for something")

            assert "Error executing tool" in result.tool_calls[0]["output"]
            assert result.tool_calls[0]["tool_name"] == "retrieve_context"
        finally:
            retrieve_tool.func = original_func


# =============================================================================
# ConversationState Tests
# =============================================================================

class TestConversationState:
    """Tests for ConversationState tracking."""

    def test_add_user_message(self):
        """Test adding user message."""
        state = ConversationState()
        state.add_user_message("Hello")

        assert len(state.messages) == 1
        assert isinstance(state.messages[0], HumanMessage)
        assert state.messages[0].content == "Hello"

    def test_add_assistant_message_with_tool_calls(self):
        """Test adding assistant message with tool calls."""
        state = ConversationState()
        tool_calls = [{"name": "tool1", "args": {}, "id": "call_1"}]
        state.add_assistant_message("I'll help", tool_calls)

        assert len(state.messages) == 1
        assert isinstance(state.messages[0], AIMessage)
        assert state.messages[0].content == "I'll help"
        assert state.messages[0].tool_calls == tool_calls

    def test_add_tool_message(self):
        """Test adding tool message."""
        state = ConversationState()
        state.add_tool_message("call_1", "Tool result", artifact={"data": "test"})

        assert len(state.messages) == 1
        assert isinstance(state.messages[0], ToolMessage)
        assert state.messages[0].content == "Tool result"
        assert state.messages[0].tool_call_id == "call_1"

    def test_get_messages_for_llm(self):
        """Test getting messages formatted for LLM."""
        state = ConversationState()
        state.add_user_message("Question")
        state.add_assistant_message("", [{"name": "tool1", "args": {}, "id": "call_1"}])
        state.add_tool_message("call_1", "Result")

        messages = state.get_messages_for_llm()
        assert len(messages) == 3
        assert isinstance(messages[0], HumanMessage)
        assert isinstance(messages[1], AIMessage)
        assert isinstance(messages[2], ToolMessage)


# =============================================================================
# Retrieval Utilities Tests
# =============================================================================

class TestRetrievalUtils:
    """Tests for retrieval result merging and deduplication."""

    def test_merge_retrieval_results_single(self, mock_retrieval_result):
        """Test merging single result returns it unchanged."""
        result = merge_retrieval_results([mock_retrieval_result])
        assert result is mock_retrieval_result

    def test_merge_retrieval_results_empty(self):
        """Test merging empty list returns None."""
        result = merge_retrieval_results([])
        assert result is None

    def test_merge_retrieval_results_deduplicates(self):
        """Test merging deduplicates by (document_id, chunk_index)."""
        chunk1 = RetrievedChunk(
            document=Document(
                page_content="Content A",
                metadata={"document_id": "doc1", "chunk_index": 0, "filename": "a.pdf"}
            ),
            score=0.1,
        )
        chunk2 = RetrievedChunk(
            document=Document(
                page_content="Content B",
                metadata={"document_id": "doc1", "chunk_index": 1, "filename": "a.pdf"}
            ),
            score=0.2,
        )
        chunk3 = RetrievedChunk(
            document=Document(
                page_content="Content A duplicate",
                metadata={"document_id": "doc1", "chunk_index": 0, "filename": "a.pdf"}  # Same ID
            ),
            score=0.15,
        )

        result1 = RetrievalResult(
            original_query="q1", retrieval_query="q1", chunks=[chunk1, chunk2],
            retrieval_metadata={"strategy": "similarity"}
        )
        result2 = RetrievalResult(
            original_query="q2", retrieval_query="q2", chunks=[chunk3],
            retrieval_metadata={"strategy": "mmr"}
        )

        merged = merge_retrieval_results([result1, result2])

        assert merged is not None
        assert len(merged.chunks) == 2  # chunk3 deduplicated
        assert merged.chunks[0].document.page_content == "Content A"
        assert merged.chunks[1].document.page_content == "Content B"
        assert merged.original_query == "q1"  # Preserves first query

    def test_deduplicate_chunks_by_document_id_and_chunk_index(self):
        """Test chunk deduplication preserves first occurrence."""
        chunks = [
            RetrievedChunk(
                document=Document(page_content="A", metadata={"document_id": "1", "chunk_index": 0}),
                score=0.1,
            ),
            RetrievedChunk(
                document=Document(page_content="B", metadata={"document_id": "1", "chunk_index": 1}),
                score=0.2,
            ),
            RetrievedChunk(
                document=Document(page_content="A dup", metadata={"document_id": "1", "chunk_index": 0}),
                score=0.3,
            ),
        ]

        unique = deduplicate_chunks(chunks)

        assert len(unique) == 2
        assert unique[0].document.page_content == "A"
        assert unique[1].document.page_content == "B"

    def test_deduplicate_chunks_no_metadata(self):
        """Test deduplication when chunks have no metadata uses fallback keys."""
        chunks = [
            RetrievedChunk(
                document=Document(page_content="Same content", metadata={}),
                score=0.1,
            ),
            RetrievedChunk(
                document=Document(page_content="Different content", metadata={}),
                score=0.2,
            ),
            RetrievedChunk(
                document=Document(page_content="Same content", metadata={}),
                score=0.3,
            ),
        ]

        unique = deduplicate_chunks(chunks)

        # When metadata is empty, both get doc_id="unknown" and chunk_idx=-1
        # So they are treated as the same chunk and deduplicated
        assert len(unique) == 1
        assert unique[0].document.page_content == "Same content"


# =============================================================================
# Tool Registry Tests
# =============================================================================

class TestToolRegistry:
    """Tests for dynamic tool registry."""

    def test_get_tools_returns_all_three(self):
        """Test registry returns all three tools."""
        tools = get_tools()
        assert len(tools) == 3
        names = {t.name for t in tools}
        assert names == {"retrieve_context", "list_documents", "search_by_filename"}

    def test_new_tool_auto_registered(self):
        """Test that adding a tool to tools/__init__.py makes it available."""
        tools = get_tools()
        for tool in tools:
            assert isinstance(tool, BaseTool)
            assert hasattr(tool, "name")
            assert hasattr(tool, "description")

    def test_tool_descriptions_present(self):
        """Test that all tools have descriptions for the system prompt."""
        tools = get_tools()
        for tool in tools:
            assert tool.description
            assert len(tool.description.strip()) > 0


# =============================================================================
# System Prompt Tests
# =============================================================================

class TestSystemPrompt:
    """Tests for system prompt with tool descriptions."""

    def test_build_system_prompt_includes_tools(self):
        """Test that system prompt includes tool descriptions."""
        from backend.rag.prompts import build_system_prompt, build_tool_descriptions

        prompt = build_system_prompt()
        tool_desc = build_tool_descriptions()

        assert "AVAILABLE TOOLS:" in prompt
        assert "retrieve_context" in prompt
        assert "list_documents" in prompt
        assert "search_by_filename" in prompt

        # Tool descriptions should not encode workflows
        assert "search_by_filename" in tool_desc
        assert "retrieve_context" in tool_desc
        # Should NOT mention chaining
        assert "search_by_filename" in tool_desc
        assert "then" not in tool_desc.lower() or "search_by_filename" not in tool_desc.lower()


# =============================================================================
# Streaming Tests (mocked LLM)
# =============================================================================

class TestStreaming:
    """Tests for streaming with multi-tool orchestration."""

    @pytest.fixture(autouse=True)
    def mock_llm(self):
        """Mock the LLM for streaming tests."""
        # The agent.py imports get_llm from backend.providers
        # We need to patch it where it's used in agent.py and tool_executor.py
        with patch("backend.rag.agent.get_llm") as mock_get_llm_agent, \
             patch("backend.rag.tool_executor.get_llm") as mock_get_llm_executor:
            mock_llm = MagicMock()  # Use MagicMock, not AsyncMock, to avoid coroutines
            mock_get_llm_agent.return_value = mock_llm
            mock_get_llm_executor.return_value = mock_llm
            
            # Configure astream as async generator
            async def mock_astream(prompt):
                class Chunk:
                    def __init__(self, content):
                        self.content = content
                yield Chunk("Documents ")
                yield Chunk("listed.")
            
            mock_llm.astream = mock_astream
            yield mock_llm

    @pytest.mark.asyncio
    async def test_stream_events_yields_tool_calls(self, mock_retrieval_result, mock_llm):
        """Test streaming yields tool_calls events."""
        # First call: LLM requests tool
        mock_response1 = AIMessage(content="", tool_calls=[
            {"name": "list_documents", "args": {}, "id": "call_1"}
        ])
        # Second call: LLM returns final answer
        mock_response2 = AIMessage(content="Documents listed.")

        mock_llm.bind_tools.return_value.invoke.side_effect = [mock_response1, mock_response2]

        with patch("backend.rag.tools.list_documents.list_indexed_documents") as mock_list:
            mock_list.return_value = [
                {"document_id": "doc1", "filename": "test.pdf", "status": "indexed"}
            ]

            events = []
            async for kind, data in stream_events("List my documents"):
                events.append((kind, data))

            # Should have tool_calls event
            tool_events = [e for e in events if e[0] == "tool_calls"]
            assert len(tool_events) == 1
            assert tool_events[0][1].tool_name == "list_documents"

            # Should have message events
            msg_events = [e for e in events if e[0] == "messages"]
            assert len(msg_events) > 0

            # Should have metadata event
            meta_events = [e for e in events if e[0] == "metadata"]
            assert len(meta_events) == 1

    @pytest.mark.asyncio
    async def test_stream_events_no_tools_needed(self, mock_llm):
        """Test streaming when no tools are needed."""
        mock_response = AIMessage(content="General knowledge answer.")
        mock_response.tool_calls = []

        mock_llm.bind_tools.return_value.invoke.return_value = mock_response

        events = []
        async for kind, data in stream_events("What is 2+2?"):
            events.append((kind, data))

        # Should not have tool_calls
        tool_events = [e for e in events if e[0] == "tool_calls"]
        assert len(tool_events) == 0

        # Should have messages
        msg_events = [e for e in events if e[0] == "messages"]
        assert len(msg_events) > 0


# =============================================================================
# Invoke Tests (mocked LLM)
# =============================================================================

class TestInvoke:
    """Tests for non-streaming invoke."""

    @pytest.fixture(autouse=True)
    def mock_llm(self, clear_llm_cache):
        """Mock the LLM for invoke tests."""
        with patch("backend.rag.agent.get_llm") as mock_get_llm_agent, \
             patch("backend.rag.tool_executor.get_llm") as mock_get_llm_executor:
            mock_llm = MagicMock()
            mock_get_llm_agent.return_value = mock_llm
            mock_get_llm_executor.return_value = mock_llm
            yield mock_llm

    def test_invoke_general_question(self, mock_llm):
        """Test invoke with general knowledge question (no tools)."""
        mock_response = AIMessage(content="2+2=4")
        mock_response.tool_calls = []
        mock_llm.bind_tools.return_value.invoke.return_value = mock_response

        result = invoke("What is 2+2?")

        assert isinstance(result, ChatResult)
        assert "4" in result.answer
        assert result.tool_calls == []

    def test_invoke_with_tool(self, mock_retrieval_result, mock_llm):
        """Test invoke with tool usage."""
        mock_response1 = AIMessage(content="", tool_calls=[
            {"name": "list_documents", "args": {}, "id": "call_1"}
        ])
        mock_response2 = AIMessage(content="You have 1 document.")

        mock_llm.bind_tools.return_value.invoke.side_effect = [mock_response1, mock_response2]

        with patch("backend.rag.tools.list_documents.list_indexed_documents") as mock_list:
            mock_list.return_value = [
                {"document_id": "doc1", "filename": "test.pdf", "status": "indexed"}
            ]

            result = invoke("List my documents")

            assert isinstance(result, ChatResult)
            assert len(result.tool_calls) == 1


# =============================================================================
# Ambiguous Match Handling
# =============================================================================

class TestAmbiguousMatch:
    """Tests for handling ambiguous document matches."""

    @pytest.fixture(autouse=True)
    def mock_llm(self, clear_llm_cache):
        """Mock the LLM for ambiguous match tests."""
        with patch("backend.rag.tool_executor.get_llm") as mock_get_llm:
            mock_llm = MagicMock()
            mock_get_llm.return_value = mock_llm
            yield mock_llm

    def test_ambiguous_search_allows_clarification(self, mock_retrieval_result, mock_llm):
        """Test that ambiguous results let LLM ask for clarification."""
        # First call: LLM searches by filename
        mock_response1 = AIMessage(content="", tool_calls=[
            {"name": "search_by_filename", "args": {"filename": "architecture"}, "id": "call_1"}
        ])
        # Second call: LLM sees multiple matches and asks for clarification
        mock_response2 = AIMessage(content="I found multiple documents matching 'architecture': system_architecture.pdf and ARCHITECTURE_decisions.md. Which one would you like me to summarize?")
        mock_response2.tool_calls = []

        mock_llm.bind_tools.return_value.invoke.side_effect = [mock_response1, mock_response2]

        with patch("backend.rag.tools.search_by_filename.search_documents_by_filename") as mock_search:
            mock_search.return_value = [
                {"document_id": "doc1", "filename": "system_architecture.pdf", "file_hash": "h1", "status": "indexed"},
                {"document_id": "doc2", "filename": "ARCHITECTURE_decisions.md", "file_hash": "h2", "status": "indexed"},
            ]

            result = invoke("Summarize architecture")

            # Should NOT automatically pick one - should ask clarification
            assert "multiple" in result.answer.lower() or "which" in result.answer.lower()


# =============================================================================
# Integration Tests (require API key)
# =============================================================================

class TestIntegration:
    """Integration tests (marked as slow, require API key)."""

    @pytest.mark.skip(reason="Requires API key and network")
    def test_full_integration_single_tool(self):
        """Full integration test with real LLM."""
        result = invoke("List all uploaded documents")
        assert isinstance(result, ChatResult)

    @pytest.mark.skip(reason="Requires API key and network")
    def test_full_integration_two_tools(self):
        """Full integration test with two tools."""
        result = invoke("What documents do I have about API design?")
        assert isinstance(result, ChatResult)
        assert len(result.tool_calls) >= 1