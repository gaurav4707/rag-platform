"""Retrieval Pipeline - Composable multi-stage retrieval orchestration.

This module implements the Retrieval Pipeline, a composable orchestration layer
that coordinates query processing, retrieval, merging, parent retrieval,
reranking, context compression, and result building stages.

Architecture:
    User Query
        │
        ▼
    ┌──────────────────────────────────────────────────┐
    │                RETRIEVAL PIPELINE                │
    │                                                  │
    │  Stage 1: RewriteStage              (optional)   │
    │  Stage 2: ExpansionStage            (optional)   │
    │  Stage 3: RetrievalStage                         │
    │  Stage 4: MergeStage                             │
    │  Stage 5: ParentRetrievalStage      (optional)   │
    │  Stage 6: RerankStage               (optional)   │
    │  Stage 7: ContextCompressionStage   (optional)   │
    │  Stage 8: ResultBuilderStage                     │
    │                                                  │
    │  Each stage returns StageResult {chunks, trace}  │
    └──────────────────────────────────────────────────┘
        │
        ▼
  RetrievalResult (single, unified)

Stage semantics:
    - Each stage receives PipelineContext (read for query/config state)
    - Each stage returns StageResult (new chunks + trace) — immutable pattern
    - Stages update non-chunk context state directly (rewritten_query, expanded_queries)
    - Pipeline owns updating working_chunks from StageResult
"""

from __future__ import annotations

import logging
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Callable

from backend.rag.retrieval_config import QueryProcessingConfig, RetrievalConfig
from backend.rag.query_rewriter import BaseQueryRewriter, get_query_rewriter
from backend.rag.query_expander import BaseQueryExpander, get_query_expander
from backend.rag.retrieval_strategies import RetrievalStrategy, get_strategy
from backend.rag.reranker import BaseReranker, get_reranker
from backend.rag.retrieval_executor import RetrievalExecutor
from backend.rag.parent_retrieval import resolve_parents, get_parent_retrieval_metadata
from backend.rag.context_compression import BaseContextCompressor, get_context_compressor
from backend.storage.parent_store import BaseParentStore, FileParentStore
from backend.config import PARENT_STORAGE_DIR
from backend.models.rag_models import RetrievalResult, RetrievedChunk

logger = logging.getLogger(__name__)


@dataclass
class StageResult:
    """Result returned by each pipeline stage.

    Stages produce new chunks (immutable) and a trace entry for
    pipeline execution metadata. The pipeline collects these and
    updates working state.

    Attributes:
        chunks: Transformed chunk list (new list, not mutated in place).
        trace: Trace entry for pipeline execution metadata.
    """

    chunks: list[RetrievedChunk]
    trace: dict = field(default_factory=dict)


@dataclass
class PipelineContext:
    """Carries state through pipeline stages.

    PipelineContext stores execution state. Pipeline orchestration
    (updating working_chunks, collecting traces) belongs in
    RetrievalPipeline, not in helper methods here.
    """

    original_query: str
    config: RetrievalConfig

    # Query processing outputs
    rewritten_query: str | None = None
    expanded_queries: list[str] = field(default_factory=list)

    # Retrieval outputs
    retrieved_chunks_per_query: list[list[RetrievedChunk]] = field(default_factory=list)

    # Single source of truth for current chunk state
    # Updated by the pipeline from each stage's StageResult.chunks
    working_chunks: list[RetrievedChunk] = field(default_factory=list)

    # Pipeline execution trace (collected by pipeline from StageResult.trace)
    pipeline_trace: list[dict] = field(default_factory=list)


class PipelineStage(ABC):
    """Base class for pipeline stages.

    Each stage executes a single transformation step.
    Stages receive PipelineContext for reading state and config.
    They return StageResult containing new chunks and a trace entry.
    """

    @property
    @abstractmethod
    def name(self) -> str:
        """Stage name for tracing."""
        pass

    @abstractmethod
    def execute(self, context: PipelineContext) -> StageResult:
        """Execute the stage, returning transformed chunks and trace.

        Args:
            context: Pipeline execution state (read for query/config).

        Returns:
            StageResult with transformed chunks and trace metadata.
        """
        pass


class RewriteStage(PipelineStage):
    """Query rewriting stage."""

    def __init__(self, query_rewriter: BaseQueryRewriter):
        self.query_rewriter = query_rewriter

    @property
    def name(self) -> str:
        return "rewrite"

    def execute(self, context: PipelineContext) -> StageResult:
        qp_config = context.config.query_processing

        if not qp_config.rewrite_enabled:
            return StageResult(
                chunks=context.working_chunks,
                trace={"stage": "rewrite", "skipped": True},
            )

        try:
            result = self.query_rewriter.rewrite(context.original_query)
            context.rewritten_query = result.retrieval_query
            return StageResult(
                chunks=context.working_chunks,
                trace={
                    "stage": "rewrite",
                    "rewritten": result.rewritten,
                    "input": context.original_query,
                    "output": result.retrieval_query,
                },
            )
        except Exception as e:
            logger.warning("Query rewrite failed: %s", e)
            context.rewritten_query = context.original_query
            return StageResult(
                chunks=context.working_chunks,
                trace={
                    "stage": "rewrite",
                    "error": str(e),
                    "fallback": True,
                },
            )


class ExpansionStage(PipelineStage):
    """Query expansion (multi-query) stage."""

    def __init__(self, query_expander: BaseQueryExpander):
        self.query_expander = query_expander

    @property
    def name(self) -> str:
        return "expansion"

    def execute(self, context: PipelineContext) -> StageResult:
        qp_config = context.config.query_processing
        primary_query = context.rewritten_query or context.original_query

        if not qp_config.expand_enabled:
            context.expanded_queries = [primary_query]
            return StageResult(
                chunks=context.working_chunks,
                trace={"stage": "expansion", "skipped": True},
            )

        try:
            result = self.query_expander.expand(primary_query)
            context.expanded_queries = result.expanded_queries
            return StageResult(
                chunks=context.working_chunks,
                trace={
                    "stage": "expansion",
                    "primary_query": primary_query,
                    "expanded_queries": result.expanded_queries,
                    "count": len(result.expanded_queries),
                    "metadata": result.metadata,
                },
            )
        except Exception as e:
            logger.warning("Query expansion failed: %s", e)
            context.expanded_queries = [primary_query]
            return StageResult(
                chunks=context.working_chunks,
                trace={
                    "stage": "expansion",
                    "error": str(e),
                    "fallback": True,
                },
            )


class RetrievalStage(PipelineStage):
    """Retrieval stage - executes retrieval for each expanded query."""

    def __init__(
        self,
        strategy: RetrievalStrategy,
        executor: RetrievalExecutor | None = None,
    ):
        self.strategy = strategy
        self.executor = executor or RetrievalExecutor()

    @property
    def name(self) -> str:
        return "retrieval"

    def execute(self, context: PipelineContext) -> StageResult:
        queries = context.expanded_queries or [context.rewritten_query or context.original_query]

        def retrieve_fn(query: str) -> list[RetrievedChunk]:
            result = self.strategy.retrieve(
                query=query,
                original_query=context.original_query,
                config=context.config,
            )
            return result.chunks

        all_results = self.executor.execute_parallel(queries, retrieve_fn)
        context.retrieved_chunks_per_query = all_results

        total_candidates = sum(len(r) for r in all_results)
        return StageResult(
            chunks=context.working_chunks,
            trace={
                "stage": "retrieval",
                "strategy": context.config.search_type,
                "queries_executed": len(queries),
                "total_candidates": total_candidates,
            },
        )


class MergeStage(PipelineStage):
    """Merge and deduplicate chunks from multiple queries."""

    @property
    def name(self) -> str:
        return "merge"

    def execute(self, context: PipelineContext) -> StageResult:
        all_chunks = []
        for chunks in context.retrieved_chunks_per_query:
            all_chunks.extend(chunks)

        seen: set[tuple] = set()
        merged = []

        for chunk in all_chunks:
            doc_id = chunk.document.metadata.get("document_id")
            chunk_idx = chunk.document.metadata.get("chunk_index")

            if doc_id is not None and chunk_idx is not None:
                key = (doc_id, chunk_idx)
                if key not in seen:
                    seen.add(key)
                    merged.append(chunk)
            else:
                content_key = chunk.document.page_content[:200]
                if content_key not in seen:
                    seen.add(content_key)
                    merged.append(chunk)

        duplicates_removed = len(all_chunks) - len(merged)

        return StageResult(
            chunks=merged,
            trace={
                "stage": "merge",
                "total_chunks_before": len(all_chunks),
                "duplicates_removed": duplicates_removed,
                "merged_count": len(merged),
            },
        )


class ParentRetrievalStage(PipelineStage):
    """Resolves child chunks to parent blocks."""

    def __init__(self, parent_store: BaseParentStore | None = None):
        self.parent_store = parent_store or FileParentStore(PARENT_STORAGE_DIR)

    @property
    def name(self) -> str:
        return "parent_retrieval"

    def execute(self, context: PipelineContext) -> StageResult:
        if not context.config.parent_retrieval_enabled or not context.working_chunks:
            return StageResult(
                chunks=context.working_chunks,
                trace={"stage": "parent_retrieval", "skipped": True},
            )

        try:
            resolved = resolve_parents(context.working_chunks, self.parent_store)
            meta = get_parent_retrieval_metadata(context.working_chunks, resolved)
            return StageResult(
                chunks=resolved,
                trace={"stage": "parent_retrieval", **meta},
            )
        except Exception as e:
            logger.warning("Parent retrieval failed: %s", e)
            return StageResult(
                chunks=context.working_chunks,
                trace={
                    "stage": "parent_retrieval",
                    "error": str(e),
                    "fallback": True,
                },
            )


class RerankStage(PipelineStage):
    """Reranking stage."""

    def __init__(self, reranker: BaseReranker):
        self.reranker = reranker

    @property
    def name(self) -> str:
        return "reranking"

    def execute(self, context: PipelineContext) -> StageResult:
        candidates = context.working_chunks

        if context.config.reranker == "none" or not candidates:
            return StageResult(
                chunks=candidates,
                trace={"stage": "reranking", "skipped": True},
            )

        primary_query = context.rewritten_query or context.original_query

        try:
            reranked = self.reranker.rerank(primary_query, candidates)
            return StageResult(
                chunks=reranked,
                trace={
                    "stage": "reranking",
                    "reranker": context.config.reranker,
                    "candidates_before": len(candidates),
                    "candidates_after": len(reranked),
                },
            )
        except Exception as e:
            logger.warning("Reranking failed: %s", e)
            return StageResult(
                chunks=candidates,
                trace={
                    "stage": "reranking",
                    "error": str(e),
                    "fallback": True,
                },
            )


class ContextCompressionStage(PipelineStage):
    """Context compression stage.

    Compresses working chunks by removing content irrelevant to the query.
    Runs after reranking so the scorer/LLM only processes the highest-ranked
    chunks that will survive the final top-k selection.
    """

    def __init__(self, compressor: BaseContextCompressor):
        self.compressor = compressor

    @property
    def name(self) -> str:
        return "context_compression"

    def execute(self, context: PipelineContext) -> StageResult:
        candidates = context.working_chunks

        if context.config.compression_strategy == "none" or not candidates:
            return StageResult(
                chunks=candidates,
                trace={"stage": "context_compression", "skipped": True},
            )

        primary_query = context.rewritten_query or context.original_query
        start = time.perf_counter()

        try:
            original_tokens = sum(len(c.document.page_content.split()) for c in candidates)
            original_chars = sum(len(c.document.page_content) for c in candidates)

            compressed = self.compressor.compress(
                primary_query,
                candidates,
                target_ratio=context.config.compression_target_ratio,
            )

            latency_ms = (time.perf_counter() - start) * 1000
            compressed_tokens = sum(len(c.document.page_content.split()) for c in compressed)
            compressed_chars = sum(len(c.document.page_content) for c in compressed)
            ratio = compressed_tokens / original_tokens if original_tokens > 0 else 1.0

            return StageResult(
                chunks=compressed,
                trace={
                    "stage": "context_compression",
                    "strategy": context.config.compression_strategy,
                    "scorer": context.config.compression_scoring if context.config.compression_strategy == "extractive" else None,
                    "original_tokens": original_tokens,
                    "compressed_tokens": compressed_tokens,
                    "tokens_saved": original_tokens - compressed_tokens,
                    "compression_ratio": round(ratio, 3),
                    "characters_saved": original_chars - compressed_chars,
                    "latency_ms": round(latency_ms, 1),
                },
            )
        except Exception as e:
            logger.warning("Context compression failed: %s", e)
            return StageResult(
                chunks=candidates,
                trace={
                    "stage": "context_compression",
                    "error": str(e),
                    "fallback": True,
                },
            )


class ResultBuilderStage(PipelineStage):
    """Final result building stage.

    Applies final top-k truncation and builds the pipeline summary
    trace that gets serialized into RetrievalResult metadata.
    """

    @property
    def name(self) -> str:
        return "result_builder"

    def execute(self, context: PipelineContext) -> StageResult:
        final_chunks = context.working_chunks[: context.config.reranker_top_k]

        qp_config = context.config.query_processing

        pipeline_summary = []

        if qp_config.rewrite_enabled:
            pipeline_summary.append({
                "stage": "rewrite",
                "enabled": True,
                "strategy": qp_config.rewrite_strategy,
            })

        if qp_config.expand_enabled:
            pipeline_summary.append({
                "stage": "expansion",
                "enabled": True,
                "strategy": qp_config.expand_strategy,
                "count": qp_config.expand_count,
                "queries_generated": len(context.expanded_queries),
            })

        pipeline_summary.extend([
            {
                "stage": "retrieval",
                "strategy": context.config.search_type,
                "queries_executed": len(context.expanded_queries),
                "total_candidates": sum(len(r) for r in context.retrieved_chunks_per_query),
            },
            {
                "stage": "merge",
                "duplicates_removed": sum(len(r) for r in context.retrieved_chunks_per_query) - len(context.working_chunks),
                "merged_count": len(context.working_chunks),
            },
        ])

        if context.config.parent_retrieval_enabled:
            pipeline_summary.append({
                "stage": "parent_retrieval",
            })

        if context.config.reranker != "none":
            pipeline_summary.append({
                "stage": "reranking",
                "reranker": context.config.reranker,
            })

        if context.config.compression_strategy != "none":
            pipeline_summary.append({
                "stage": "context_compression",
                "strategy": context.config.compression_strategy,
            })

        pipeline_summary.append({
            "stage": "result_builder",
            "final_count": len(final_chunks),
        })

        return StageResult(
            chunks=final_chunks,
            trace={
                "stage": "result_builder",
                "final_count": len(final_chunks),
                "summary": pipeline_summary,
            },
        )


class RetrievalPipeline:
    """Main pipeline orchestrator.

    Owns pipeline configuration and stage execution. The pipeline
    is responsible for:
        - Building stages from config
        - Executing each stage sequentially
        - Updating working_chunks from StageResult.chunks
        - Collecting pipeline_trace from StageResult.trace
        - Building the final RetrievalResult
    """

    def __init__(
        self,
        query_rewriter: BaseQueryRewriter | None = None,
        query_expander: BaseQueryExpander | None = None,
        strategy: RetrievalStrategy | None = None,
        reranker: BaseReranker | None = None,
        compressor: BaseContextCompressor | None = None,
        executor: RetrievalExecutor | None = None,
    ):
        """Initialize pipeline with optional injected dependencies.

        Args:
            query_rewriter: Query rewriter (created from config if None).
            query_expander: Query expander (created from config if None).
            strategy: Retrieval strategy (created from config if None).
            reranker: Reranker (created from config if None).
            compressor: Context compressor (created from config if None).
            executor: Retrieval executor (created if None).
        """
        self._query_rewriter = query_rewriter
        self._query_expander = query_expander
        self._strategy = strategy
        self._reranker = reranker
        self._compressor = compressor
        self._executor = executor or RetrievalExecutor()

        self._stages: list[PipelineStage] | None = None

    def _build_stages(self, config: RetrievalConfig):
        """Build pipeline stages from config."""
        qp_config = config.query_processing

        rewriter = self._query_rewriter or get_query_rewriter(qp_config.rewrite_strategy)
        expander = self._query_expander or get_query_expander(
            qp_config.expand_strategy,
            num_queries=qp_config.expand_count,
        )
        strategy = self._strategy or get_strategy(config.search_type, config.hybrid_enabled)
        reranker = self._reranker or get_reranker(config.reranker)
        compressor = self._compressor or get_context_compressor(
            config.compression_strategy,
            config.compression_scoring,
        )

        parent_store = FileParentStore(PARENT_STORAGE_DIR)

        self._stages = [
            RewriteStage(rewriter),
            ExpansionStage(expander),
            RetrievalStage(strategy, self._executor),
            MergeStage(),
            ParentRetrievalStage(parent_store),
            RerankStage(reranker),
            ContextCompressionStage(compressor),
            ResultBuilderStage(),
        ]

    def execute(self, query: str, config: RetrievalConfig) -> tuple[str, RetrievalResult]:
        """Execute the full pipeline.

        Each stage returns StageResult {chunks, trace}.
        The pipeline updates working_chunks and collects pipeline_trace.

        Args:
            query: The user's original query.
            config: Retrieval configuration.

        Returns:
            Tuple of (serialized_string, RetrievalResult) for the agent tool.
        """
        if self._stages is None:
            self._build_stages(config)

        stages = self._stages
        if stages is None:
            raise RuntimeError("Pipeline stages were not initialized")

        context = PipelineContext(
            original_query=query,
            config=config,
        )

        for stage in stages:
            result = stage.execute(context)
            context.working_chunks = result.chunks
            context.pipeline_trace.append(result.trace)

        retrieval_query = context.rewritten_query or context.original_query
        qp_config = config.query_processing

        pipeline_summary = context.pipeline_trace[-1].get("summary", []) if context.pipeline_trace else []

        result = RetrievalResult(
            original_query=context.original_query,
            retrieval_query=retrieval_query,
            chunks=context.working_chunks,
            retrieval_metadata={
                "pipeline": pipeline_summary,
                "config": {
                    "search_type": config.search_type,
                    "reranker": config.reranker,
                    "parent_retrieval_enabled": config.parent_retrieval_enabled,
                    "expand_enabled": qp_config.expand_enabled,
                    "expand_strategy": qp_config.expand_strategy,
                    "expand_count": qp_config.expand_count,
                    "rewrite_enabled": qp_config.rewrite_enabled,
                    "rewrite_strategy": qp_config.rewrite_strategy,
                    "compression_strategy": config.compression_strategy,
                    "compression_scoring": config.compression_scoring,
                },
            },
        )

        serialized = "\n\n".join(
            f"Source: {chunk.document.metadata}\nContent: {chunk.document.page_content}"
            for chunk in context.working_chunks
        )

        return serialized, result


def create_pipeline_from_config(config: RetrievalConfig) -> RetrievalPipeline:
    """Factory function to create a pipeline with config-based defaults.

    Args:
        config: RetrievalConfig with all pipeline settings.

    Returns:
        Configured RetrievalPipeline instance.
    """
    qp_config = config.query_processing

    query_rewriter = get_query_rewriter(qp_config.rewrite_strategy)
    query_expander = get_query_expander(
        qp_config.expand_strategy,
        num_queries=qp_config.expand_count,
    )
    strategy = get_strategy(config.search_type, config.hybrid_enabled)
    reranker = get_reranker(config.reranker)
    compressor = get_context_compressor(
        config.compression_strategy,
        config.compression_scoring,
    )

    return RetrievalPipeline(
        query_rewriter=query_rewriter,
        query_expander=query_expander,
        strategy=strategy,
        reranker=reranker,
        compressor=compressor,
    )
