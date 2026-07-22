"""Chunking strategy abstraction.

Provides the Strategy Pattern for document chunking.
Strategies only decide chunk boundaries — no metadata enrichment.
"""
from __future__ import annotations

import time
from collections.abc import Sequence
from dataclasses import dataclass, field
from typing import Protocol

import re

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


@dataclass
class Boundary:
    """A candidate split point in text."""

    position: int  # character offset
    priority: int  # lower = higher priority
    label: str  # e.g., "heading", "paragraph", "sentence"


class BoundaryRule(Protocol):
    """Protocol for boundary detection rules.

    Rules MUST NOT modify text. They only identify candidate boundaries.
    """

    def detect(self, document: Document) -> list[Boundary]: ...


class HeadingRule:
    """Detects markdown headings and standalone ALL CAPS lines."""

    _MD_HEADING = re.compile(r"^(#{1,6})\s+.+$", re.MULTILINE)
    _CAPS_LINE = re.compile(r"^[A-Z][A-Z0-9\s]{2,}$", re.MULTILINE)

    def detect(self, document: Document) -> list[Boundary]:
        text = document.page_content
        boundaries: list[Boundary] = []
        for match in self._MD_HEADING.finditer(text):
            boundaries.append(Boundary(position=match.start(), priority=1, label="heading"))
        for match in self._CAPS_LINE.finditer(text):
            boundaries.append(Boundary(position=match.start(), priority=1, label="heading"))
        return boundaries


class NumberedSectionRule:
    """Detects numbered sections like '1. Introduction' or '2) Methods'."""

    _PATTERN = re.compile(r"^\d+[\.\)]\s+", re.MULTILINE)

    def detect(self, document: Document) -> list[Boundary]:
        boundaries: list[Boundary] = []
        for match in self._PATTERN.finditer(document.page_content):
            boundaries.append(Boundary(position=match.start(), priority=2, label="numbered_section"))
        return boundaries


class ParagraphRule:
    """Detects paragraph boundaries (double newlines)."""

    def detect(self, document: Document) -> list[Boundary]:
        boundaries: list[Boundary] = []
        text = document.page_content
        idx = 0
        while True:
            pos = text.find("\n\n", idx)
            if pos == -1:
                break
            boundaries.append(Boundary(position=pos, priority=3, label="paragraph"))
            idx = pos + 2
        return boundaries


class ListRule:
    """Detects bullet list items."""

    _PATTERN = re.compile(r"^[\-\*•]\s+", re.MULTILINE)

    def detect(self, document: Document) -> list[Boundary]:
        boundaries: list[Boundary] = []
        for match in self._PATTERN.finditer(document.page_content):
            boundaries.append(Boundary(position=match.start(), priority=4, label="list"))
        return boundaries


class SentenceRule:
    """Detects sentence boundaries (period/question/exclamation followed by space and capital)."""

    _PATTERN = re.compile(r"[.!?]\s+[A-Z]")

    def detect(self, document: Document) -> list[Boundary]:
        boundaries: list[Boundary] = []
        for match in self._PATTERN.finditer(document.page_content):
            boundaries.append(Boundary(position=match.end() - 1, priority=5, label="sentence"))
        return boundaries
