"""Chunking strategy abstraction.

Provides the Strategy Pattern for document chunking.
Strategies only decide chunk boundaries — no metadata enrichment.
"""
from __future__ import annotations

import time
from collections.abc import Sequence
from dataclasses import dataclass, field
from typing import Protocol

from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter

from backend.rag.splitter import SEPARATORS


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


class BaseChunkingStrategy(Protocol):
    """Protocol for chunking strategies.

    Strategies only decide chunk boundaries.
    They do not assign chunk IDs, generate parent references, or update metadata.
    Output must be deterministic: same input + config = identical output.
    """

    def split(self, documents: Sequence[Document]) -> ChunkingResult: ...


class FixedChunkingStrategy:
    """Wraps RecursiveCharacterTextSplitter as a BaseChunkingStrategy.

    Behavior identical to the existing text_splitter and parent_text_splitter.
    """

    def __init__(self, chunk_size: int, chunk_overlap: int):
        self._splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            add_start_index=True,
            separators=SEPARATORS,
        )

    def split(self, documents: Sequence[Document]) -> ChunkingResult:
        start = time.perf_counter()
        chunks = self._splitter.split_documents(list(documents))
        duration_ms = (time.perf_counter() - start) * 1000

        sizes = [len(c.page_content) for c in chunks]
        metrics = ChunkingMetrics(
            chunk_count=len(chunks),
            average_chunk_size=sum(sizes) / len(sizes) if sizes else 0.0,
            boundary_hits=0,
            strategy="fixed",
            duration_ms=duration_ms,
        )
        return ChunkingResult(chunks=chunks, success=True, metrics=metrics)
