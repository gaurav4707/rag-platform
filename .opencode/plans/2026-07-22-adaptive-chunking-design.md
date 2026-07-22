# Sprint 6.4 — Adaptive Chunking Design Spec

**Date**: 2026-07-22
**Status**: Approved
**Sprint**: 6.4

---

## 1. Objective

Replace fixed-size child chunk generation in the indexing pipeline with an adaptive chunking strategy that respects structural document boundaries (headings, paragraphs, lists, sentences) while preserving the existing metadata contract and providing a clean extensibility path for future chunking strategies.

---

## 2. Scope

**In scope**:
- Chunking strategy abstraction (`BaseChunkingStrategy`)
- `FixedChunkingStrategy` (wraps existing behavior)
- `AdaptiveChunkingStrategy` with boundary detection rules
- `ChunkingPipeline` with fallback orchestration
- `ChunkingResult` and `ChunkingMetrics` typed models
- `BoundaryDetector` + `ChunkAssembler` separation
- `IndexingConfig` for indexing-time configuration
- Parent strategy abstraction (fixed for MVP)
- HierarchicalSplitter refactor to delegate to strategies
- Page scope only (MVP)

**Out of scope**:
- Document scope (future milestone)
- Semantic chunking, Markdown-aware, code-aware, table-aware strategies (future)
- Retrieval pipeline changes
- Prompt Builder changes
- Citation Builder changes
- Agent changes
- Frontend changes

---

## 3. Architecture

### 3.1 Component Diagram

```
IndexingConfig
├── chunking_strategy: "fixed" | "adaptive"
├── chunking_scope: "page" | "document"
├── adaptive_min_chunk_size: 200
└── adaptive_max_chunk_size: 1500

BaseChunkingStrategy (Protocol)
├── FixedChunkingStrategy
└── AdaptiveChunkingStrategy
        ├── BoundaryDetector
        │     ├── HeadingRule
        │     ├── NumberedSectionRule
        │     ├── ParagraphRule
        │     ├── ListRule
        │     └── SentenceRule
        └── ChunkAssembler

ChunkingPipeline
├── primary: BaseChunkingStrategy
├── fallback: BaseChunkingStrategy
└── execute(documents) -> ChunkingResult

ChunkingResult
├── chunks: list[Document]
├── adaptive_success: bool
└── metrics: ChunkingMetrics

ChunkingMetrics (dataclass)
├── chunk_count: int
├── average_chunk_size: float
├── boundary_hits: int
├── strategy: str
└── duration_ms: float

HierarchicalSplitter
├── parent_strategy: BaseChunkingStrategy (fixed for MVP)
├── child_pipeline: ChunkingPipeline
├── scope: "page" | "document"
└── split(page_docs) -> HierarchicalSplitResult
```

### 3.2 Data Flow — Indexing

```
PDF
  ↓
Loader → list[Document] (one per page)
  ↓
Metadata Enrichment (document_id, filename, file_hash)
  ↓
HierarchicalSplitter
  ├── Scope: page (MVP) — processes one page at a time
  │         document (future) — merges pages first
  ├── Parent Strategy: FixedChunkingStrategy (always)
  │     → parent_blocks (4000 chars)
  ├── Child Pipeline: ChunkingPipeline
  │     ├── Primary: AdaptiveChunkingStrategy
  │     │     ├── BoundaryDetector → candidate boundaries
  │     │     └── ChunkAssembler → child chunks
  │     └── Fallback: FixedChunkingStrategy (1000 chars)
  └── Metadata Enrichment (parent_id, chunk_index, etc.)
  ↓
HierarchicalSplitResult
  ├── parent_blocks → ParentStore (JSON)
  └── child_chunks → Vector Store (ChromaDB)
```

### 3.3 Invariant

**Adaptive Chunking changes only chunk boundaries, never document semantics or metadata.**

Every chunk continues to carry: `document_id`, `filename`, `file_hash`, `parent_id`, `parent_page_range_start`, `parent_page_range_end`, `parent_child_index`, `chunk_index`.

---

## 4. Module Specifications

### 4.1 `backend/rag/chunking.py`

New file containing all chunking abstractions.

#### `BaseChunkingStrategy` (Protocol)

```python
from typing import Protocol, Sequence
from langchain_core.documents import Document

class BaseChunkingStrategy(Protocol):
    def split(self, documents: Sequence[Document]) -> ChunkingResult: ...
```

- Accepts `Sequence[Document]` (not `list`) for flexibility.
- Returns `ChunkingResult` (not raw list).
- Strategies **only decide chunk boundaries** — no chunk IDs, no parent references, no metadata enrichment.
- Output must be deterministic: same input + config = same output.

#### `FixedChunkingStrategy`

```python
class FixedChunkingStrategy:
    def __init__(self, chunk_size: int, chunk_overlap: int): ...
    def split(self, documents: Sequence[Document]) -> ChunkingResult: ...
```

- Wraps `RecursiveCharacterTextSplitter` with existing `SEPARATORS`.
- Behavior identical to current `text_splitter` and `parent_text_splitter`.
- Always reports `strategy="fixed"`.

#### `AdaptiveChunkingStrategy`

```python
class AdaptiveChunkingStrategy:
    def __init__(
        self,
        min_chunk_size: int,
        max_chunk_size: int,
        detector: BoundaryDetector | None = None,
        assembler: ChunkAssembler | None = None,
    ): ...
    def split(self, documents: Sequence[Document]) -> ChunkingResult: ...
```

- Uses `BoundaryDetector` to find candidate split points.
- Uses `ChunkAssembler` to build chunks from boundaries.
- If no useful boundaries are found, returns `ChunkingResult(adaptive_success=False)`.
- Does **not** inject or construct a fallback — that is the pipeline's responsibility.

#### `ChunkingResult`

```python
@dataclass
class ChunkingResult:
    chunks: list[Document]
    adaptive_success: bool = True
    metrics: ChunkingMetrics = field(default_factory=ChunkingMetrics)
```

#### `ChunkingMetrics`

```python
@dataclass
class ChunkingMetrics:
    chunk_count: int = 0
    average_chunk_size: float = 0.0
    boundary_hits: int = 0
    strategy: str = "fixed"
    duration_ms: float = 0.0
```

#### `ChunkingPipeline`

```python
class ChunkingPipeline:
    def __init__(
        self,
        primary: BaseChunkingStrategy,
        fallback: BaseChunkingStrategy | None = None,
    ): ...
    def execute(self, documents: Sequence[Document]) -> ChunkingResult: ...
```

- Tries `primary` first.
- If `primary` returns `adaptive_success=False` and `fallback` is provided, executes `fallback`.
- Returns `ChunkingResult` from whichever strategy succeeded.
- If both fail (should not happen with `FixedChunkingStrategy` fallback), returns empty result with error metrics.

### 4.2 `BoundaryDetector`

```python
@dataclass
class Boundary:
    position: int      # character offset
    priority: int      # lower = higher priority
    label: str         # e.g., "heading", "paragraph", "sentence"

class BoundaryDetector:
    def __init__(self, rules: list[BoundaryRule] | None = None): ...
    def detect(self, text: str) -> list[Boundary]: ...
```

- Runs all rules, merges results, sorts by position.
- Deduplicates boundaries at the same position (keeps highest priority).

#### `BoundaryRule` (Protocol)

```python
class BoundaryRule(Protocol):
    def detect(self, text: str) -> list[Boundary]: ...
```

#### Rule implementations

| Rule | Pattern | Priority |
|------|---------|----------|
| `HeadingRule` | `^#{1,6}\s+.+$` (markdown), standalone caps lines | 1 |
| `NumberedSectionRule` | `^\d+\.\s+` | 2 |
| `ParagraphRule` | `\n\n` | 3 |
| `ListRule` | `^[\-\*•]\s+` | 4 |
| `SentenceRule` | `[.!?]\s+` | 5 |

All rules operate on plain text via regex. No LLM calls. Linear with document size.

### 4.3 `ChunkAssembler`

```python
class ChunkAssembler:
    def __init__(self, min_size: int, max_size: int): ...
    def assemble(
        self, text: str, boundaries: list[Boundary]
    ) -> list[Document]: ...
```

- Builds chunks from boundary positions.
- Merges consecutive small boundaries until `min_size` is reached.
- Splits at the next boundary when `max_size` is exceeded.
- If no boundaries exist, returns the entire text as one chunk (caller decides if this is a problem).

### 4.4 `backend/rag/splitter.py` (Modified)

```python
class HierarchicalSplitter:
    def __init__(
        self,
        parent_strategy: BaseChunkingStrategy | None = None,
        child_pipeline: ChunkingPipeline | None = None,
        scope: str = "page",
        document_id: str = "",
        filename: str = "",
        file_hash: str = "",
    ): ...
    def split(self, page_docs: list[Document]) -> HierarchicalSplitResult: ...
```

Key changes:
- `parent_strategy` defaults to `FixedChunkingStrategy(PARENT_CHUNK_SIZE, PARENT_CHUNK_OVERLAP)`.
- `child_pipeline` defaults to constructing `ChunkingPipeline` with configured strategy.
- `scope` parameter (unused in MVP beyond storage in metadata).
- Metadata enrichment (parent_id, document_id, chunk_index, etc.) stays here — unchanged.
- Module-level `text_splitter` and `parent_text_splitter` instances stay for backward compatibility with tests.

### 4.5 `backend/config.py` (Modified)

```python
# Chunking
CHUNKING_STRATEGY = "fixed"        # "fixed" | "adaptive"
CHUNKING_SCOPE = "page"            # "page" | "document" (document is future)
ADAPTIVE_MIN_CHUNK_SIZE = 200
ADAPTIVE_MAX_CHUNK_SIZE = 1500
```

Defaults preserve current behavior: `CHUNKING_STRATEGY = "fixed"` means no adaptive chunking unless explicitly enabled.

### 4.6 `backend/services/document_service.py` (Modified)

- Reads `CHUNKING_STRATEGY`, `CHUNKING_SCOPE`, `ADAPTIVE_MIN_CHUNK_SIZE`, `ADAPTIVE_MAX_CHUNK_SIZE` from config.
- Constructs `IndexingConfig` and passes it to `HierarchicalSplitter`.

---

## 5. Configuration

### 5.1 `IndexingConfig` (new dataclass)

```python
@dataclass(frozen=True)
class IndexingConfig:
    chunking_strategy: str = "fixed"       # "fixed" | "adaptive"
    chunking_scope: str = "page"           # "page" | "document"
    adaptive_min_chunk_size: int = 200
    adaptive_max_chunk_size: int = 1500
    parent_chunk_size: int = 4000
    parent_chunk_overlap: int = 200
    child_chunk_size: int = 1000
    child_chunk_overlap: int = 200
```

Defined in `backend/rag/chunking.py` alongside the strategy abstractions.

### 5.2 Configuration Flow

```
config.py constants
  ↓
document_service.py reads constants
  ↓
Constructs IndexingConfig
  ↓
Passes to HierarchicalSplitter
  ↓
HierarchicalSplitter constructs strategies + pipeline
```

`RetrievalConfig` is **not modified** — chunking is an indexing-time concern.

---

## 6. Adaptive Heuristics

### 6.1 Boundary Detection Rules

Ordered by priority (lower number = higher priority):

| Priority | Rule | Pattern | Example |
|----------|------|---------|---------|
| 1 | `HeadingRule` | `^#{1,6}\s+.+$` | `## Installation` |
| 1 | `HeadingRule` | Standalone ALL CAPS line (>=3 chars, no period) | `INSTALLATION` |
| 2 | `NumberedSectionRule` | `^\d+[\.\)]\s+` | `1. Prerequisites` |
| 3 | `ParagraphRule` | `\n\n` | Double newline |
| 4 | `ListRule` | `^[\-\*•]\s+` | `- Step one` |
| 5 | `SentenceRule` | `[.!?]\s+[A-Z]` | `End of sentence. Next` |

### 6.2 Chunk Assembly Algorithm

```
1. Detect boundaries via BoundaryDetector
2. If no boundaries found → return adaptive_success=False
3. Build initial chunks from boundary positions
4. Merge chunks smaller than min_chunk_size with neighbor
5. Split chunks larger than max_chunk_size at next boundary
6. Return chunks with adaptive_success=True
```

The pipeline decides fallback based on `adaptive_success`, not by comparing outputs.

### 6.3 Fallback Decision

The `ChunkingPipeline` checks `ChunkingResult.adaptive_success`:
- `True` → use adaptive chunks
- `False` → execute fallback strategy, return its result

No output comparison. The strategy explicitly reports success.

---

## 7. Metadata Preservation

Every chunk produced by any strategy must carry:

| Field | Source |
|-------|--------|
| `document_id` | Set by `HierarchicalSplitter` |
| `filename` | Set by `HierarchicalSplitter` |
| `file_hash` | Set by `HierarchicalSplitter` |
| `parent_id` | Set by `HierarchicalSplitter` |
| `parent_page_range_start` | Set by `HierarchicalSplitter` |
| `parent_page_range_end` | Set by `HierarchicalSplitter` |
| `parent_child_index` | Set by `HierarchicalSplitter` |
| `chunk_index` | Set by `HierarchicalSplitter` |
| `start_index` | Set by strategy (character offset within parent) |
| `page` | Inherited from page Document |

Strategies do **not** set these fields. `HierarchicalSplitter` handles all metadata enrichment after chunks are produced.

---

## 8. Determinism

Given identical input documents and identical `IndexingConfig`:

```
input → strategy → identical output
```

This is guaranteed by:
- No randomness in any strategy
- No external state (no LLM calls, no network)
- Deterministic regex matching
- Deterministic boundary merging/assembly

---

## 9. Testing

### 9.1 New file: `backend/tests/test_chunking.py`

| Test Class | Tests |
|------------|-------|
| `TestFixedChunkingStrategy` | Same output as current text_splitter; handles empty input; respects chunk_size and overlap |
| `TestAdaptiveChunkingStrategy` | Heading preservation; paragraph preservation; list preservation; sentence preservation; fallback when no boundaries; min/max chunk size enforcement |
| `TestBoundaryDetector` | Heading detection; numbered section detection; paragraph detection; list detection; sentence detection; priority ordering; deduplication at same position |
| `TestChunkAssembler` | Merge small chunks; split large chunks; preserve boundaries; handle no boundaries |
| `TestChunkingPipeline` | Primary success; primary failure triggers fallback; both fail returns empty; metrics propagation |
| `TestHierarchicalSplitterIntegration` | Parent-child mapping preserved with adaptive; metadata propagation; chunk_index continuity; page metadata preserved |
| `TestIndexingConfig` | Defaults preserve backward compatibility; custom config propagation |
| `TestDeterminism` | Same input produces same output (run twice, compare) |

### 9.2 Existing test compatibility

- `test_parent_retrieval.py::TestHierarchicalSplitter` — continues passing (default config = fixed strategy)
- `test_retriever.py::TestChunkQuality` — continues passing (module-level `text_splitter` stays available)

---

## 10. Documentation Updates

| File | Change |
|------|--------|
| `ARCHITECTURE.md` | Add chunking strategy layer to module responsibilities; update indexing flow diagram |
| `RAG_PIPELINE.md` | Update Step 4 (Hierarchical Split) to reference strategy delegation |
| `DECISIONS.md` | New ADR for Adaptive Chunking decision |
| `CHANGELOG.md` | Sprint 6.4 entry |

---

## 11. Success Criteria

- [ ] `BaseChunkingStrategy` protocol defined
- [ ] `FixedChunkingStrategy` wraps existing behavior identically
- [ ] `AdaptiveChunkingStrategy` with BoundaryDetector + ChunkAssembler
- [ ] `ChunkingPipeline` orchestrates fallback
- [ ] `ChunkingResult` + `ChunkingMetrics` typed models
- [ ] `IndexingConfig` separate from `RetrievalConfig`
- [ ] `HierarchicalSplitter` delegates to strategies
- [ ] Parent strategy abstracted (fixed for MVP)
- [ ] All metadata preserved exactly
- [ ] Deterministic output guaranteed
- [ ] Config defaults preserve backward compatibility
- [ ] All existing tests pass
- [ ] New test suite covers all components
- [ ] Documentation updated
- [ ] No changes to retrieval, prompt, citation, agent, or frontend layers

---

## 12. Remaining Work for Sprint 6.5

- `summarize_document` tool implementation
- Document scope chunking (merge pages into continuous stream)
- SemanticChunkingStrategy (LLM-based boundary detection)
- MarkdownChunkingStrategy
- CodeChunkingStrategy
- TableAwareChunkingStrategy
