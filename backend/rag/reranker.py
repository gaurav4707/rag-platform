"""Cross-Encoder Reranking for Retrieval Enhancement.

This module provides a provider-agnostic reranking abstraction with a default
implementation using a local Hugging Face cross-encoder model.
"""

from __future__ import annotations
import truststore
truststore.inject_into_ssl()
import logging
import threading
import time
from typing import Protocol

from backend.models.rag_models import RetrievedChunk

logger = logging.getLogger(__name__)


class BaseReranker(Protocol):
    """Protocol for reranking implementations.

    Rerankers reorder retrieved chunks by relevance to the query.
    They must not perform retrieval themselves.
    """

    def rerank(
        self,
        query: str,
        chunks: list[RetrievedChunk],
    ) -> list[RetrievedChunk]:
        """Rerank chunks by relevance to the query.

        Args:
            query: The search query.
            chunks: List of retrieved chunks to rerank.

        Returns:
            Reranked list of chunks (same objects, new order).
        """
        ...

    @property
    def name(self) -> str:
        """Return the reranker identifier."""
        ...


class NoOpReranker:
    """No-op reranker that returns chunks unchanged.

    Used when reranking is disabled.
    """

    def rerank(
        self,
        query: str,
        chunks: list[RetrievedChunk],
    ) -> list[RetrievedChunk]:
        return chunks

    @property
    def name(self) -> str:
        return "none"


class CrossEncoderReranker:
    """Cross-encoder reranker using a local Hugging Face model.

    Uses a lightweight cross-encoder (default: cross-encoder/ms-marco-MiniLM-L-6-v2)
    to compute relevance scores between the query and each chunk.
    The model is lazy-loaded as a singleton and supports batch inference.
    """

    _instance: CrossEncoderReranker | None = None
    _model = None
    _lock = threading.Lock()

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(
        self,
        model_name: str = "cross-encoder/ms-marco-MiniLM-L-6-v2",
        device: str | None = None,
    ):
        if not hasattr(self, "_initialized"):
            self.model_name = model_name
            self.device = device
            self._initialized = True

    def _load_model(self):
        """Lazy-load the cross-encoder model."""
        if self._model is None:
            try:
                from sentence_transformers import CrossEncoder
            except ImportError as e:
                logger.error("sentence-transformers not installed: %s", e)
                raise

            logger.info("Loading cross-encoder model: %s", self.model_name)
            self._model = CrossEncoder(self.model_name, device=self.device)
            logger.info("Cross-encoder model loaded successfully")

    @classmethod
    def get_instance(
        cls,
        model_name: str = "cross-encoder/ms-marco-MiniLM-L-6-v2",
        device: str | None = None,
    ) -> CrossEncoderReranker:
        """Get or create the singleton instance."""
        if cls._instance is None:
            cls._instance = cls(model_name=model_name, device=device)
        return cls._instance

    def rerank(
        self,
        query: str,
        chunks: list[RetrievedChunk],
    ) -> list[RetrievedChunk]:
        """Rerank chunks using cross-encoder scores.

        Args:
            query: The search query.
            chunks: List of retrieved chunks to rerank.

        Returns:
            Reranked list of chunks sorted by relevance score (highest first).
        """
        if not chunks:
            return chunks

        start_time = time.perf_counter()

        try:
            self._load_model()

            # Prepare pairs for batch inference
            pairs = [(query, chunk.document.page_content) for chunk in chunks]

            # Batch inference
            model = self._model
            assert model is not None
            scores = model.predict(pairs, show_progress_bar=False)

            # Create new chunks with reranked scores
            scored_chunks = list(zip(chunks, scores, strict=False))
            scored_chunks.sort(key=lambda x: x[1], reverse=True)

            reranked = [chunk for chunk, _ in scored_chunks]

            latency_ms = (time.perf_counter() - start_time) * 1000
            logger.info(
                "Reranker: CrossEncoder | Candidates: %d | Returned: %d | Latency: %.1f ms",
                len(chunks),
                len(reranked),
                latency_ms,
            )

            return reranked

        except Exception as e:
            logger.exception("Cross-encoder reranking failed: %s", e)
            # Return original order on failure
            return chunks

    @property
    def name(self) -> str:
        return "cross_encoder"


def get_reranker(reranker_type: str = "cross_encoder", **kwargs) -> BaseReranker:
    """Factory function to get a reranker instance.

    Args:
        reranker_type: Type of reranker ("none" | "cross_encoder").
        **kwargs: Additional arguments for the reranker constructor.

    Returns:
        BaseReranker instance.
    """
    if reranker_type == "none":
        return NoOpReranker()
    elif reranker_type == "cross_encoder":
        return CrossEncoderReranker.get_instance(**kwargs)
    else:
        logger.warning("Unknown reranker type: %s, falling back to no-op", reranker_type)
        return NoOpReranker()
