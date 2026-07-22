"""Tests for context compression module."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest
from langchain_core.documents import Document

from backend.models.rag_models import RetrievedChunk
from backend.rag.context_compression import (
    BaseContextCompressor,
    EmbeddingScorer,
    ExtractiveContextCompressor,
    KeywordScorer,
    LLMContextCompressor,
    NoOpContextCompressor,
    get_context_compressor,
    get_relevance_scorer,
)
from backend.rag.retrieval_config import RetrievalConfig
from backend.rag.retrieval_pipeline import (
    ContextCompressionStage,
    PipelineContext,
    StageResult,
)


def _make_chunk(text: str, doc_id: str = "1", chunk_index: int = 0, score: float = 0.5, page: int = 1, filename: str = "test.pdf") -> RetrievedChunk:
    return RetrievedChunk(
        document=Document(
            page_content=text,
            metadata={
                "document_id": doc_id,
                "chunk_index": chunk_index,
                "filename": filename,
                "page": page,
                "source": "pdf",
            },
        ),
        score=score,
    )


class TestNoOpContextCompressor:
    def test_returns_chunks_unchanged(self):
        chunks = [_make_chunk("hello world")]
        compressor = NoOpContextCompressor()
        result = compressor.compress("query", chunks)
        assert result is chunks
        assert result[0].document.page_content == "hello world"

    def test_preserves_multiple_chunks(self):
        chunks = [_make_chunk("a", doc_id="1"), _make_chunk("b", doc_id="2")]
        compressor = NoOpContextCompressor()
        result = compressor.compress("query", chunks)
        assert len(result) == 2
        assert result is chunks


class TestKeywordScorer:
    def test_exact_match(self):
        scorer = KeywordScorer()
        score = scorer.score("capital of France", "France is a country in Europe")
        assert score > 0

    def test_no_match(self):
        scorer = KeywordScorer()
        score = scorer.score("python programming", "The capital of France is Paris")
        assert score == 0.0

    def test_partial_match(self):
        scorer = KeywordScorer()
        score = scorer.score("capital of France", "The capital of Germany is Berlin")
        # "capital" and "of" match, "France" doesn't
        assert 0 < score < 1.0

    def test_empty_query(self):
        scorer = KeywordScorer()
        score = scorer.score("", "some text")
        assert score == 0.0

    def test_case_insensitive(self):
        scorer = KeywordScorer()
        score = scorer.score("FRANCE", "france is a country")
        assert score > 0


class TestEmbeddingScorer:
    def test_uses_embedding_provider(self):
        mock_emb = MagicMock()
        mock_emb.embed_query.side_effect = lambda x: [1.0, 0.0, 0.0, 0.0] if "query" in x else [0.5, 0.5, 0.0, 0.0]

        scorer = EmbeddingScorer()
        scorer._embeddings = mock_emb
        score = scorer.score("test query", "some text")
        assert isinstance(score, float)
        assert 0 <= score <= 1.0

    def test_identical_vectors(self):
        mock_emb = MagicMock()
        mock_emb.embed_query.return_value = [1.0, 0.0, 0.0]
        scorer = EmbeddingScorer()
        scorer._embeddings = mock_emb
        score = scorer.score("same", "same")
        assert score == 1.0

    def test_orthogonal_vectors(self):
        mock_emb = MagicMock()
        mock_emb.embed_query.side_effect = lambda x: [1.0, 0.0] if x == "a" else [0.0, 1.0]
        scorer = EmbeddingScorer()
        scorer._embeddings = mock_emb
        score = scorer.score("a", "b")
        assert score == 0.0


class TestExtractiveContextCompressor:
    def test_single_sentence_unchanged(self):
        scorer = MagicMock()
        compressor = ExtractiveContextCompressor(scorer=scorer)
        chunks = [_make_chunk("Single sentence chunk.")]
        result = compressor.compress("query", chunks)
        assert result[0].document.page_content == "Single sentence chunk."
        scorer.score.assert_not_called()

    def test_extracts_relevant_sentences(self):
        scorer = MagicMock()
        # Return high score only for the first sentence
        scorer.score.side_effect = lambda q, s: 0.9 if "Paris" in s else 0.1

        compressor = ExtractiveContextCompressor(scorer=scorer)
        text = "Paris is the capital of France. The weather is nice today. The Eiffel Tower is in Paris."
        chunks = [_make_chunk(text)]
        result = compressor.compress("Paris", chunks, target_ratio=0.5)
        # Should keep ~2 sentences (50% of 3 = 1.5 -> 2 with max(1, int))
        # The two highest-scored: "Paris is..." and "The Eiffel..."
        assert "Paris" in result[0].document.page_content
        assert "weather" not in result[0].document.page_content

    def test_preserves_original_sentence_order(self):
        scorer = MagicMock()
        scorer.score.side_effect = lambda q, s: 0.5

        compressor = ExtractiveContextCompressor(scorer=scorer)
        text = "First sentence. Second sentence. Third sentence."
        chunks = [_make_chunk(text)]
        result = compressor.compress("q", chunks, target_ratio=1.0)
        # All sentences kept, order preserved
        assert result[0].document.page_content == text

    def test_provenance_preserved(self):
        scorer = MagicMock()
        scorer.score.return_value = 0.5
        compressor = ExtractiveContextCompressor(scorer=scorer)
        chunks = [_make_chunk("First. Second. Third.", doc_id="doc1", chunk_index=2, page=3, filename="report.pdf")]
        result = compressor.compress("query", chunks)
        meta = result[0].document.metadata
        assert meta["document_id"] == "doc1"
        assert meta["chunk_index"] == 2
        assert meta["page"] == 3
        assert meta["filename"] == "report.pdf"

    def test_score_preserved(self):
        scorer = MagicMock()
        scorer.score.return_value = 0.5
        compressor = ExtractiveContextCompressor(scorer=scorer)
        chunks = [_make_chunk("First. Second.", score=0.85)]
        result = compressor.compress("query", chunks)
        assert result[0].score == 0.85


class TestLLMContextCompressor:
    def test_uses_llm_for_compression(self):
        mock_llm = MagicMock()
        mock_llm.invoke.return_value.content = "compressed text"
        compressor = LLMContextCompressor(llm=mock_llm)
        compressor._initialized = True
        chunks = [_make_chunk("Long text to compress with irrelevant details.")]
        result = compressor.compress("query", chunks)
        assert result[0].document.page_content == "compressed text"

    def test_fallback_on_llm_failure(self):
        mock_llm = MagicMock()
        mock_llm.invoke.side_effect = Exception("LLM error")
        compressor = LLMContextCompressor(llm=mock_llm)
        compressor._initialized = True
        original = "Original text to keep on failure."
        chunks = [_make_chunk(original)]
        result = compressor.compress("query", chunks)
        assert result[0].document.page_content == original

    def test_lazy_initialization(self):
        compressor = LLMContextCompressor()
        assert compressor._initialized is False
        assert compressor._llm is None

    def test_metadata_preserved(self):
        mock_llm = MagicMock()
        mock_llm.invoke.return_value.content = "compressed"
        compressor = LLMContextCompressor(llm=mock_llm)
        compressor._initialized = True
        chunks = [_make_chunk("Some text.", doc_id="d1", chunk_index=5, page=2)]
        result = compressor.compress("query", chunks)
        meta = result[0].document.metadata
        assert meta["document_id"] == "d1"
        assert meta["chunk_index"] == 5
        assert meta["page"] == 2

    def test_score_preserved(self):
        mock_llm = MagicMock()
        mock_llm.invoke.return_value.content = "compressed"
        compressor = LLMContextCompressor(llm=mock_llm)
        compressor._initialized = True
        chunks = [_make_chunk("Some text.", score=0.92)]
        result = compressor.compress("query", chunks)
        assert result[0].score == 0.92


class TestGetRelevanceScorer:
    def test_keyword_scorer(self):
        scorer = get_relevance_scorer("keyword")
        assert isinstance(scorer, KeywordScorer)

    def test_embedding_scorer(self):
        scorer = get_relevance_scorer("embedding")
        assert isinstance(scorer, EmbeddingScorer)

    def test_unknown_fallback(self):
        scorer = get_relevance_scorer("unknown")
        assert isinstance(scorer, KeywordScorer)


class TestGetContextCompressor:
    def test_noop(self):
        c = get_context_compressor("none")
        assert isinstance(c, NoOpContextCompressor)

    def test_extractive(self):
        c = get_context_compressor("extractive")
        assert isinstance(c, ExtractiveContextCompressor)

    def test_llm(self):
        c = get_context_compressor("llm")
        assert isinstance(c, LLMContextCompressor)

    def test_unknown_fallback(self):
        c = get_context_compressor("unknown")
        assert isinstance(c, NoOpContextCompressor)


class TestContextCompressionStage:
    def test_skipped_when_disabled(self):
        compressor = MagicMock()
        stage = ContextCompressionStage(compressor)
        config = RetrievalConfig(compression_strategy="none")
        ctx = PipelineContext(original_query="test", config=config)
        ctx.working_chunks = [_make_chunk("test")]
        result = stage.execute(ctx)
        assert result.trace.get("skipped") is True
        compressor.compress.assert_not_called()

    def test_compresses_when_enabled(self):
        compressor = MagicMock()
        compressor.compress.side_effect = lambda q, c, **kw: c
        stage = ContextCompressionStage(compressor)
        config = RetrievalConfig(compression_strategy="extractive")
        ctx = PipelineContext(original_query="test", config=config)
        chunks = [_make_chunk("some content")]
        ctx.working_chunks = chunks
        result = stage.execute(ctx)
        compressor.compress.assert_called_once()
        assert result.trace["stage"] == "context_compression"

    def test_trace_metrics(self):
        compressor = MagicMock()
        compressor.compress.side_effect = lambda q, c, **kw: [
            _make_chunk("compressed") for _ in c
        ]
        stage = ContextCompressionStage(compressor)
        config = RetrievalConfig(compression_strategy="extractive")
        ctx = PipelineContext(original_query="test", config=config)
        ctx.working_chunks = [_make_chunk("original content here")]
        result = stage.execute(ctx)
        assert "original_tokens" in result.trace
        assert "compressed_tokens" in result.trace
        assert "compression_ratio" in result.trace
        assert "latency_ms" in result.trace
        assert "tokens_saved" in result.trace
        assert "characters_saved" in result.trace

    def test_failure_falls_back(self):
        compressor = MagicMock()
        compressor.compress.side_effect = Exception("compression failed")
        stage = ContextCompressionStage(compressor)
        config = RetrievalConfig(compression_strategy="extractive")
        ctx = PipelineContext(original_query="test", config=config)
        original = [_make_chunk("original content")]
        ctx.working_chunks = original
        result = stage.execute(ctx)
        assert result.chunks == original
        assert result.trace.get("fallback") is True

    def test_empty_chunks_skipped(self):
        compressor = MagicMock()
        stage = ContextCompressionStage(compressor)
        config = RetrievalConfig(compression_strategy="extractive")
        ctx = PipelineContext(original_query="test", config=config)
        ctx.working_chunks = []
        result = stage.execute(ctx)
        assert result.trace.get("skipped") is True
        compressor.compress.assert_not_called()

    def test_returns_stage_result(self):
        compressor = MagicMock()
        compressor.compress.return_value = [_make_chunk("compressed")]
        stage = ContextCompressionStage(compressor)
        config = RetrievalConfig(compression_strategy="extractive")
        ctx = PipelineContext(original_query="test", config=config)
        ctx.working_chunks = [_make_chunk("original")]
        result = stage.execute(ctx)
        assert isinstance(result, StageResult)
        assert isinstance(result.chunks, list)
        assert isinstance(result.trace, dict)


class TestCompressionPipelineIntegration:
    def test_compression_stage_in_pipeline(self):
        """Verify compression stage runs in pipeline and produces StageResult."""
        from backend.rag.retrieval_pipeline import RetrievalPipeline

        pipeline = RetrievalPipeline()
        config = RetrievalConfig(
            compression_strategy="none",
            reranker="none",
        )
        serialized, result = pipeline.execute("test query", config)
        assert isinstance(serialized, str)
        assert isinstance(result.chunks, list)

    def test_compression_preserves_chunk_metadata(self):
        """Verify compressed chunks retain provenance through the pipeline."""
        from backend.rag.retrieval_pipeline import RetrievalPipeline

        pipeline = RetrievalPipeline()
        config = RetrievalConfig(
            compression_strategy="none",
            reranker="none",
        )
        serialized, result = pipeline.execute("test query", config)
        for chunk in result.chunks:
            assert "document_id" in chunk.document.metadata
            assert "filename" in chunk.document.metadata

    def test_config_in_retrieval_metadata(self):
        """Verify compression config appears in pipeline metadata."""
        from backend.rag.retrieval_pipeline import RetrievalPipeline

        pipeline = RetrievalPipeline()
        config = RetrievalConfig(
            compression_strategy="extractive",
            compression_scoring="keyword",
            compression_target_ratio=0.5,
            reranker="none",
        )
        serialized, result = pipeline.execute("test", config)
        assert result.retrieval_metadata["config"]["compression_strategy"] == "extractive"
        assert result.retrieval_metadata["config"]["compression_scoring"] == "keyword"

    def test_compression_disabled_default(self):
        """Verify compression is disabled by default (no behavior change)."""
        from backend.rag.retrieval_pipeline import RetrievalPipeline
        from backend.rag.retrieval_config import DEFAULT_RETRIEVAL_CONFIG

        assert DEFAULT_RETRIEVAL_CONFIG.compression_strategy == "none"

        pipeline = RetrievalPipeline()
        config = DEFAULT_RETRIEVAL_CONFIG
        serialized, result = pipeline.execute("test", config)
        assert result.retrieval_metadata["config"]["compression_strategy"] == "none"
