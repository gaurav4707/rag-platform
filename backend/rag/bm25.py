"""BM25 lexical retrieval implementation using rank-bm25.

Provides keyword-based retrieval to complement dense vector search.
Index is kept in-memory only; ChromaDB is the single source of truth.
"""

from __future__ import annotations

import logging
import threading
from typing import Any

from langchain_core.documents import Document
from rank_bm25 import BM25Okapi

from backend.models.rag_models import RetrievedChunk

logger = logging.getLogger(__name__)

_bm25_index: BM25Okapi | None = None
_corpus: list[Document] = []
_tokenized_corpus: list[list[str]] = []
_index_lock = threading.RLock()
_initialized = False


def _tokenize(text: str) -> list[str]:
    """Simple whitespace tokenizer for BM25.

    Args:
        text: Input text to tokenize

    Returns:
        List of lowercase tokens
    """
    return text.lower().split()


def _build_index(documents: list[Document]) -> None:
    """Build BM25 index from documents.

    Args:
        documents: List of LangChain Documents
    """
    global _bm25_index, _corpus, _tokenized_corpus, _initialized

    with _index_lock:
        _corpus = documents
        _tokenized_corpus = [_tokenize(doc.page_content) for doc in documents]

        if _tokenized_corpus:
            _bm25_index = BM25Okapi(_tokenized_corpus)
            _initialized = True
            logger.info("BM25 index built with %d documents", len(documents))
        else:
            _bm25_index = None
            _initialized = False
            logger.info("BM25 index cleared (no documents)")


def rebuild(documents: list[Document]) -> None:
    """Rebuild the BM25 index from scratch.

    Args:
        documents: List of all documents to index
    """
    _build_index(documents)


def refresh() -> None:
    """Refresh the BM25 index from the vector store."""
    from backend.rag.vector_store import get_all_documents

    try:
        docs = get_all_documents()
        _build_index(docs)
    except Exception as e:
        logger.warning("Failed to refresh BM25 index: %s", e)


def invalidate() -> None:
    """Invalidate the BM25 index."""
    global _bm25_index, _corpus, _tokenized_corpus, _initialized

    with _index_lock:
        _bm25_index = None
        _corpus = []
        _tokenized_corpus = []
        _initialized = False

    logger.info("BM25 index invalidated")


def search(query: str, k: int = 10) -> list[RetrievedChunk]:
    """Search the BM25 index for relevant chunks.

    Args:
        query: Search query string
        k: Number of results to return

    Returns:
        List of RetrievedChunk objects ranked by BM25 score
    """
    if not query or not query.strip():
        logger.debug("BM25 search: empty query")
        return []

    with _index_lock:
        if not _initialized or _bm25_index is None or not _corpus:
            logger.debug("BM25 search: index not available")
            return []

        try:
            tokenized_query = _tokenize(query)
            scores = _bm25_index.get_scores(tokenized_query)

            top_indices = sorted(
                range(len(scores)),
                key=lambda i: scores[i],
                reverse=True,
            )[:k]

            results = []
            for idx in top_indices:
                if scores[idx] > 0:
                    chunk = RetrievedChunk(
                        document=_corpus[idx],
                        score=float(scores[idx]),
                    )
                    results.append(chunk)

            logger.debug("BM25 search returned %d results for query: %s", len(results), query[:50])
            return results

        except Exception as e:
            logger.warning("BM25 search failed: %s", e)
            return []


def get_stats() -> dict[str, Any]:
    """Get BM25 index statistics.

    Returns:
        Dictionary with index statistics
    """
    with _index_lock:
        return {
            "initialized": _initialized,
            "document_count": len(_corpus),
            "index_ready": _bm25_index is not None,
        }