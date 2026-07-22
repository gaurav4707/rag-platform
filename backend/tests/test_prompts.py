"""Tests for the prompt builder module."""

from __future__ import annotations

import pytest
from langchain_core.documents import Document

from backend.models.rag_models import RetrievalResult, RetrievedChunk
from backend.rag.prompts import (
    build_system_prompt,
    build_user_question_section,
    build_context_section,
    build_final_instruction,
    build_prompt,
    _remove_duplicate_chunks,
    _truncate_context,
    _format_chunk_metadata,
    _format_chunk_content,
    _format_retrieved_chunk,
)


class TestPromptBuilderHelpers:
    """Tests for internal helper functions."""

    def test_remove_duplicate_chunks(self):
        """Duplicate chunks by exact content are removed."""
        chunk1 = RetrievedChunk(
            document=Document(page_content="Same content", metadata={"document_id": "1", "chunk_index": 0}),
            score=0.1,
        )
        chunk2 = RetrievedChunk(
            document=Document(page_content="Different content", metadata={"document_id": "1", "chunk_index": 1}),
            score=0.2,
        )
        chunk3 = RetrievedChunk(
            document=Document(page_content="Same content", metadata={"document_id": "2", "chunk_index": 0}),
            score=0.15,
        )

        chunks = [chunk1, chunk2, chunk3]
        result = _remove_duplicate_chunks(chunks)

        assert len(result) == 2
        assert result[0].document.page_content == "Same content"
        assert result[1].document.page_content == "Different content"

    def test_remove_duplicate_chunks_preserves_first_occurrence(self):
        """First occurrence (highest rank) is preserved."""
        chunk1 = RetrievedChunk(
            document=Document(page_content="Content A", metadata={}),
            score=0.1,
        )
        chunk2 = RetrievedChunk(
            document=Document(page_content="Content A", metadata={}),
            score=0.2,
        )

        result = _remove_duplicate_chunks([chunk1, chunk2])
        assert len(result) == 1
        assert result[0].score == 0.1  # First one kept

    def test_remove_duplicate_chunks_empty(self):
        """Empty list returns empty list."""
        assert _remove_duplicate_chunks([]) == []

    def test_truncate_context_within_limit(self):
        """Chunks within limit are returned unchanged."""
        chunks = [
            RetrievedChunk(document=Document(page_content="A" * 100, metadata={}), score=0.1),
            RetrievedChunk(document=Document(page_content="B" * 100, metadata={}), score=0.2),
        ]
        result = _truncate_context(chunks, 500)
        assert len(result) == 2

    def test_truncate_context_exceeds_limit(self):
        """Chunks exceeding limit are truncated from the end."""
        chunks = [
            RetrievedChunk(document=Document(page_content="A" * 300, metadata={}), score=0.1),
            RetrievedChunk(document=Document(page_content="B" * 300, metadata={}), score=0.2),
            RetrievedChunk(document=Document(page_content="C" * 300, metadata={}), score=0.3),
        ]
        result = _truncate_context(chunks, 500)
        assert len(result) == 1
        assert result[0].document.page_content == "A" * 300

    def test_truncate_context_never_truncates_individual_chunk(self):
        """Individual chunks are never partially truncated."""
        chunks = [
            RetrievedChunk(document=Document(page_content="A" * 600, metadata={}), score=0.1),
        ]
        result = _truncate_context(chunks, 500)
        # Even though 600 > 500, the chunk is kept because we don't truncate individual chunks
        # Actually, the current implementation would return empty if first chunk exceeds limit
        # Let's verify the behavior: if first chunk > max, we get empty list
        # This is correct per requirements: "Never truncate individual chunks"
        assert len(result) == 0  # First chunk exceeds budget, so none included

    def test_format_chunk_metadata(self):
        """Metadata formatting includes user-friendly fields."""
        chunk = RetrievedChunk(
            document=Document(
                page_content="Test content",
                metadata={
                    "filename": "test.pdf",
                    "page": 5,
                    "chunk_index": 3,
                },
            ),
            score=0.12345,
        )

        result = _format_chunk_metadata(chunk, 1)

        assert "[Source 1]" in result
        assert "Document: test.pdf" in result
        assert "Page: 5" in result
        assert "Chunk: 3" in result
        assert "Relevance Score: 0.1235" in result  # Rounded to 4 decimals

    def test_format_chunk_metadata_missing_fields(self):
        """Missing metadata fields show 'unknown'."""
        chunk = RetrievedChunk(
            document=Document(page_content="Test", metadata={}),
        )

        result = _format_chunk_metadata(chunk, 1)

        assert "Document: unknown" in result
        assert "Page: unknown" in result
        assert "Chunk: unknown" in result
        assert "Relevance Score" not in result  # No score provided

    def test_format_chunk_content(self):
        """Content formatting preserves text."""
        chunk = RetrievedChunk(
            document=Document(page_content="  Hello world  ", metadata={}),
            score=0.1,
        )

        result = _format_chunk_content(chunk)
        assert result == "Content:\nHello world"

    def test_format_retrieved_chunk(self):
        """Full chunk formatting includes metadata and content."""
        chunk = RetrievedChunk(
            document=Document(
                page_content="Test content",
                metadata={"filename": "doc.pdf", "page": 1, "chunk_index": 0},
            ),
            score=0.5,
        )

        result = _format_retrieved_chunk(chunk, 2)

        assert "[Source 2]" in result
        assert "Document: doc.pdf" in result
        assert "Content:\nTest content" in result


class TestPromptBuilderSections:
    """Tests for individual prompt sections."""

    def test_build_system_prompt(self):
        """System prompt contains all required sections."""
        prompt = build_system_prompt()

        assert "SYSTEM INSTRUCTIONS" in prompt
        assert "GROUNDING RULES" in prompt
        assert "CITATION GUIDANCE" in prompt
        assert "BEHAVIOR" in prompt
        assert "I don't know based on the available documents" in prompt
        assert "Do not fabricate" in prompt
        assert "Preserve technical terminology" in prompt

    def test_build_user_question_section(self):
        """User question section formats correctly."""
        prompt = build_user_question_section("What is RAG?")

        assert "USER QUESTION" in prompt
        assert "What is RAG?" in prompt

    def test_build_context_section_empty(self):
        """Empty retrieval result shows appropriate message."""
        retrieval_result = RetrievalResult(
            original_query="test",
            retrieval_query="test",
            chunks=[],
        )

        result = build_context_section(retrieval_result)

        assert "RETRIEVED CONTEXT" in result
        assert "No relevant context retrieved" in result

    def test_build_context_section_with_chunks(self):
        """Context section formats multiple chunks with separators."""
        chunks = [
            RetrievedChunk(
                document=Document(
                    page_content="Content A",
                    metadata={"filename": "a.pdf", "page": 1, "chunk_index": 0},
                ),
                score=0.1,
            ),
            RetrievedChunk(
                document=Document(
                    page_content="Content B",
                    metadata={"filename": "b.pdf", "page": 2, "chunk_index": 1},
                ),
                score=0.2,
            ),
        ]
        retrieval_result = RetrievalResult(
            original_query="test",
            retrieval_query="test",
            chunks=chunks,
        )

        result = build_context_section(retrieval_result)

        assert "RETRIEVED CONTEXT" in result
        assert "[Source 1]" in result
        assert "[Source 2]" in result
        assert "Document: a.pdf" in result
        assert "Document: b.pdf" in result
        assert "Content A" in result
        assert "Content B" in result
        assert "-" * 50 in result  # Separator

    def test_build_context_section_deduplicates(self):
        """Context section removes duplicate chunks."""
        chunks = [
            RetrievedChunk(
                document=Document(page_content="Same", metadata={"filename": "a.pdf"}),
                score=0.1,
            ),
            RetrievedChunk(
                document=Document(page_content="Same", metadata={"filename": "b.pdf"}),
                score=0.2,
            ),
            RetrievedChunk(
                document=Document(page_content="Different", metadata={"filename": "c.pdf"}),
                score=0.3,
            ),
        ]
        retrieval_result = RetrievalResult(
            original_query="test",
            retrieval_query="test",
            chunks=chunks,
        )

        result = build_context_section(retrieval_result)

        # Should only have 2 sources (duplicate removed)
        assert "[Source 1]" in result
        assert "[Source 2]" in result
        assert "[Source 3]" not in result
        assert result.count("Same") == 1  # Only appears once in formatted output

    def test_build_final_instruction(self):
        """Final instruction section is correct."""
        prompt = build_final_instruction()

        assert "ANSWER" in prompt
        assert "Provide your answer based on the retrieved context above" in prompt


class TestBuildPrompt:
    """Tests for the main build_prompt function."""

    def test_build_prompt_structure(self):
        """Complete prompt has all four sections in correct order."""
        chunks = [
            RetrievedChunk(
                document=Document(
                    page_content="Test content",
                    metadata={"filename": "test.pdf", "page": 1, "chunk_index": 0},
                ),
                score=0.1,
            ),
        ]
        retrieval_result = RetrievalResult(
            original_query="What is this?",
            retrieval_query="What is this?",
            chunks=chunks,
        )

        prompt = build_prompt("What is this?", retrieval_result)

        # Check section order
        system_idx = prompt.index("SYSTEM INSTRUCTIONS")
        question_idx = prompt.index("USER QUESTION")
        context_idx = prompt.index("RETRIEVED CONTEXT")
        answer_idx = prompt.index("ANSWER")

        assert system_idx < question_idx < context_idx < answer_idx

    def test_build_prompt_includes_question(self):
        """User question appears in prompt."""
        retrieval_result = RetrievalResult(
            original_query="test",
            retrieval_query="test",
            chunks=[],
        )

        prompt = build_prompt("My specific question", retrieval_result)
        assert "My specific question" in prompt

    def test_build_prompt_includes_context(self):
        """Retrieved context appears in prompt."""
        chunks = [
            RetrievedChunk(
                document=Document(
                    page_content="Important information here",
                    metadata={"filename": "doc.pdf", "page": 5, "chunk_index": 0},
                ),
                score=0.1,
            ),
        ]
        retrieval_result = RetrievalResult(
            original_query="test",
            retrieval_query="test",
            chunks=chunks,
        )

        prompt = build_prompt("Question", retrieval_result)
        assert "Important information here" in prompt
        assert "doc.pdf" in prompt
        assert "Page: 5" in prompt

    def test_build_prompt_empty_retrieval(self):
        """Prompt handles empty retrieval gracefully."""
        retrieval_result = RetrievalResult(
            original_query="test",
            retrieval_query="test",
            chunks=[],
        )

        prompt = build_prompt("Question", retrieval_result)
        assert "No relevant context retrieved" in prompt
        assert "ANSWER" in prompt

    def test_build_prompt_provider_agnostic(self):
        """Prompt contains no provider-specific formatting."""
        retrieval_result = RetrievalResult(
            original_query="test",
            retrieval_query="test",
            chunks=[],
        )

        prompt = build_prompt("Question", retrieval_result)

        # No special tokens, no model-specific formatting
        assert "<|" not in prompt
        assert "[INST]" not in prompt
        assert "<<SYS>>" not in prompt
        assert "llama" not in prompt.lower()
        assert "gpt" not in prompt.lower()


class TestPromptConfig:
    """Tests for prompt configuration."""

    def test_default_config(self):
        """Default config has reasonable values."""
        from backend.rag.prompts import DEFAULT_PROMPT_CONFIG

        assert DEFAULT_PROMPT_CONFIG.max_context_chars == 8000
        assert DEFAULT_PROMPT_CONFIG.max_chunks == 6


class TestContextLengthManagement:
    """Tests for context window management."""

    def test_truncation_preserves_order(self):
        """Truncation keeps highest-ranked chunks."""
        chunks = [
            RetrievedChunk(document=Document(page_content="A" * 1000, metadata={}), score=0.1),
            RetrievedChunk(document=Document(page_content="B" * 1000, metadata={}), score=0.2),
            RetrievedChunk(document=Document(page_content="C" * 1000, metadata={}), score=0.3),
        ]
        retrieval_result = RetrievalResult(
            original_query="test",
            retrieval_query="test",
            chunks=chunks,
        )

        # Max chars = 1500, only first chunk fits
        from backend.rag.prompts import DEFAULT_PROMPT_CONFIG
        original_max = DEFAULT_PROMPT_CONFIG.max_context_chars
        DEFAULT_PROMPT_CONFIG.max_context_chars = 1500

        try:
            prompt = build_prompt("Question", retrieval_result)
            assert "A" * 1000 in prompt
            assert "B" * 1000 not in prompt
        finally:
            DEFAULT_PROMPT_CONFIG.max_context_chars = original_max

    def test_large_chunks_handled(self):
        """Chunks larger than budget are excluded."""
        chunks = [
            RetrievedChunk(document=Document(page_content="X" * 10000, metadata={}), score=0.1),
        ]
        retrieval_result = RetrievalResult(
            original_query="test",
            retrieval_query="test",
            chunks=chunks,
        )

        from backend.rag.prompts import DEFAULT_PROMPT_CONFIG
        original_max = DEFAULT_PROMPT_CONFIG.max_context_chars
        DEFAULT_PROMPT_CONFIG.max_context_chars = 8000

        try:
            prompt = build_prompt("Question", retrieval_result)
            # Chunk exceeds budget, so no context included
            assert "No relevant context retrieved" in prompt
        finally:
            DEFAULT_PROMPT_CONFIG.max_context_chars = original_max