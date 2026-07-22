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
    ExpansionStage,
    MergeStage,
    PipelineContext,
    PipelineStage,
    RerankStage,
    ResultBuilderStage,
    RetrievalPipeline,
    RetrievalStage,
    RewriteStage,
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


class TestPipelineContext:
    def test_defaults(self):
        config = RetrievalConfig()
        ctx = PipelineContext(original_query="test", config=config)
        assert ctx.original_query == "test"
        assert ctx.config is config
        assert ctx.rewritten_query is None
        assert ctx.expanded_queries == []
        assert ctx.retrieved_chunks_per_query == []
        assert ctx.merged_chunks == []
        assert ctx.reranked_chunks == []
        assert ctx.final_chunks == []
        assert ctx.pipeline_trace == []


class TestRewriteStage:
    def test_skipped_when_not_enabled(self):
        rewriter = MagicMock()
        stage = RewriteStage(rewriter)
        config = _default_config(qp_rewrite_enabled=False)
        ctx = PipelineContext(original_query="hello", config=config)
        result = stage.execute(ctx)
        assert result.rewritten_query is None
        rewriter.rewrite.assert_not_called()
        assert result.pipeline_trace[-1]["skipped"] is True

    def test_rewrites_when_enabled(self):
        rewriter = MagicMock()
        rewriter.rewrite.return_value = QueryRewriteResult(
            original_query="hello", retrieval_query="hello rewritten", rewritten=True,
        )
        stage = RewriteStage(rewriter)
        config = _default_config(qp_rewrite_enabled=True, qp_rewrite_strategy="llm")
        ctx = PipelineContext(original_query="hello", config=config)
        result = stage.execute(ctx)
        assert result.rewritten_query == "hello rewritten"
        rewriter.rewrite.assert_called_once_with("hello")

    def test_failure_falls_back(self):
        rewriter = MagicMock()
        rewriter.rewrite.side_effect = Exception("fail")
        stage = RewriteStage(rewriter)
        config = _default_config(qp_rewrite_enabled=True, qp_rewrite_strategy="llm")
        ctx = PipelineContext(original_query="hello", config=config)
        result = stage.execute(ctx)
        assert result.rewritten_query == "hello"
        assert result.pipeline_trace[-1].get("fallback") is True


class TestExpansionStage:
    def test_skipped_when_not_enabled(self):
        expander = MagicMock()
        stage = ExpansionStage(expander)
        config = _default_config(qp_expand_enabled=False)
        ctx = PipelineContext(original_query="hello", config=config)
        result = stage.execute(ctx)
        assert result.expanded_queries == ["hello"]
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
        assert len(result.expanded_queries) == 3
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
        assert result.expanded_queries == ["hello rewritten"]

    def test_failure_falls_back(self):
        expander = MagicMock()
        expander.expand.side_effect = Exception("fail")
        stage = ExpansionStage(expander)
        config = _default_config(qp_expand_enabled=True)
        ctx = PipelineContext(original_query="hello", config=config)
        result = stage.execute(ctx)
        assert result.expanded_queries == ["hello"]
        assert result.pipeline_trace[-1].get("fallback") is True


class TestRetrievalStage:
    def test_executes_all_queries(self):
        strategy = MagicMock()
        strategy.retrieve.return_value.chunks = [_make_chunk("result")]
        stage = RetrievalStage(strategy)
        config = _default_config()
        ctx = PipelineContext(original_query="test", config=config)
        ctx.expanded_queries = ["q1", "q2"]
        result = stage.execute(ctx)
        assert len(result.retrieved_chunks_per_query) == 2

    def test_uses_expanded_queries(self):
        strategy = MagicMock()
        strategy.retrieve.return_value.chunks = [_make_chunk("r")]
        stage = RetrievalStage(strategy)
        config = _default_config()
        ctx = PipelineContext(original_query="test", config=config)
        ctx.expanded_queries = ["q1", "q2", "q3"]
        result = stage.execute(ctx)
        assert len(result.retrieved_chunks_per_query) == 3

    def test_fallback_to_original_when_no_expanded(self):
        strategy = MagicMock()
        strategy.retrieve.return_value.chunks = [_make_chunk("r")]
        stage = RetrievalStage(strategy)
        config = _default_config()
        ctx = PipelineContext(original_query="original", config=config)
        ctx.expanded_queries = []
        result = stage.execute(ctx)
        assert len(result.retrieved_chunks_per_query) == 1


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
        assert len(result.merged_chunks) == 2

    def test_deduplicates_by_doc_id_chunk_index(self):
        stage = MergeStage()
        config = _default_config()
        ctx = PipelineContext(original_query="test", config=config)
        ctx.retrieved_chunks_per_query = [
            [_make_chunk("a", doc_id="1", chunk_index=0)],
            [_make_chunk("a duplicate", doc_id="1", chunk_index=0)],
        ]
        result = stage.execute(ctx)
        assert len(result.merged_chunks) == 1
        assert result.pipeline_trace[-1]["duplicates_removed"] == 1

    def test_empty_input(self):
        stage = MergeStage()
        config = _default_config()
        ctx = PipelineContext(original_query="test", config=config)
        ctx.retrieved_chunks_per_query = [[], []]
        result = stage.execute(ctx)
        assert result.merged_chunks == []


class TestRerankStage:
    def test_skipped_when_reranker_disabled(self):
        reranker = MagicMock()
        stage = RerankStage(reranker)
        config = _default_config(reranker="none")
        ctx = PipelineContext(original_query="test", config=config)
        ctx.merged_chunks = [_make_chunk("a"), _make_chunk("b")]
        result = stage.execute(ctx)
        assert len(result.reranked_chunks) == 2
        reranker.rerank.assert_not_called()

    def test_reranks_when_enabled(self):
        reranker = MagicMock()
        reranker.rerank.return_value = [_make_chunk("b"), _make_chunk("a")]
        stage = RerankStage(reranker)
        config = _default_config(reranker="cross_encoder", reranker_top_k=5)
        ctx = PipelineContext(original_query="test", config=config)
        chunks = [_make_chunk("a"), _make_chunk("b")]
        ctx.merged_chunks = chunks
        result = stage.execute(ctx)
        assert len(result.reranked_chunks) == 2
        reranker.rerank.assert_called_once()

    def test_rerank_failure_falls_back(self):
        reranker = MagicMock()
        reranker.rerank.side_effect = Exception("fail")
        stage = RerankStage(reranker)
        config = _default_config(reranker="cross_encoder")
        ctx = PipelineContext(original_query="test", config=config)
        ctx.merged_chunks = [_make_chunk("a")]
        result = stage.execute(ctx)
        assert len(result.reranked_chunks) == 1

    def test_skipped_when_no_chunks(self):
        reranker = MagicMock()
        stage = RerankStage(reranker)
        config = _default_config(reranker="cross_encoder")
        ctx = PipelineContext(original_query="test", config=config)
        ctx.merged_chunks = []
        result = stage.execute(ctx)
        assert result.reranked_chunks == []
        reranker.rerank.assert_not_called()


class TestResultBuilderStage:
    def test_uses_reranked_chunks(self):
        stage = ResultBuilderStage()
        config = _default_config(reranker_top_k=5)
        ctx = PipelineContext(original_query="test", config=config)
        ctx.reranked_chunks = [_make_chunk("a"), _make_chunk("b")]
        ctx.merged_chunks = [_make_chunk("c")]
        result = stage.execute(ctx)
        assert result.final_chunks == ctx.reranked_chunks

    def test_falls_back_to_merged(self):
        stage = ResultBuilderStage()
        config = _default_config(reranker_top_k=5)
        ctx = PipelineContext(original_query="test", config=config)
        ctx.reranked_chunks = []
        ctx.merged_chunks = [_make_chunk("a")]
        result = stage.execute(ctx)
        assert result.final_chunks == ctx.merged_chunks

    def test_applies_final_top_k(self):
        stage = ResultBuilderStage()
        config = _default_config(reranker_top_k=2)
        ctx = PipelineContext(original_query="test", config=config)
        ctx.reranked_chunks = [_make_chunk(str(i)) for i in range(5)]
        result = stage.execute(ctx)
        assert len(result.final_chunks) == 2

    def test_builds_pipeline_trace(self):
        stage = ResultBuilderStage()
        config = _default_config(reranker="none")
        ctx = PipelineContext(original_query="test", config=config)
        ctx.expanded_queries = ["test"]
        ctx.retrieved_chunks_per_query = [[_make_chunk("a")]]
        ctx.merged_chunks = [_make_chunk("a")]
        result = stage.execute(ctx)
        assert len(result.pipeline_trace) > 0
        assert any(s["stage"] == "result_builder" for s in result.pipeline_trace)


class TestRetrievalPipeline:
    def test_execute_returns_serialized_and_result(self):
        pipeline = RetrievalPipeline()
        config = _default_config(qp_expand_enabled=False)
        result_serialized, result = pipeline.execute("test query", config)
        assert isinstance(result_serialized, str)
        assert isinstance(result, RetrievalResult)

    def test_execute_with_expansion(self):
        pipeline = RetrievalPipeline()
        config = _default_config(qp_expand_enabled=True, qp_expand_strategy="llm", qp_expand_count=3)
        result_serialized, result = pipeline.execute("test query", config)
        assert isinstance(result_serialized, str)
        assert isinstance(result, RetrievalResult)

    def test_retrieval_query_in_result(self):
        pipeline = RetrievalPipeline()
        config = _default_config(qp_rewrite_enabled=False, qp_expand_enabled=False)
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
        config = _default_config(qp_expand_enabled=True, qp_expand_strategy="llm")
        pipeline.execute("q", config)
        rewriter.rewrite.assert_called_once_with("q")
        expander.expand.assert_called_once()

    def test_pipeline_trace_in_metadata(self):
        pipeline = RetrievalPipeline()
        config = _default_config()
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
        )
        pipeline = create_pipeline_from_config(config)
        assert isinstance(pipeline, RetrievalPipeline)
