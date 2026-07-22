"""Chunking strategy abstraction.

Provides the Strategy Pattern for document chunking.
Strategies only decide chunk boundaries — no metadata enrichment.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Sequence

from langchain_core.documents import Document


@dataclass
class ChunkingMetrics:
    """Metrics from a chunking operation."""

    chunk_count: int = 0
    average_chunk_size: float = 0.0
    boundary_hits: int = 0
    strategy: str = "fixed"
    duration_ms: float = 0.0
    fallback_used: bool = False


@dataclass
class ChunkingResult:
    """Result of a chunking operation."""

    chunks: list[Document]
    success: bool = True
    metrics: ChunkingMetrics = field(default_factory=ChunkingMetrics)
