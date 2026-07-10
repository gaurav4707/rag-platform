"""Retrieval Strategy Pattern Implementation.

Defines strategy classes for different retrieval approaches:
- SimilarityStrategy: Dense vector similarity search
- MMRStrategy: Maximum Marginal Relevance search
- HybridStrategy: Combined dense + BM25 with Reciprocal Rank Fusion
"""

from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from typing import Any

from backend.rag.retrieval_config import RetrievalConfig
from backend.models.rag_models import RetrievalResult, RetrievedChunk
from backend.rag.vector_store import (
    maximal_marginal_relevance,
    mmr_search_with_scores,
    similarity_search_with_scores_filtered,
)
from backend.rag.bm25 import search as bm25_search

logger = logging.getLogger(__name__)


class RetrievalStrategy(ABC):
    """Abstract base class for retrieval strategies."""

    @abstractmethod
    def retrieve(
        self,
        query: str,
        original_query: str | None,
        config: RetrievalConfig,
    ) -> RetrievalResult:
        """Execute retrieval and return results.

        Args:
            query: The (possibly rewritten) query to search with
            original_query: The original user query
            config: Retrieval configuration

        Returns:
            RetrievalResult with retrieved chunks and metadata
        """
        pass


class SimilarityStrategy(RetrievalStrategy):
    """Dense vector similarity search strategy."""

    def retrieve(
        self,
        query: str,
        original_query: str | None,
        config: RetrievalConfig,
    ) -> RetrievalResult:
        """Perform similarity search.

        Args:
            query: Search query
            original_query: Original user query
            config: Retrieval configuration

        Returns:
            RetrievalResult with dense retrieval results
        """
        if not query or not query.strip():
            logger.debug("Similarity retrieve: empty query")
            orig = original_query if original_query is not None else query
            return RetrievalResult(
                original_query=orig,
                retrieval_query=query,
                chunks=[],
                retrieval_metadata={"strategy": "similarity", "dense_results": 0},
            )

        try:
            dense_docs = similarity_search_with_scores_filtered(
                query=query,
                top_k=config.top_k,
                metadata_filter=config.metadata_filter,
            )
            dense_results = [
                RetrievedChunk(document=doc, score=score) for doc, score in dense_docs
            ]
            logger.debug("Dense retrieved: %d", len(dense_results))
        except Exception as e:
            logger.warning("Dense retrieval failed: %s", e)
            dense_results = []

        final_chunks = self._normalize_metadata(dense_results[: config.top_k])

        metadata = {
            "strategy": "similarity",
            "dense_results": len(dense_results),
            "final_results": len(final_chunks),
        }

        return RetrievalResult(
            original_query=original_query if original_query is not None else query,
            retrieval_query=query,
            chunks=final_chunks,
            retrieval_metadata=metadata,
        )

    def _normalize_metadata(self, chunks: list[RetrievedChunk]) -> list[RetrievedChunk]:
        """Ensure all chunks have consistent metadata fields."""
        normalized = []
        for chunk in chunks:
            metadata = chunk.document.metadata.copy()

            required_fields = ["document_id", "filename", "page", "chunk_index", "source"]
            for field in required_fields:
                if field not in metadata:
                    metadata[field] = "unknown" if field != "chunk_index" else -1

            doc = chunk.document.__class__(
                page_content=chunk.document.page_content,
                metadata=metadata,
            )
            normalized.append(RetrievedChunk(document=doc, score=chunk.score))

        return normalized


class MMRStrategy(RetrievalStrategy):
    """Maximum Marginal Relevance search strategy."""

    def retrieve(
        self,
        query: str,
        original_query: str | None,
        config: RetrievalConfig,
    ) -> RetrievalResult:
        """Perform MMR search.

        Args:
            query: Search query
            original_query: Original user query
            config: Retrieval configuration

        Returns:
            RetrievalResult with MMR results
        """
        if not query or not query.strip():
            logger.debug("MMR retrieve: empty query")
            orig = original_query if original_query is not None else query
            return RetrievalResult(
                original_query=orig,
                retrieval_query=query,
                chunks=[],
                retrieval_metadata={"strategy": "mmr", "mmr_results": 0},
            )

        try:
            mmr_docs = mmr_search_with_scores(
                query=query,
                top_k=config.top_k,
                fetch_k=config.fetch_k,
                lambda_mult=config.lambda_mult,
                metadata_filter=config.metadata_filter,
                maximal_marginal_relevance=maximal_marginal_relevance,
            )
            mmr_results = [
                RetrievedChunk(document=doc, score=score) for doc, score in mmr_docs
            ]
            logger.debug("MMR retrieved: %d", len(mmr_results))
        except Exception as e:
            logger.warning("MMR retrieval failed: %s", e)
            mmr_results = []

        final_chunks = self._normalize_metadata(mmr_results[: config.top_k])

        metadata = {
            "strategy": "mmr",
            "mmr_results": len(mmr_results),
            "final_results": len(final_chunks),
        }

        return RetrievalResult(
            original_query=original_query if original_query is not None else query,
            retrieval_query=query,
            chunks=final_chunks,
            retrieval_metadata=metadata,
        )

    def _normalize_metadata(self, chunks: list[RetrievedChunk]) -> list[RetrievedChunk]:
        """Ensure all chunks have consistent metadata fields."""
        normalized = []
        for chunk in chunks:
            metadata = chunk.document.metadata.copy()

            required_fields = ["document_id", "filename", "page", "chunk_index", "source"]
            for field in required_fields:
                if field not in metadata:
                    metadata[field] = "unknown" if field != "chunk_index" else -1

            doc = chunk.document.__class__(
                page_content=chunk.document.page_content,
                metadata=metadata,
            )
            normalized.append(RetrievedChunk(document=doc, score=chunk.score))

        return normalized


class HybridStrategy(RetrievalStrategy):
    """Hybrid retrieval combining dense and BM25 with Reciprocal Rank Fusion."""

    def __init__(self, hybrid_enabled: bool = True):
        """Initialize hybrid strategy.

        Args:
            hybrid_enabled: Whether hybrid retrieval is enabled
        """
        self.hybrid_enabled = hybrid_enabled

    def retrieve(
        self,
        query: str,
        original_query: str | None,
        config: RetrievalConfig,
    ) -> RetrievalResult:
        """Perform hybrid retrieval with RRF.

        Args:
            query: Search query
            original_query: Original user query
            config: Retrieval configuration

        Returns:
            RetrievalResult with fused results
        """
        if not query or not query.strip():
            logger.debug("Hybrid retrieve: empty query")
            orig = original_query if original_query is not None else query
            return RetrievalResult(
                original_query=orig,
                retrieval_query=query,
                chunks=[],
                retrieval_metadata={"strategy": "hybrid", "dense_results": 0, "bm25_results": 0},
            )

        dense_results: list[RetrievedChunk] = []
        bm25_results: list[RetrievedChunk] = []

        if self.hybrid_enabled:
            try:
                dense_docs = similarity_search_with_scores_filtered(
                    query=query,
                    top_k=config.dense_top_k,
                    metadata_filter=config.metadata_filter,
                )
                dense_results = [
                    RetrievedChunk(document=doc, score=score) for doc, score in dense_docs
                ]
                logger.debug("Dense retrieved: %d", len(dense_results))
            except Exception as e:
                logger.warning("Dense retrieval failed: %s", e)

            try:
                bm25_results = bm25_search(query, k=config.bm25_top_k)
                logger.debug("BM25 retrieved: %d", len(bm25_results))
            except Exception as e:
                logger.warning("BM25 retrieval failed: %s", e)

            fused = self._rrf_fuse(dense_results, bm25_results, k=config.rrf_k)

            dense_count = len(dense_results)
            bm25_count = len(bm25_results)
            fused_count = len(fused)
            duplicates = dense_count + bm25_count - fused_count

            logger.debug(
                "Dense: %d, BM25: %d, Fused: %d, Duplicates removed: %d",
                dense_count,
                bm25_count,
                fused_count,
                duplicates,
            )

            final_chunks = self._normalize_metadata(fused[: config.final_top_k])

            metadata = {
                "strategy": "hybrid",
                "dense_results": dense_count,
                "bm25_results": bm25_count,
                "duplicates_removed": duplicates,
                "fusion": "rrf",
                "rrf_k": config.rrf_k,
                "final_results": len(final_chunks),
            }

        else:
            # Fallback to dense only
            try:
                dense_docs = similarity_search_with_scores_filtered(
                    query=query,
                    top_k=config.final_top_k,
                    metadata_filter=config.metadata_filter,
                )
                final_chunks = self._normalize_metadata([
                    RetrievedChunk(document=doc, score=score) for doc, score in dense_docs
                ])
            except Exception as e:
                logger.warning("Dense retrieval failed: %s", e)
                final_chunks = []

            metadata = {
                "strategy": "hybrid",
                "dense_results": len(final_chunks),
                "bm25_results": 0,
                "fusion": "none",
                "final_results": len(final_chunks),
            }

        return RetrievalResult(
            original_query=original_query if original_query is not None else query,
            retrieval_query=query,
            chunks=final_chunks,
            retrieval_metadata=metadata,
        )

    def _rrf_fuse(
        self,
        dense_results: list[RetrievedChunk],
        bm25_results: list[RetrievedChunk],
        k: int = 60,
    ) -> list[RetrievedChunk]:
        """Merge dense and BM25 results using Reciprocal Rank Fusion.

        RRF formula: score = sum(1 / (k + rank)) for each result list.

        Args:
            dense_results: Results from dense retrieval (already ranked)
            bm25_results: Results from BM25 retrieval (already ranked)
            k: RRF constant (default 60)

        Returns:
            Fused and ranked list of unique chunks
        """
        if not dense_results and not bm25_results:
            return []

        rrf_scores: dict[str, float] = {}
        chunk_map: dict[str, RetrievedChunk] = {}

        def chunk_key(chunk: RetrievedChunk) -> str:
            """Generate a stable key for deduplication."""
            doc_id = chunk.document.metadata.get("document_id", "unknown")
            chunk_idx = chunk.document.metadata.get("chunk_index", "unknown")
            return f"{doc_id}:{chunk_idx}"

        for rank, chunk in enumerate(dense_results):
            key = chunk_key(chunk)
            rrf_scores[key] = rrf_scores.get(key, 0.0) + 1.0 / (k + rank + 1)
            if key not in chunk_map:
                chunk_map[key] = chunk

        for rank, chunk in enumerate(bm25_results):
            key = chunk_key(chunk)
            rrf_scores[key] = rrf_scores.get(key, 0.0) + 1.0 / (k + rank + 1)
            if key not in chunk_map:
                chunk_map[key] = chunk

        sorted_keys = sorted(rrf_scores.keys(), key=lambda k: rrf_scores[k], reverse=True)

        fused_results = []
        for key in sorted_keys:
            chunk = chunk_map[key]
            fused_results.append(RetrievedChunk(document=chunk.document, score=rrf_scores[key]))

        return fused_results

    def _normalize_metadata(self, chunks: list[RetrievedChunk]) -> list[RetrievedChunk]:
        """Ensure all chunks have consistent metadata fields."""
        normalized = []
        for chunk in chunks:
            metadata = chunk.document.metadata.copy()

            required_fields = ["document_id", "filename", "page", "chunk_index", "source"]
            for field in required_fields:
                if field not in metadata:
                    metadata[field] = "unknown" if field != "chunk_index" else -1

            doc = chunk.document.__class__(
                page_content=chunk.document.page_content,
                metadata=metadata,
            )
            normalized.append(RetrievedChunk(document=doc, score=chunk.score))

        return normalized


def get_strategy(search_type: str, hybrid_enabled: bool = True) -> RetrievalStrategy:
    """Factory function to get the appropriate retrieval strategy.

    Args:
        search_type: Type of search ("similarity", "mmr", "hybrid")
        hybrid_enabled: Whether hybrid retrieval is enabled

    Returns:
        RetrievalStrategy instance
    """
    if search_type == "similarity":
        return SimilarityStrategy()
    elif search_type == "mmr":
        return MMRStrategy()
    elif search_type == "hybrid":
        return HybridStrategy(hybrid_enabled=hybrid_enabled)
    else:
        raise ValueError(f"Unsupported search_type: {search_type}")