"""Retrieval tool for the Agentic RAG system.

This module provides the `retrieve_context` tool that the Agent uses to
relev document chunks for a user query. All retrieval paths now route
through RetrievalPipeline for consistent behavior.

Architecture:
- `_single_query_retrieve` is a thin compat wrapper → RetrievalPipeline
- `retrieve_context` tool → always uses RetrievalPipeline
"""

from langchain.tools import tool

from backend.rag.retrieval_config import DEFAULT_RETRIEVAL_CONFIG, QueryProcessingConfig, RetrievalConfig
from backend.rag.query_rewriter import get_query_rewriter
from backend.rag.retrieval_strategies import get_strategy
from backend.rag.reranker import get_reranker
from backend.rag.query_parser import parse_query, build_metadata_filter
from backend.rag.retrieval_pipeline import create_pipeline_from_config
from backend.rag.parent_retrieval import resolve_parents, get_parent_retrieval_metadata
from backend.storage.parent_store import FileParentStore
from backend.config import PARENT_STORAGE_DIR
from backend.models.rag_models import RetrievalResult, RetrievedChunk

import logging
import time
from typing import Any

logger = logging.getLogger(__name__)


# ponytail: Module-level wrappers kept for test patching compatibility.
# Tests patch: backend.rag.retriever.similarity_search_with_scores_filtered
def similarity_search_with_scores_filtered(query: str, top_k: int, metadata_filter: dict | None = None):
    """Module-level wrapper for test patching."""
    from backend.rag.vector_store import similarity_search_with_scores_filtered as _fn
    return _fn(query, top_k, metadata_filter)


def mmr_search_with_scores(
    query: str,
    top_k: int,
    fetch_k: int,
    lambda_mult: float,
    metadata_filter: dict | None = None,
    maximal_marginal_relevance=None,
):
    """Module-level wrapper for test patching."""
    from backend.rag.vector_store import mmr_search_with_scores as _fn
    from backend.rag.vector_store import maximal_marginal_relevance as _mmr
    return _fn(
        query=query,
        top_k=top_k,
        fetch_k=fetch_k,
        lambda_mult=lambda_mult,
        metadata_filter=metadata_filter,
        maximal_marginal_relevance=_mmr if maximal_marginal_relevance is None else maximal_marginal_relevance,
    )


def _run_similarity_search(
    query: str,
    config: RetrievalConfig,
) -> list[tuple]:
    return similarity_search_with_scores_filtered(
        query=query,
        top_k=config.top_k,
        metadata_filter=config.metadata_filter,
    )


def _run_mmr_search(
    query: str,
    config: RetrievalConfig,
) -> list[tuple]:
    return mmr_search_with_scores(
        query=query,
        top_k=config.top_k,
        fetch_k=config.fetch_k,
        lambda_mult=config.lambda_mult,
        metadata_filter=config.metadata_filter,
    )


def _run_retrieval(
    query: str,
    config: RetrievalConfig,
) -> list[tuple]:
    if config.search_type == "similarity":
        return _run_similarity_search(query, config)
    if config.search_type == "mmr":
        return _run_mmr_search(query, config)
    raise ValueError(f"Unsupported search_type: {config.search_type}")


def _deduplicate_chunks(chunks: list[tuple]) -> list[tuple]:
    """Remove duplicate chunks based on stable identifier (document_id, chunk_index)."""
    seen: set[tuple] = set()
    unique_chunks: list[tuple] = []

    for doc, score in chunks:
        doc_id = doc.metadata.get("document_id")
        chunk_index = doc.metadata.get("chunk_index")

        if doc_id is not None and chunk_index is not None:
            key = (doc_id, chunk_index)
            if key not in seen:
                seen.add(key)
                unique_chunks.append((doc, score))
        else:
            content_key = doc.page_content[:200]
            if content_key not in seen:
                seen.add(content_key)
                unique_chunks.append((doc, score))

    return unique_chunks


def _log_retrieval_details(
    original_query: str,
    retrieval_query: str,
    chunks: list[RetrievedChunk],
    retrieval_metadata: dict | None = None,
) -> None:
    """Log detailed retrieval information for debugging."""
    logger.debug("\n=== Retrieval ===")
    logger.debug("Original Query : %s", original_query)
    logger.debug("Retrieval Query: %s", retrieval_query)
    logger.debug("Chunks Retrieved: %d", len(chunks))

    if retrieval_metadata:
        logger.debug("Strategy: %s", retrieval_metadata.get("strategy", "unknown"))
        logger.debug("Dense Results: %d", retrieval_metadata.get("dense_results", 0))
        logger.debug("BM25 Results: %d", retrieval_metadata.get("bm25_results", 0))
        logger.debug("Duplicates Removed: %d", retrieval_metadata.get("duplicates_removed", 0))
        logger.debug("Fusion: %s", retrieval_metadata.get("fusion", "none"))
        logger.debug("Query Rewritten: %s", retrieval_metadata.get("query_rewritten", False))
        logger.debug("Reranker: %s", retrieval_metadata.get("reranker", "none"))
        logger.debug("Reranking Applied: %s", retrieval_metadata.get("reranking_applied", False))
        logger.debug("Candidate Count: %d", retrieval_metadata.get("candidate_count", 0))
        logger.debug("Final Count: %d", retrieval_metadata.get("final_count", 0))
        logger.debug("Reranking Latency (ms): %s", retrieval_metadata.get("reranking_latency_ms", "N/A"))

    for i, chunk in enumerate(chunks):
        meta = chunk.document.metadata
        doc_id = meta.get("document_id", "unknown")
        filename = meta.get("filename", "unknown")
        page = meta.get("page", "unknown")
        chunk_idx = meta.get("chunk_index", "unknown")
        score = chunk.score
        preview = chunk.document.page_content[:300].replace("\n", " ")

        logger.debug(
            "  Chunk %d: doc_id=%s, filename=%s, page=%s, chunk_index=%s, score=%.4f, preview=%s",
            i + 1,
            doc_id,
            filename,
            page,
            chunk_idx,
            score,
            preview,
        )


# Backward compatibility functions

def _rewrite_query(query: str, strategy: str = "none") -> str:
    rewriter = get_query_rewriter(strategy)
    result = rewriter.rewrite(query)
    return result.retrieval_query


def rewrite_query(query: str, strategy: str = "none") -> str:
    """Backward-compatible rewrite_query function."""
    return _rewrite_query(query, strategy)


def _single_query_retrieve(
    query: str,
    config: RetrievalConfig,
    original_query: str | None = None,
) -> tuple[str, RetrievalResult]:
    """Thin compatibility wrapper around RetrievalPipeline.

    Disables expansion to maintain single-query semantics.
    All other settings (rewrite, rerank, parent retrieval, compression)
    pass through to the pipeline.

    Returns (serialized_string, RetrievalResult) matching the legacy interface.
    """
    qp = QueryProcessingConfig(
        rewrite_enabled=config.query_processing.rewrite_enabled,
        rewrite_strategy=config.query_processing.rewrite_strategy,
        expand_enabled=False,
    )

    pipeline_config = RetrievalConfig(
        top_k=config.top_k,
        search_type=config.search_type,
        score_threshold=config.score_threshold,
        fetch_k=config.fetch_k,
        lambda_mult=config.lambda_mult,
        metadata_filter=config.metadata_filter,
        query_processing=qp,
        dense_top_k=config.dense_top_k,
        bm25_top_k=config.bm25_top_k,
        final_top_k=config.final_top_k,
        rrf_k=config.rrf_k,
        hybrid_enabled=config.hybrid_enabled,
        parent_retrieval_enabled=config.parent_retrieval_enabled,
        parent_target_size=config.parent_target_size,
        parent_overlap=config.parent_overlap,
        reranker=config.reranker,
        reranker_top_k=config.reranker_top_k,
        compression_strategy=config.compression_strategy,
        compression_scoring=config.compression_scoring,
        compression_target_ratio=config.compression_target_ratio,
        compression_max_tokens=config.compression_max_tokens,
    )

    pipeline = create_pipeline_from_config(pipeline_config)
    serialized, artifact = pipeline.execute(query, pipeline_config)

    # Log for backward compat
    _log_retrieval_details(
        original_query or query,
        artifact.retrieval_query,
        artifact.chunks,
        artifact.retrieval_metadata,
    )

    return serialized, artifact


def _retrieve_context(
    query: str,
    config: RetrievalConfig = DEFAULT_RETRIEVAL_CONFIG,
):
    """Retrieve information to help answer a query.

    Returns a RetrievalResult containing the query and retrieved chunks with scores.

    Supports two modes:
    - Single-query (default): rewrite → retrieve → rerank → compress
    - Multi-query (when expand_enabled=True): rewrite → expand → parallel retrieve → merge → rerank → compress
    """
    parsed = parse_query(query)

    metadata_filter = build_metadata_filter(
        page=parsed.page,
        existing_filter=config.metadata_filter,
    )

    updated_config = RetrievalConfig(
        top_k=config.top_k,
        search_type=config.search_type,
        score_threshold=config.score_threshold,
        fetch_k=config.fetch_k,
        lambda_mult=config.lambda_mult,
        metadata_filter=metadata_filter,
        query_processing=config.query_processing,
        dense_top_k=config.dense_top_k,
        bm25_top_k=config.bm25_top_k,
        final_top_k=config.final_top_k,
        rrf_k=config.rrf_k,
        hybrid_enabled=config.hybrid_enabled,
        parent_retrieval_enabled=config.parent_retrieval_enabled,
        parent_target_size=config.parent_target_size,
        parent_overlap=config.parent_overlap,
        reranker=config.reranker,
        reranker_top_k=config.reranker_top_k,
        compression_strategy=config.compression_strategy,
        compression_scoring=config.compression_scoring,
        compression_target_ratio=config.compression_target_ratio,
        compression_max_tokens=config.compression_max_tokens,
    )

    qp_config = updated_config.query_processing

    if qp_config.expand_enabled:
        pipeline = create_pipeline_from_config(updated_config)
        serialized, artifact = pipeline.execute(parsed.cleaned_query, updated_config)
        return serialized, artifact
    else:
        return _single_query_retrieve(
            parsed.cleaned_query,
            updated_config,
            original_query=parsed.original_query,
        )


retrieve_context: Any = tool(response_format="content_and_artifact")(_retrieve_context)
