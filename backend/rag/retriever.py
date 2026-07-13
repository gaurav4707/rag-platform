"""Retrieval tool for the Agentic RAG system.

This module provides the `retrieve_context` tool that the Agent uses to
retrieve relevant document chunks for a user query. It orchestrates the
retrieval pipeline including query rewriting and strategy selection.
"""

from langchain.tools import tool

from backend.rag.retrieval_config import DEFAULT_RETRIEVAL_CONFIG, RetrievalConfig
from backend.rag.query_rewriter import get_query_rewriter
from backend.rag.retrieval_strategies import get_strategy
from backend.rag.reranker import get_reranker
from backend.models.rag_models import RetrievalResult, RetrievedChunk

import logging

logger = logging.getLogger(__name__)


# Module-level wrappers for test patching compatibility
# These are called by the internal functions and can be patched by tests
# Tests patch: backend.rag.retriever.similarity_search_with_scores_filtered
# and: backend.rag.retriever.mmr_search_with_scores
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
    """Remove duplicate chunks based on stable identifier (document_id, chunk_index).

    Preserves the first occurrence (highest score) of each unique chunk.
    Only deduplicates when both identifiers are present and valid.
    """
    seen: set[tuple] = set()
    unique_chunks: list[tuple] = []

    for doc, score in chunks:
        doc_id = doc.metadata.get("document_id")
        chunk_index = doc.metadata.get("chunk_index")

        # Only deduplicate if both identifiers are present
        if doc_id is not None and chunk_index is not None:
            key = (doc_id, chunk_index)
            if key not in seen:
                seen.add(key)
                unique_chunks.append((doc, score))
        else:
            # Fallback: use content hash for chunks without metadata
            content_key = doc.page_content[:200]  # First 200 chars as fallback
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


@tool(response_format="content_and_artifact")
def retrieve_context(
    query: str,
    config: RetrievalConfig = DEFAULT_RETRIEVAL_CONFIG,
):
    """Retrieve information to help answer a query.

    Returns a RetrievalResult containing the query and retrieved chunks with scores.
    """
    # Use backward-compatible rewrite_query function
    try:
        retrieval_query = rewrite_query(query, config.query_rewrite)
        rewritten = retrieval_query != query
    except Exception:
        logger.warning("Query rewrite failed, using original query")
        retrieval_query = query
        rewritten = False

    # Select retrieval strategy based on config
    strategy = get_strategy(config.search_type, config.hybrid_enabled)

    # Execute retrieval with the (possibly rewritten) query
    retrieval_result = strategy.retrieve(
        query=retrieval_query,
        original_query=query,
        config=config,
    )

    # Apply reranking if enabled
    reranking_start = None
    reranking_applied = False
    candidate_count = len(retrieval_result.chunks)

    if config.reranker != "none" and retrieval_result.chunks:
        reranker = get_reranker(config.reranker)
        reranking_start = __import__("time").perf_counter()
        reranked_chunks = reranker.rerank(retrieval_query, retrieval_result.chunks)
        reranking_latency_ms = (__import__("time").perf_counter() - reranking_start) * 1000

        # Apply final top-k after reranking
        final_chunks = reranked_chunks[: config.reranker_top_k]

        retrieval_result.chunks = final_chunks
        reranking_applied = True

        logger.info(
            "Reranking applied: %s | Candidates: %d -> Final: %d",
            config.reranker,
            candidate_count,
            len(final_chunks),
        )
    else:
        reranking_latency_ms = None
        # Still apply final top-k for consistency
        retrieval_result.chunks = retrieval_result.chunks[: config.reranker_top_k]

    # Update retrieval metadata with query rewrite and reranking info
    retrieval_result.retrieval_metadata["query_rewritten"] = rewritten
    retrieval_result.retrieval_metadata["original_query"] = query
    retrieval_result.retrieval_metadata["retrieval_query"] = retrieval_query
    retrieval_result.retrieval_metadata["reranker"] = config.reranker
    retrieval_result.retrieval_metadata["reranking_applied"] = reranking_applied
    retrieval_result.retrieval_metadata["candidate_count"] = candidate_count
    retrieval_result.retrieval_metadata["final_count"] = len(retrieval_result.chunks)

    if reranking_latency_ms is not None:
        retrieval_result.retrieval_metadata["reranking_latency_ms"] = round(reranking_latency_ms, 1)

    # Serialize for the agent
    serialized = "\n\n".join(
        f"Source: {chunk.document.metadata}\nContent: {chunk.document.page_content}"
        for chunk in retrieval_result.chunks
    )

    _log_retrieval_details(
        query,
        retrieval_query,
        retrieval_result.chunks,
        retrieval_result.retrieval_metadata,
    )

    return serialized, retrieval_result


# Backward compatibility function for tests
def _rewrite_query(query: str, strategy: str = "none") -> str:
    """Internal rewrite query function used by backward compatibility wrapper."""
    rewriter = get_query_rewriter(strategy)
    result = rewriter.rewrite(query)
    return result.retrieval_query


def rewrite_query(query: str, strategy: str = "none") -> str:
    """Backward-compatible rewrite_query function.

    This function is maintained for backward compatibility with existing tests
    and code that imports from backend.rag.retriever.rewrite_query.

    New code should use the QueryRewriter classes directly.
    """
    return _rewrite_query(query, strategy)
