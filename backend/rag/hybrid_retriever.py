"""BM25 index management utilities.

This module provides functions to rebuild, refresh, and invalidate the BM25 index.
The actual hybrid retrieval logic is now in retrieval_strategy.py.
"""

from __future__ import annotations

import logging
from typing import Any

from backend.rag.bm25 import rebuild as bm25_rebuild, refresh as bm25_refresh, invalidate as bm25_invalidate, get_stats as bm25_get_stats

logger = logging.getLogger(__name__)


def rebuild_bm25_index(documents: list) -> None:
    """Rebuild the BM25 index with the given documents."""
    bm25_rebuild(documents)


def refresh_bm25_index() -> None:
    """Refresh the BM25 index from the vector store."""
    bm25_refresh()


def invalidate_bm25_index() -> None:
    """Invalidate the BM25 index."""
    bm25_invalidate()


def get_bm25_stats() -> dict[str, Any]:
    """Get BM25 index statistics."""
    return bm25_get_stats()