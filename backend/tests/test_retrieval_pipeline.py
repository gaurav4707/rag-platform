"""Tests for the retrieval pipeline module."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest
from langchain_core.documents import Document

from backend.models.rag_models import RetrievalResult, RetrievedChunk
from backend.rag.retrieval_config import RetrievalConfig, QueryProcessingConfig
from backend.rag.query_expander import QueryExpansionResult
from backend.rag.query_rewriter import QueryRewriteResult
from backend.rag.retrieval_pipeline import (
    ContextCompressionStage,
    ExpansionStage,
    MergeStage,
    PipelineContext,
    PipelineStage,
    RerankStage,
    ResultBuilderStage,
    RetrievalPipeline,
    RetrievalStage,
    RewriteStage,
    StageResult,
    create_pipeline_from_config,
)
from backend.rag.retrieval_executor import RetrievalExecutor


def _make_chunk(text: str, doc_id: str = "1", chunk_index: int = 0, score: float = 0.5) -> RetrievedChunk:
    return RetrievedChunk(
        document=Document(
            page_content=text,
            metadata={"document_id": doc_id, "chunk_index": chunk_index, "filename": "test.pdf"},
        ),
        score=score,
    )


def _default_config(**kwargs) -> RetrievalConfig:
    qp_kwargs = {k: v for k, v in kwargs.items() if k.startswith("qp_")}
    other_kwargs = {k: v for k, v in kwargs.items() if not k.startswith("qp_")}
    qp = QueryProcessingConfig(**{k[3:]: v for k, v in qp_kwargs.items()})
    return RetrievalConfig(query_processing=qp, **other_kwargs)


class TestStageResult:
    def test_defaults(self):
        result = StageResult(chunks=[])
        assert result.chunks == []
        assert result.trace == {}

    def test_with_trace(self):
        result = StageResult(chunks=[_make_chunk("a")], trace={"stage": "test", "key": "value"})
        assert result.chunks[0].document.page_content == "a"
        assert result.trace["stage"] == "test"


class TestPipelineContext:
    def test_defaults(self):
        config = RetrievalConfig()
        ctx = PipelineContext(original_query="test", config=config)
        assert ctx.original_query == "test"
        assert ctx.config is config
        assert ctx.rewritten_query is None
        assert ctx.expanded_queries == []
        assert ctx.retrieved_chunks_per_query == []
        assert ctx.working_chunks == []
        assert ctx.pipeline_trace == []


class TestRewriteStage:
    def test_skipped_when_not_enabled(self):
        rewriter = MagicMock()
        stage = RewriteStage(rewriter)
        config = _default_config(qp_rewrite_enabled=False)
        ctx = PipelineContext(original_query="hello", config=config)
        result = stage.execute(ctx)
        assert ctx.rewritten_query is None
        rewriter.rewrite.assert_not_called()
        assert result.trace.get("skipped") is True

    def test_rewrites_when_enabled(self):
        rewriter = MagicMock()
        rewriter.rewrite.return_value = QueryRewriteResult(
            original_query="hello", retrieval_query="hello rewritten", rewritten=True,
        )
        stage = RewriteStage(rewriter)
        config = _default_config(qp_rewrite_enabled=True, qp_rewrite_strategy="llm")
        ctx = PipelineContext(original_query="hello", config=config)
        result = stage.execute(ctx)
        assert ctx.rewritten_query == "hello rewritten"
        rewriter.rewrite.assert_called_once_with("hello")

    def test_failure_falls_back(self):
        rewriter = MagicMock()
        rewriter.rewrite.side_effect = Exception("fail")
        stage = RewriteStage(rewriter)
        config = _default_config(qp_rewrite_enabled=True, qp_rewrite_strategy="llm")
        ctx = PipelineContext(original_query="hello", config=config)
        result = stage.execute(ctx)
        assert ctx.rewritten_query == "hello"
        assert result.trace.get("fallback") is True


class TestExpansionStage:
    def test_skipped_when_not_enabled(self):
        expander = MagicMock()
        stage = ExpansionStage(expander)
        config = _default_config(qp_expand_enabled=False)
        ctx = PipelineContext(original_query="hello", config=config)
        result = stage.execute(ctx)
        assert ctx.expanded_queries == ["hello"]
        expander.expand.assert_not_called()

    def test_expands_when_enabled(self):
        expander = MagicMock()
        expander.expand.return_value = QueryExpansionResult(
            original_query="hello",
            expanded_queries=["hello", "hello variant 1", "hello variant 2"],
            metadata={"strategy": "llm", "expansion_count": 3},
        )
        stage = ExpansionStage(expander)
        config = _default_config(qp_expand_enabled=True, qp_expand_strategy="llm", qp_expand_count=3)
        ctx = PipelineContext(original_query="hello", config=config)
        result = stage.execute(ctx)
        assert len(ctx.expanded_queries) == 3
        expander.expand.assert_called_once_with("hello")

    def test_uses_rewritten_query_when_available(self):
        expander = MagicMock()
        expander.expand.return_value = QueryExpansionResult(
            original_query="hello", expanded_queries=["hello rewritten"], metadata={},
        )
        stage = ExpansionStage(expander)
        config = _default_config(qp_expand_enabled=False)
        ctx = PipelineContext(original_query="hello", config=config)
        ctx.rewritten_query = "hello rewritten"
        result = stage.execute(ctx)
        assert ctx.expanded_queries == ["hello rewritten"]

    def test_failure_falls_back(self):
        expander = MagicMock()
        expander.expand.side_effect = Exception("fail")
        stage = ExpansionStage(expander)
        config = _default_config(qp_expand_enabled=True)
        ctx = PipelineContext(original_query="hello", config=config)
        result = stage.execute(ctx)
        assert ctx.expanded_queries == ["hello"]
        assert result.trace.get("fallback") is True


class TestRetrievalStage:
    def test_executes_all_queries(self):
        strategy = MagicMock()
        strategy.retrieve.return_value.chunks = [_make_chunk("result")]
        stage = RetrievalStage(strategy)
        config = _default_config()
        ctx = PipelineContext(original_query="test", config=config)
        ctx.expanded_queries = ["q1", "q2"]
        result = stage.execute(ctx)
        assert len(ctx.retrieved_chunks_per_query) == 2

    def test_uses_expanded_queries(self):
        strategy = MagicMock()
        strategy.retrieve.return_value.chunks = [_make_chunk("r")]
        stage = RetrievalStage(strategy)
        config = _default_config()
        ctx = PipelineContext(original_query="test", config=config)
        ctx.expanded_queries = ["q1", "q2", "q3"]
        result = stage.execute(ctx)
        assert len(ctx.retrieved_chunks_per_query) == 3

    def test_fallback_to_original_when_no_expanded(self):
        strategy = MagicMock()
        strategy.retrieve.return_value.chunks = [_make_chunk("r")]
        stage = RetrievalStage(strategy)
        config = _default_config()
        ctx = PipelineContext(original_query="original", config=config)
        ctx.expanded_queries = []
        result = stage.execute(ctx)
        assert len(ctx.retrieved_chunks_per_query) == 1


class TestMergeStage:
    def test_merges_multiple_results(self):
        stage = MergeStage()
        config = _default_config()
        ctx = PipelineContext(original_query="test", config=config)
        ctx.retrieved_chunks_per_query = [
            [_make_chunk("a", doc_id="1", chunk_index=0)],
            [_make_chunk("b", doc_id="1", chunk_index=1)],
        ]
        result = stage.execute(ctx)
        assert len(result.chunks) == 2

    def test_deduplicates_by_doc_id_chunk_index(self):
        stage = MergeStage()
        config = _default_config()
        ctx = PipelineContext(original_query="test", config=config)
        ctx.retrieved_chunks_per_query = [
            [_make_chunk("a", doc_id="1", chunk_index=0)],
            [_make_chunk("a duplicate", doc_id="1", chunk_index=0)],
        ]
        result = stage.execute(ctx)
        assert len(result.chunks) == 1
        assert result.trace["duplicates_removed"] == 1

    def test_empty_input(self):
        stage = MergeStage()
        config = _default_config()
        ctx = PipelineContext(original_query="test", config=config)
        ctx.retrieved_chunks_per_query = [[], []]
        result = stage.execute(ctx)
        assert result.chunks == []

    def test_returns_stage_result(self):
        stage = MergeStage()
        config = _default_config()
        ctx = PipelineContext(original_query="test", config=config)
        ctx.retrieved_chunks_per_query = [[_make_chunk("a")]]
        result = stage.execute(ctx)
        assert isinstance(result, StageResult)
        assert isinstance(result.chunks, list)
        assert isinstance(result.trace, dict)


class TestRerankStage:
    def test_skipped_when_reranker_disabled(self):
        reranker = MagicMock()
        stage = RerankStage(reranker)
        config = _default_config(reranker="none")
        ctx = PipelineContext(original_query="test", config=config)
        ctx.working_chunks = [_make_chunk("a"), _make_chunk("b")]
        result = stage.execute(ctx)
        assert len(result.chunks) == 2
        reranker.rerank.assert_not_called()

    def test_reranks_when_enabled(self):
        reranker = MagicMock()
        reranker.rerank.return_value = [_make_chunk("b"), _make_chunk("a")]
        stage = RerankStage(reranker)
        config = _default_config(reranker="cross_encoder", reranker_top_k=5)
        ctx = PipelineContext(original_query="test", config=config)
        chunks = [_make_chunk("a"), _make_chunk("b")]
        ctx.working_chunks = chunks
        result = stage.execute(ctx)
        assert len(result.chunks) == 2
        reranker.rerank.assert_called_once()

    def test_rerank_failure_falls_back(self):
        reranker = MagicMock()
        reranker.rerank.side_effect = Exception("fail")
        stage = RerankStage(reranker)
        config = _default_config(reranker="cross_encoder")
        ctx = PipelineContext(original_query="test", config=config)
        ctx.working_chunks = [_make_chunk("a")]
        result = stage.execute(ctx)
        assert len(result.chunks) == 1
        assert result.trace.get("fallback") is True

    def test_skipped_when_no_chunks(self):
        reranker = MagicMock()
        stage = RerankStage(reranker)
        config = _default_config(reranker="cross_encoder")
        ctx = PipelineContext(original_query="test", config=config)
        ctx.working_chunks = []
        result = stage.execute(ctx)
        assert result.chunks == []
        reranker.rerank.assert_not_called()

    def test_returns_stage_result(self):
        reranker = MagicMock()
        reranker.rerank.return_value = [_make_chunk("a")]
        stage = RerankStage(reranker)
        config = _default_config(reranker="cross_encoder")
        ctx = PipelineContext(original_query="test", config=config)
        ctx.working_chunks = [_make_chunk("a")]
        result = stage.execute(ctx)
        assert isinstance(result, StageResult)


class TestResultBuilderStage:
    def test_applies_final_top_k(self):
        stage = ResultBuilderStage()
        config = _default_config(reranker_top_k=2)
        ctx = PipelineContext(original_query="test", config=config)
        ctx.working_chunks = [_make_chunk(str(i)) for i in range(5)]
        result = stage.execute(ctx)
        assert len(result.chunks) == 2

    def test_preserves_all_when_under_top_k(self):
        stage = ResultBuilderStage()
        config = _default_config(reranker_top_k=10)
        ctx = PipelineContext(original_query="test", config=config)
        chunks = [_make_chunk("a"), _make_chunk("b")]
        ctx.working_chunks = chunks
        result = stage.execute(ctx)
        assert len(result.chunks) == 2

    def test_builds_pipeline_summary_in_trace(self):
        stage = ResultBuilderStage()
        config = _default_config(reranker="none")
        ctx = PipelineContext(original_query="test", config=config)
        ctx.expanded_queries = ["test"]
        ctx.retrieved_chunks_per_query = [[_make_chunk("a")]]
        ctx.working_chunks = [_make_chunk("a")]
        result = stage.execute(ctx)
        assert "summary" in result.trace
        assert any(s["stage"] == "result_builder" for s in result.trace["summary"])

    def test_returns_stage_result(self):
        stage = ResultBuilderStage()
        config = _default_config()
        ctx = PipelineContext(original_query="test", config=config)
        result = stage.execute(ctx)
        assert isinstance(result, StageResult)


class TestRetrievalPipeline:
    def test_execute_returns_serialized_and_result(self):
        pipeline = RetrievalPipeline()
        config = _default_config(qp_expand_enabled=False, reranker="none")
        result_serialized, result = pipeline.execute("test query", config)
        assert isinstance(result_serialized, str)
        assert isinstance(result, RetrievalResult)

    def test_execute_with_expansion(self):
        pipeline = RetrievalPipeline()
        config = _default_config(
            qp_expand_enabled=True, qp_expand_strategy="llm", qp_expand_count=3,
            reranker="none",
        )
        result_serialized, result = pipeline.execute("test query", config)
        assert isinstance(result_serialized, str)
        assert isinstance(result, RetrievalResult)

    def test_retrieval_query_in_result(self):
        pipeline = RetrievalPipeline()
        config = _default_config(qp_rewrite_enabled=False, qp_expand_enabled=False, reranker="none")
        result_serialized, result = pipeline.execute("my query", config)
        assert result.original_query == "my query"
        assert result.retrieval_query == "my query"

    def test_injected_dependencies_used(self):
        rewriter = MagicMock()
        rewriter.rewrite.return_value = QueryRewriteResult(
            original_query="q", retrieval_query="q", rewritten=False,
        )
        expander = MagicMock()
        expander.expand.return_value = QueryExpansionResult(
            original_query="q", expanded_queries=["q"], metadata={},
        )
        pipeline = RetrievalPipeline(
            query_rewriter=rewriter,
            query_expander=expander,
        )
        config = _default_config(
            qp_expand_enabled=True, qp_expand_strategy="llm",
            reranker="none",
        )
        pipeline.execute("q", config)
        rewriter.rewrite.assert_called_once_with("q")
        expander.expand.assert_called_once()

    def test_pipeline_trace_in_metadata(self):
        pipeline = RetrievalPipeline()
        config = _default_config(reranker="none")
        serialized, result = pipeline.execute("test", config)
        assert "pipeline" in result.retrieval_metadata
        assert "config" in result.retrieval_metadata

    def test_create_pipeline_from_config(self):
        config = _default_config()
        pipeline = create_pipeline_from_config(config)
        assert isinstance(pipeline, RetrievalPipeline)

    def test_create_pipeline_from_config_with_llm(self):
        config = _default_config(
            qp_rewrite_enabled=True, qp_rewrite_strategy="llm",
            qp_expand_enabled=True, qp_expand_strategy="llm", qp_expand_count=3,
            reranker="cross_encoder",
        )
        pipeline = create_pipeline_from_config(config)
        assert isinstance(pipeline, RetrievalPipeline)

    def test_working_chunks_updates_through_pipeline(self):
        """Verify the pipeline updates working_chunks from StageResult.chunks."""
        pipeline = RetrievalPipeline()
        config = _default_config(
            qp_rewrite_enabled=False,
            qp_expand_enabled=False,
            reranker="none",
        )
        serialized, result = pipeline.execute("test", config)
        # Final result chunks come from working_chunks after all stages
        assert len(result.chunks) <= config.reranker_top_k

    def test_pipeline_trace_collected(self):
        """Verify each stage's trace is collected in pipeline_trace."""
        pipeline = RetrievalPipeline()
        config = _default_config(
            qp_rewrite_enabled=False,
            qp_expand_enabled=False,
            reranker="none",
        )
        serialized, result = pipeline.execute("test", config)
        # pipeline_trace is replaced by the summary from ResultBuilderStage
        assert "pipeline" in result.retrieval_metadata
        assert "result_builder" in str(result.retrieval_metadata["pipeline"])
