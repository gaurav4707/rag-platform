"""Retrieval Pipeline - Composable multi-stage retrieval orchestration.

This module implements the Retrieval Pipeline, a composable orchestration layer
that coordinates query processing, retrieval, merging, and reranking stages.

Architecture:
    User Query
        │
        ▼
    ┌─────────────────────────────────────────┐
    │           RETRIEVAL PIPELINE            │
    │                                         │
    │  Stage 1: RewriteStage    (optional)    │
    │  Stage 2: ExpansionStage  (optional)    │
    │  Stage 3: RetrievalStage                │
    │  Stage 4: MergeStage                    │
    │  Stage 5: RerankStage      (optional)   │
    │  Stage 6: ResultBuilderStage            │
    │                                         │
    │  Future stages insertable without       │
    │  modifying existing stages.             │
    └─────────────────────────────────────────┘
        │
        ▼
RetrievalResult (single, unified)
"""

from __future__ import annotations

import logging
import time
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
from backend.models.rag_models import RetrievalResult, RetrievedChunk

logger = logging.getLogger(__name__)


@dataclass
class PipelineContext:
    """Carries state through pipeline stages."""

    original_query: str
    config: RetrievalConfig

    # Query processing outputs
    rewritten_query: str | None = None
    expanded_queries: list[str] = field(default_factory=list)

    # Retrieval outputs
    retrieved_chunks_per_query: list[list[RetrievedChunk]] = field(default_factory=list)
    merged_chunks: list[RetrievedChunk] = field(default_factory=list)
    reranked_chunks: list[RetrievedChunk] = field(default_factory=list)
    final_chunks: list[RetrievedChunk] = field(default_factory=list)

    # Pipeline trace
    pipeline_trace: list[dict] = field(default_factory=list)


class PipelineStage(ABC):
    """Base class for pipeline stages."""

    @property
    @abstractmethod
    def name(self) -> str:
        """Stage name for tracing."""
        pass

    @abstractmethod
    def execute(self, context: PipelineContext) -> PipelineContext:
        """Execute the stage, mutating and returning context."""
        pass


class RewriteStage(PipelineStage):
    """Query rewriting stage."""

    def __init__(self, query_rewriter: BaseQueryRewriter):
        self.query_rewriter = query_rewriter

    @property
    def name(self) -> str:
        return "rewrite"

    def execute(self, context: PipelineContext) -> PipelineContext:
        qp_config = context.config.query_processing

        if not qp_config.rewrite_enabled:
            context.pipeline_trace.append({"stage": "rewrite", "skipped": True})
            return context

        try:
            result = self.query_rewriter.rewrite(context.original_query)
            context.rewritten_query = result.retrieval_query
            context.pipeline_trace.append({
                "stage": "rewrite",
                "rewritten": result.rewritten,
                "input": context.original_query,
                "output": result.retrieval_query,
            })
        except Exception as e:
            logger.warning("Query rewrite failed: %s", e)
            context.rewritten_query = context.original_query
            context.pipeline_trace.append({
                "stage": "rewrite",
                "error": str(e),
                "fallback": True,
            })

        return context


class ExpansionStage(PipelineStage):
    """Query expansion (multi-query) stage."""

    def __init__(self, query_expander: BaseQueryExpander):
        self.query_expander = query_expander

    @property
    def name(self) -> str:
        return "expansion"

    def execute(self, context: PipelineContext) -> PipelineContext:
        qp_config = context.config.query_processing

        if not qp_config.expand_enabled:
            # Use rewritten query if available, else original
            primary_query = context.rewritten_query or context.original_query
            context.expanded_queries = [primary_query]
            context.pipeline_trace.append({"stage": "expansion", "skipped": True})
            return context

        primary_query = context.rewritten_query or context.original_query

        try:
            result = self.query_expander.expand(primary_query)
            context.expanded_queries = result.expanded_queries
            context.pipeline_trace.append({
                "stage": "expansion",
                "primary_query": primary_query,
                "expanded_queries": result.expanded_queries,
                "count": len(result.expanded_queries),
                "metadata": result.metadata,
            })
        except Exception as e:
            logger.warning("Query expansion failed: %s", e)
            context.expanded_queries = [primary_query]
            context.pipeline_trace.append({
                "stage": "expansion",
                "error": str(e),
                "fallback": True,
            })

        return context


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

    def execute(self, context: PipelineContext) -> PipelineContext:
        queries = context.expanded_queries or [context.rewritten_query or context.original_query]

        # Create retrieve function that uses the strategy
        def retrieve_fn(query: str) -> list[RetrievedChunk]:
            result = self.strategy.retrieve(
                query=query,
                original_query=context.original_query,
                config=context.config,
            )
            return result.chunks

        # Execute retrieval for all queries in parallel
        all_results = self.executor.execute_parallel(queries, retrieve_fn)
        context.retrieved_chunks_per_query = all_results

        total_candidates = sum(len(r) for r in all_results)
        context.pipeline_trace.append({
            "stage": "retrieval",
            "strategy": context.config.search_type,
            "queries_executed": len(queries),
            "total_candidates": total_candidates,
        })

        return context


class MergeStage(PipelineStage):
    """Merge and deduplicate chunks from multiple queries."""

    @property
    def name(self) -> str:
        return "merge"

    def execute(self, context: PipelineContext) -> PipelineContext:
        # Flatten all chunks
        all_chunks = []
        for chunks in context.retrieved_chunks_per_query:
            all_chunks.extend(chunks)

        # Deduplicate by (document_id, chunk_index)
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
                # Fallback: content-based dedupe
                content_key = chunk.document.page_content[:200]
                if content_key not in seen:
                    seen.add(content_key)
                    merged.append(chunk)

        context.merged_chunks = merged
        duplicates_removed = len(all_chunks) - len(merged)

        context.pipeline_trace.append({
            "stage": "merge",
            "total_chunks_before": len(all_chunks),
            "duplicates_removed": duplicates_removed,
            "merged_count": len(merged),
        })

        return context


class RerankStage(PipelineStage):
    """Reranking stage."""

    def __init__(self, reranker: BaseReranker):
        self.reranker = reranker

    @property
    def name(self) -> str:
        return "reranking"

    def execute(self, context: PipelineContext) -> PipelineContext:
        if context.config.reranker == "none" or not context.merged_chunks:
            context.reranked_chunks = context.merged_chunks
            context.pipeline_trace.append({"stage": "reranking", "skipped": True})
            return context

        # Use primary query for reranking
        primary_query = context.rewritten_query or context.original_query

        try:
            reranked = self.reranker.rerank(primary_query, context.merged_chunks)
            context.reranked_chunks = reranked

            context.pipeline_trace.append({
                "stage": "reranking",
                "reranker": context.config.reranker,
                "candidates_before": len(context.merged_chunks),
                "candidates_after": len(reranked),
            })
        except Exception as e:
            logger.warning("Reranking failed: %s", e)
            context.reranked_chunks = context.merged_chunks
            context.pipeline_trace.append({
                "stage": "reranking",
                "error": str(e),
                "fallback": True,
            })

        return context


class ResultBuilderStage(PipelineStage):
    """Final result building stage."""

    @property
    def name(self) -> str:
        return "result_builder"

    def execute(self, context: PipelineContext) -> PipelineContext:
        # Use reranked chunks if available, else merged
        chunks = context.reranked_chunks if context.reranked_chunks else context.merged_chunks

        # Apply final top-k
        final_chunks = chunks[: context.config.reranker_top_k]
        context.final_chunks = final_chunks

        # Build pipeline trace entry
        qp_config = context.config.query_processing

        pipeline_trace = []

        if qp_config.rewrite_enabled:
            pipeline_trace.append({
                "stage": "rewrite",
                "enabled": True,
                "strategy": qp_config.rewrite_strategy,
            })

        if qp_config.expand_enabled:
            pipeline_trace.append({
                "stage": "expansion",
                "enabled": True,
                "strategy": qp_config.expand_strategy,
                "count": qp_config.expand_count,
                "queries_generated": len(context.expanded_queries),
            })

        pipeline_trace.extend([
            {
                "stage": "retrieval",
                "strategy": context.config.search_type,
                "queries_executed": len(context.expanded_queries),
                "total_candidates": sum(len(r) for r in context.retrieved_chunks_per_query),
            },
            {
                "stage": "merge",
                "duplicates_removed": sum(len(r) for r in context.retrieved_chunks_per_query) - len(context.merged_chunks),
                "merged_count": len(context.merged_chunks),
            },
        ])

        if context.config.reranker != "none":
            pipeline_trace.append({
                "stage": "reranking",
                "reranker": context.config.reranker,
                "candidates_before": len(context.merged_chunks),
                "candidates_after": len(context.reranked_chunks) if context.reranked_chunks else len(context.merged_chunks),
            })

        pipeline_trace.append({
            "stage": "result_builder",
            "final_count": len(final_chunks),
        })

        # Update context's trace with the full pipeline trace
        context.pipeline_trace = pipeline_trace

        return context


class RetrievalPipeline:
    """Main pipeline orchestrator."""

    def __init__(
        self,
        query_rewriter: BaseQueryRewriter | None = None,
        query_expander: BaseQueryExpander | None = None,
        strategy: RetrievalStrategy | None = None,
        reranker: BaseReranker | None = None,
        executor: RetrievalExecutor | None = None,
    ):
        """Initialize pipeline with optional injected dependencies.

        Args:
            query_rewriter: Query rewriter (created from config if None)
            query_expander: Query expander (created from config if None)
            strategy: Retrieval strategy (created from config if None)
            reranker: Reranker (created from config if None)
            executor: Retrieval executor (created if None)
        """
        self._query_rewriter = query_rewriter
        self._query_expander = query_expander
        self._strategy = strategy
        self._reranker = reranker
        self._executor = executor or RetrievalExecutor()

        # Will be built on first execute() with config
        self._stages: list[PipelineStage] | None = None

    def _build_stages(self, config: RetrievalConfig):
        """Build pipeline stages from config."""
        qp_config = config.query_processing

        # Create components if not injected
        rewriter = self._query_rewriter or get_query_rewriter(qp_config.rewrite_strategy)
        expander = self._query_expander or get_query_expander(
            qp_config.expand_strategy,
            num_queries=qp_config.expand_count,
        )
        strategy = self._strategy or get_strategy(config.search_type, config.hybrid_enabled)
        reranker = self._reranker or get_reranker(config.reranker)

        self._stages = [
            RewriteStage(rewriter),
            ExpansionStage(expander),
            RetrievalStage(strategy, self._executor),
            MergeStage(),
            RerankStage(reranker),
            ResultBuilderStage(),
        ]

    def execute(self, query: str, config: RetrievalConfig) -> tuple[str, RetrievalResult]:
        """Execute the full pipeline.

        Args:
            query: The user's original query.
            config: Retrieval configuration.

        Returns:
            Tuple of (serialized_string, RetrievalResult) for the agent tool.
        """
        if self._stages is None:
            self._build_stages(config)

        context = PipelineContext(
            original_query=query,
            config=config,
        )

        # Execute all stages
        for stage in self._stages:
            context = stage.execute(context)

        # Build final RetrievalResult
        retrieval_query = context.rewritten_query or context.original_query
        qp_config = config.query_processing

        result = RetrievalResult(
            original_query=context.original_query,
            retrieval_query=retrieval_query,
            chunks=context.final_chunks,
            retrieval_metadata={
                "pipeline": context.pipeline_trace,
                "config": {
                    "search_type": config.search_type,
                    "reranker": config.reranker,
                    "expand_enabled": qp_config.expand_enabled,
                    "expand_strategy": qp_config.expand_strategy,
                    "expand_count": qp_config.expand_count,
                    "rewrite_enabled": qp_config.rewrite_enabled,
                    "rewrite_strategy": qp_config.rewrite_strategy,
                },
            },
        )

        # Serialize for agent
        serialized = "\n\n".join(
            f"Source: {chunk.document.metadata}\nContent: {chunk.document.page_content}"
            for chunk in context.final_chunks
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

    # Pre-create components for testability/performance
    query_rewriter = get_query_rewriter(qp_config.rewrite_strategy)
    query_expander = get_query_expander(
        qp_config.expand_strategy,
        num_queries=qp_config.expand_count,
    )
    strategy = get_strategy(config.search_type, config.hybrid_enabled)
    reranker = get_reranker(config.reranker)

    return RetrievalPipeline(
        query_rewriter=query_rewriter,
        query_expander=query_expander,
        strategy=strategy,
        reranker=reranker,
    )