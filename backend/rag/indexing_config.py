"""Indexing pipeline configuration.

Separate from RetrievalConfig — chunking is an indexing-time concern.
"""
from dataclasses import dataclass


@dataclass(frozen=True)
class IndexingConfig:
    """Configuration for the indexing pipeline."""

    chunking_strategy: str = "fixed"  # "fixed" | "adaptive"
    chunking_scope: str = "page"  # "page" | "document" (document is future)
    adaptive_min_chunk_size: int = 200
    adaptive_max_chunk_size: int = 1500
    parent_chunk_size: int = 4000
    parent_chunk_overlap: int = 200
    child_chunk_size: int = 1000
    child_chunk_overlap: int = 200
