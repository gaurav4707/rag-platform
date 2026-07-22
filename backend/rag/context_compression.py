"""Context Compression for the Retrieval Pipeline.

This module provides a modular, provider-agnostic compression layer
that reduces irrelevant content from retrieved chunks before prompt
construction. Compression is NOT summarization — it removes irrelevant
portions while preserving answerable information.

Architecture:
    BaseRelevanceScorer (protocol)
        ├── KeywordScorer (default, lightweight)
        └── EmbeddingScorer (provider-backed, optional)

    BaseContextCompressor (protocol)
        ├── NoOpContextCompressor (pass-through)
        ├── ExtractiveContextCompressor (scorer-based sentence extraction)
        └── LLMContextCompressor (provider-backed, lazy init)
"""

from __future__ import annotations

import logging
import re
from typing import Any, Protocol

from langchain_core.documents import Document

from backend.models.rag_models import RetrievedChunk

logger = logging.getLogger(__name__)


class BaseRelevanceScorer(Protocol):
    """Protocol for scoring text relevance to a query.

    Designed to be reusable across Context Compression, Graph Retrieval,
    reranking, and other relevance-scoring consumers.
    """

    def score(self, query: str, text: str) -> float:
        """Score the relevance of a text span to the query.

        Args:
            query: The user's query or search intent.
            text: The text span to score.

        Returns:
            A relevance score between 0.0 (irrelevant) and 1.0 (highly relevant).
        """
        ...


class KeywordScorer:
    """Lightweight keyword-overlap relevance scorer.

    Scores text based on the proportion of query keywords present.
    Fast, no external dependencies, suitable as default.
    """

    def score(self, query: str, text: str) -> float:
        query_words = set(query.lower().split())
        if not query_words:
            return 0.0
        text_lower = text.lower()
        matches = sum(1 for w in query_words if w in text_lower)
        return matches / len(query_words)


class EmbeddingScorer:
    """Embedding-based semantic relevance scorer.

    Uses the configured embedding provider for cosine similarity.
    Lazy-initialized — embedding provider is loaded only on first call.
    """

    def __init__(self):
        self._embeddings: Any | None = None

    def _get_embeddings(self) -> Any:
        if self._embeddings is None:
            from backend.providers.embeddings import get_embedding_provider
            self._embeddings = get_embedding_provider()
        return self._embeddings

    def _cosine_similarity(self, a: list[float], b: list[float]) -> float:
        dot = sum(x * y for x, y in zip(a, b))
        norm_a = sum(x * x for x in a) ** 0.5
        norm_b = sum(x * x for x in b) ** 0.5
        if norm_a == 0 or norm_b == 0:
            return 0.0
        return dot / (norm_a * norm_b)

    def score(self, query: str, text: str) -> float:
        emb = self._get_embeddings()
        q_vec = emb.embed_query(query)
        t_vec = emb.embed_query(text)
        return self._cosine_similarity(q_vec, t_vec)


def get_relevance_scorer(scoring: str = "keyword") -> BaseRelevanceScorer:
    """Factory: create a relevance scorer by name.

    Args:
        scoring: Scorer type — "keyword" or "embedding".

    Returns:
        BaseRelevanceScorer instance.
    """
    if scoring == "keyword":
        return KeywordScorer()
    elif scoring == "embedding":
        return EmbeddingScorer()
    logger.warning("Unknown scoring strategy: %s, falling back to keyword", scoring)
    return KeywordScorer()


class BaseContextCompressor(Protocol):
    """Protocol for context compression implementations.

    Compressors remove irrelevant content from retrieved chunks while
    preserving metadata, provenance, and scores.
    """

    def compress(
        self,
        query: str,
        chunks: list[RetrievedChunk],
        target_ratio: float = 0.5,
    ) -> list[RetrievedChunk]:
        """Compress retrieved chunks by removing irrelevant content.

        Args:
            query: The user's query to determine relevance.
            chunks: Retrieved chunks to compress.
            target_ratio: Target compression ratio (1.0 = no compression,
                         0.5 = reduce to ~50% of original).

        Returns:
            New list of RetrievedChunk instances with compressed content
            and preserved metadata.
        """
        ...


class NoOpContextCompressor:
    """No-op compressor — returns chunks unchanged.

    Used when compression is disabled.
    """

    def compress(
        self,
        query: str,
        chunks: list[RetrievedChunk],
        target_ratio: float = 0.5,
    ) -> list[RetrievedChunk]:
        return chunks


class ExtractiveContextCompressor:
    """Extractive compressor using sentence-level relevance scoring.

    Scores each sentence against the query, keeps the highest-scoring
    sentences up to the target ratio, and preserves original sentence order.
    """

    def __init__(self, scorer: BaseRelevanceScorer):
        self.scorer = scorer

    def _split_sentences(self, text: str) -> list[str]:
        sentences = re.split(r"(?<=[.!?])\s+", text)
        return [s.strip() for s in sentences if s.strip()]

    def compress(
        self,
        query: str,
        chunks: list[RetrievedChunk],
        target_ratio: float = 0.5,
    ) -> list[RetrievedChunk]:
        compressed = []
        for chunk in chunks:
            sentences = self._split_sentences(chunk.document.page_content)
            if len(sentences) <= 1:
                compressed.append(chunk)
                continue

            scored = [(s, self.scorer.score(query, s)) for s in sentences]
            scored.sort(key=lambda x: x[1], reverse=True)

            keep_count = max(1, int(len(sentences) * target_ratio))
            keep_texts = set(s for s, _ in scored[:keep_count])

            compressed_text = " ".join(s for s in sentences if s in keep_texts)
            new_doc = Document(
                page_content=compressed_text,
                metadata=dict(chunk.document.metadata),
            )
            compressed.append(RetrievedChunk(document=new_doc, score=chunk.score))

        return compressed


class LLMContextCompressor:
    """LLM-based compressor that removes irrelevant content per chunk.

    Lazy-initialized — the LLM provider is loaded only when compression
    is actually invoked.
    """

    def __init__(self, llm=None):
        self._llm: Any | None = llm
        self._initialized = False

    def _get_llm(self) -> Any:
        if not self._initialized:
            if self._llm is None:
                from backend.providers.llm import get_llm
                self._llm = get_llm()
            self._initialized = True
        return self._llm

    def _build_prompt(self, query: str, text: str) -> str:
        return (
            "You are a text compression assistant. Remove irrelevant "
            "information from the text below while preserving ALL information "
            "relevant to answering the question. Do NOT summarize — only remove "
            "irrelevant parts. Return only the compressed text.\n\n"
            f"Question: {query}\n\n"
            f"Text:\n{text}"
        )

    def compress(
        self,
        query: str,
        chunks: list[RetrievedChunk],
        target_ratio: float = 0.5,
    ) -> list[RetrievedChunk]:
        llm = self._get_llm()
        if llm is None:
            raise RuntimeError("LLM provider is unavailable")
        compressed = []
        for chunk in chunks:
            try:
                prompt = self._build_prompt(query, chunk.document.page_content)
                result = llm.invoke(prompt)
                compressed_text = result.content.strip() if hasattr(result, "content") else str(result).strip()
                if not compressed_text:
                    compressed_text = chunk.document.page_content
            except Exception as e:
                logger.warning("LLM compression failed for chunk, using original: %s", e)
                compressed_text = chunk.document.page_content

            new_doc = Document(
                page_content=compressed_text,
                metadata=dict(chunk.document.metadata),
            )
            compressed.append(RetrievedChunk(document=new_doc, score=chunk.score))

        return compressed


def get_context_compressor(
    strategy: str = "none",
    scoring: str = "keyword",
) -> BaseContextCompressor:
    """Factory: create a context compressor by strategy.

    Args:
        strategy: Compression strategy — "none", "extractive", or "llm".
        scoring: Scorer type for extractive strategy — "keyword" or "embedding".

    Returns:
        BaseContextCompressor instance.
    """
    if strategy == "none":
        return NoOpContextCompressor()
    elif strategy == "extractive":
        scorer = get_relevance_scorer(scoring)
        return ExtractiveContextCompressor(scorer=scorer)
    elif strategy == "llm":
        return LLMContextCompressor()
    logger.warning("Unknown compression strategy: %s, falling back to no-op", strategy)
    return NoOpContextCompressor()
