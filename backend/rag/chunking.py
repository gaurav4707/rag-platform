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


class BoundaryDetector:
    """Runs boundary rules and merges/deduplicates results.

    Boundaries are sorted by position. At the same position, the
    lowest priority value (highest priority) wins.
    """

    def __init__(self, rules: list[BoundaryRule] | None = None):
        self._rules: list[BoundaryRule] = rules if rules is not None else [
            HeadingRule(), NumberedSectionRule(), ParagraphRule(),
            ListRule(), SentenceRule(),
        ]

    def detect(self, document: Document) -> list[Boundary]:
        all_boundaries: list[Boundary] = []
        for rule in self._rules:
            all_boundaries.extend(rule.detect(document))

        # Sort by position, then by priority (lower = higher priority)
        all_boundaries.sort(key=lambda b: (b.position, b.priority))

        # Deduplicate: keep lowest priority at each position
        deduplicated: list[Boundary] = []
        for b in all_boundaries:
            if deduplicated and deduplicated[-1].position == b.position:
                continue  # same position, keep the earlier (lower priority value)
            deduplicated.append(b)

        return deduplicated


class ChunkAssembler:
    """Builds chunks from boundary positions.

    Invariant: Every output chunk is an exact substring of the original input.
    ChunkAssembler never invents content.
    """

    def __init__(self, min_size: int, max_size: int):
        self._min_size = min_size
        self._max_size = max_size

    def assemble(self, text: str, boundaries: list[Boundary]) -> list[Document]:
        if not boundaries:
            return [Document(page_content=text, metadata={"start_index": 0})]

        # Build split points: start of text + boundary positions + end of text
        split_points = [0] + [b.position for b in boundaries] + [len(text)]

        # Build initial chunks from split points
        raw_chunks: list[str] = []
        for i in range(len(split_points) - 1):
            start, end = split_points[i], split_points[i + 1]
            chunk_text = text[start:end].strip()
            if chunk_text:
                raw_chunks.append(chunk_text)

        if not raw_chunks:
            return [Document(page_content=text, metadata={"start_index": 0})]

        # Merge small chunks
        merged: list[str] = [raw_chunks[0]]
        for chunk_text in raw_chunks[1:]:
            if len(merged[-1]) < self._min_size:
                merged[-1] = merged[-1] + "\n\n" + chunk_text
            else:
                merged.append(chunk_text)

        # Split large chunks (at the last newline or space within max_size)
        final_chunks: list[str] = []
        for chunk_text in merged:
            if len(chunk_text) <= self._max_size:
                final_chunks.append(chunk_text)
            else:
                # Find a good split point within max_size
                split_at = chunk_text.rfind("\n\n", 0, self._max_size)
                if split_at == -1:
                    split_at = chunk_text.rfind(". ", 0, self._max_size)
                if split_at == -1:
                    split_at = chunk_text.rfind(" ", 0, self._max_size)
                if split_at <= 0:
                    split_at = self._max_size
                else:
                    split_at += 1  # include the separator
                final_chunks.append(chunk_text[:split_at].strip())
                remaining = chunk_text[split_at:].strip()
                if remaining:
                    final_chunks.append(remaining)

        # Compute start_index for each chunk
        result: list[Document] = []
        search_start = 0
        for chunk_text in final_chunks:
            pos = text.find(chunk_text, search_start)
            if pos == -1:
                pos = search_start
            result.append(Document(page_content=chunk_text, metadata={"start_index": pos}))
            search_start = pos + len(chunk_text)

        return result
