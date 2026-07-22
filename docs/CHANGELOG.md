# CHANGELOG.md

# Agentic RAG Platform — Version History

## Milestone 5 — User Experience (Current)

Delivered: [Current]

### Added

- Settings infrastructure: `SettingsContext` + `settingsService` (localStorage persistence)
- Settings UI panels: General (confirm-before-delete toggle), Retrieval (show-citations toggle), About (version + reset)
- Conversation management: `ConversationContext` with message state, reset with confirmation dialog
- ConversationHeader component: message count, new chat button
- CitationViewModel: per-message citation UI state (expand/collapse, clipboard feedback)
- `citationUtils`: pure functions for deduplication and grouping
- `CitationCard`: expand/collapse behavior, clipboard copy with feedback
- Dark mode support via Tailwind `dark:` media query variant
- UploadCard animations: drag states, progress transitions, error/success animations
- Stream performance tracking (`StreamPerformanceTracker`)
- Conversation summary header in chat interface

### Changed

- Citation display: redesigned from flat list to grouped, expandable cards with document headers
- Chat streaming: stable scroll behavior, partial token edge cases handled
- ChatWindow: optimized with `useCallback`, `useMemo`, and `React.memo`
- Copy handler pattern extracted to shared callback
- Toast notifications: styled for dark mode, improved layout
- Backend end-to-end tests pass reliably

### Removed

- Empty `hooks/` directory (logic moved to contexts)
- Unused imports across ChatWindow, Message, CitationCard, and Shell components
- `useScrollToBottom` hook (consolidated into ChatWindow)

### Fixed

- Citation deduplication: identical citations no longer appear as separate cards
- Streaming UI: no partial tokens displayed after stream completes
- Upload edge cases: blank PDF rejection, corrupted PDF detection, duplicate detection
- Stale closure in streaming callbacks via `useRef`

---

## Milestone 4 — Agent Foundations

Delivered: Prior

### Added

- `ToolExecutor`: multi-iteration orchestration loop with `ConversationState`
- `tool_registry.py`: centralized tool registration with `tools/` package
- `tools/retrieve_context.py` — delegates to Retriever
- `tools/list_documents.py` — delegates to Document Service
- `tools/search_by_filename.py` — delegates to Document Service
- `ToolExecutionResult` and `ToolCall` data models
- Streaming tool events via `agent.stream_events()`
- Configurable safety limits: `MAX_TOOL_ITERATIONS`, `MAX_TOOLS_PER_RESPONSE`
- Graceful error handling: unknown tools, tool exceptions, iteration limits

### Changed

- Agent architecture: from monolithic `agent.py` to `agent.py` (entry points) + `tool_executor.py` (orchestration)
- LangChain tool binding: `bind_tools()` for native LLM tool selection
- Backward-compatible: `agent.invoke()` and `agent.stream_events()` unchanged

### Fixed

- Tool execution status reported correctly in streaming responses

---

## Milestone 3 — Retrieval Intelligence

Delivered: Prior

### Added

- Hybrid Search: Dense (vector) + BM25 (lexical) with Reciprocal Rank Fusion (RRF)
- Retrieval Strategy Pattern: `SimilarityStrategy`, `MMRStrategy`, `HybridStrategy`
- Cross-Encoder Reranking: local HF model (`cross-encoder/ms-marco-MiniLM-L-6-v2`)
- Query Rewriting: LLM-based with heuristic skip for already-specific queries
- `retrieval_strategies.py`: Strategy Pattern for retrieval algorithms
- `bm25.py`: in-memory BM25 index with thread-safe rebuild/refresh
- `reranker.py`: `BaseReranker` protocol, `CrossEncoderReranker`, `NoOpReranker`
- `query_rewriter.py`: `BaseQueryRewriter` protocol, `LLMQueryRewriter`, `NoOpQueryRewriter`
- Offline retrieval evaluation framework: `Precision@K`, `Recall@K`, `MRR`, `NDCG`, `MAP`, `F1`, `Hit Rate`
- CLI evaluation tool: `python -m backend.evaluation.cli`
- `RetrievalConfig`: centralized retrieval parameters with defaults
- `RetrievalResult.retrieval_metadata`: strategy, counts, latency info
- Provider abstraction layer: `backend/providers/` package (`embeddings.py`, `llm.py`)
- Provider registry pattern for extensibility
- `prompts.py`: structured prompt builder with deduplication, truncation, grounding rules
- Retrieval Metadata for debugging and evaluation

### Changed

- Prompt construction: from LangChain middleware to dedicated `prompts.py` with structured sections
- Embeddings/LLM: from direct instantiation to provider factory functions
- `RetrievalResult`: now includes `retrieval_query` (rewritten) and `original_query`

### Fixed

- Duplicate chunks in retrieved context (deduplication in Prompt Builder)
- Context length management (truncation from end within character budget)

---

## Milestone 2 — Frontend Foundation

Delivered: Prior

### Added

- React + TypeScript + Vite + Tailwind CSS application
- Drag-and-drop PDF upload with validation
- Document list with delete workflow
- Streaming chat interface with markdown rendering
- Source citation cards
- Responsive layout with sidebar navigation
- Keyboard shortcuts and ARIA accessibility
- Error handling and loading states

---

## Milestone 1 — Backend Foundation

Delivered: Prior

### Added

- FastAPI application with modular architecture
- PDF upload, validation, and storage
- Text extraction, chunking, and embedding pipeline
- ChromaDB vector store with persistent storage
- Similarity search and MMR retrieval
- Chat and streaming chat endpoints
- Source citation generation
- Document management (list, delete)
- Standardized error format and handlers
- Backend documentation

---

# Upcoming

## Milestone 6 — Advanced Agentic RAG

### Sprint 6.1 — Multi-Query Retrieval Pipeline

Delivered: [Current]

#### Added

- **Composable Retrieval Pipeline**: `retrieval_pipeline.py` with configurable stages (RewriteStage, ExpansionStage, RetrievalStage, MergeStage, RerankStage, ResultBuilderStage)
- **Query Expansion**: `query_expander.py` with `BaseQueryExpander` protocol, `LLMQueryExpander` (generates N diverse queries), `NoOpQueryExpander`, factory `get_query_expander()`
- **Parallel Retrieval Executor**: `retrieval_executor.py` with `execute_parallel()` (ThreadPoolExecutor), `execute_sequential()`, configurable `max_workers`
- **QueryProcessingConfig**: Nested config for `rewrite_enabled`, `rewrite_strategy`, `expand_enabled`, `expand_strategy`, `expand_count` with backward-compatible properties
- **Pipeline Trace Metadata**: Each stage records execution details in `retrieval_metadata["pipeline"]` as an execution trace array

#### Changed

- `retriever.py`: Routes to `RetrievalPipeline` when `expand_enabled=True`, else uses legacy `_single_query_retrieve()` for backward compatibility
- `retrieval_config.py`: Extended with `QueryProcessingConfig` dataclass, backward-compat properties for `query_rewrite`, `query_rewriting_enabled`, `multi_query_enabled`, `multi_query_count`, `query_expansion_strategy`
- `retrieve_context` tool patching: Tests now patch `get_query_rewriter` instead of `rewrite_query` (internal implementation change)

#### Added (Tests)

- `test_query_expander.py`: NoOp, LLM, factory, parsing, failure modes
- `test_retrieval_executor.py`: Parallel/sequential execution, error handling, empty queries
- `test_retrieval_pipeline.py`: Per-stage unit tests (Rewrite, Expansion, Retrieval, Merge, Rerank, ResultBuilder), full pipeline integration, dependency injection validation

### Sprint 6.2 — Parent Document Retrieval

Delivered: [Current]

#### Added

- **BaseParentStore + FileParentStore**: `storage/parent_store.py` — abstract parent storage protocol + JSON-backed implementation with LRU cache
- **HierarchicalSplitter**: `rag/splitter.py` — two-stage splitter (parent → child) with `HierarchicalSplitResult` dataclass
- **ParentRetrievalStage**: `rag/retrieval_pipeline.py` — resolves child chunks to parent blocks, injected between MergeStage and RerankStage
- **resolve_parents()**: `rag/parent_retrieval.py` — child-to-parent mapping with dedup (max score per parent), fallback when parent missing
- **Parent retrieval metadata**: `get_parent_retrieval_metadata()` reports child_chunks_found, unique_parents, merged_children, average_children_per_parent
- **RetrievalConfig.parent_retrieval_enabled**: Toggle (default True), wired into pipeline execution
- **Flat metadata support**: Child chunks store parent reference as flat fields (`parent_id`, `parent_page_range_start`, `parent_page_range_end`, `parent_child_index`) for ChromaDB compatibility

#### Changed

- `document_service.py`: Uses `HierarchicalSplitter` during indexing, stores parent blocks via `FileParentStore`, cleans up on rollback
- `RerankStage`: Reranks `context.parent_chunks` when `parent_retrieval_enabled=True`, else `context.merged_chunks` (backward compatible)
- `retriever.py`: Single-query path injects parent retrieval after reranking when enabled

#### Added (Tests)

- `test_parent_retrieval.py`: 39 tests covering store (9), splitter (5), resolver (10), metadata (3), stage (5), pipeline integration (7)

### Sprint 6.3 — Context Compression (Current)

#### Added

- **Context Compression Stage**: `rag/retrieval_pipeline.py` — `ContextCompressionStage` inserted after `RerankStage`, compresses working chunks before prompt construction
- **context_compression.py**: `BaseContextCompressor` protocol with `NoOpContextCompressor`, `ExtractiveContextCompressor` (sentence-level extraction via scorer), `LLMContextCompressor` (provider-backed, lazy initialization)
- **BaseRelevanceScorer**: Generic scorer protocol with `KeywordScorer` (default, lightweight keyword overlap) and `EmbeddingScorer` (optional, provider-backed cosine similarity)
- **StageResult dataclass**: Pipeline stage return type `{chunks, trace}` enabling immutable chunk flow
- **working_chunks refactor**: `PipelineContext` consolidated to single `working_chunks` field (removed `merged_chunks`, `parent_chunks`, `reranked_chunks`, `final_chunks`)
- **RetrievalConfig compression fields**: `compression_strategy` ("none" | "extractive" | "llm"), `compression_scoring` ("keyword" | "embedding"), `compression_target_ratio`, `compression_max_tokens`
- **Expanded compression metrics**: `original_tokens`, `compressed_tokens`, `tokens_saved`, `compression_ratio`, `characters_saved`, `latency_ms`, `scorer`
- **`_single_query_retrieve`**: Refactored to thin compatibility wrapper around `RetrievalPipeline`
- **Immutable stage semantics**: Each stage returns new `StageResult` with new chunk list; pipeline updates `working_chunks` reference

#### Changed

- `retrieval_pipeline.py`: All stages refactored to return `StageResult`; `PipelineContext` simplified to `working_chunks`; `ContextCompressionStage` inserted after `RerankStage`; `ResultBuilderStage` includes compression in pipeline summary
- `PipelineContext`: Removed `merged_chunks`, `parent_chunks`, `reranked_chunks`, `final_chunks` — replaced by single `working_chunks` field updated by pipeline from `StageResult.chunks`
- Pipeline order: `Rewrite → Expansion → Retrieval → Merge → ParentRetrieval → Rerank → ContextCompression → ResultBuilder`
- `retriever.py`: `_single_query_retrieve` delegates to `create_pipeline_from_config` with `expand_enabled=False`
- `retrieval_config.py`: Added `compression_strategy`, `compression_scoring`, `compression_target_ratio`, `compression_max_tokens` fields

#### Added (Tests)

- `test_context_compression.py`: 30 tests covering NoOp, KeywordScorer, EmbeddingScorer, ExtractiveCompressor, LLMCompressor, factory functions, compression stage, pipeline integration, metadata preservation, failure fallback

### Planned (Sprint 6.4+)

- **New tools**: summarize_document, search_by_metadata
- **Agent improvements**: Reflection, planning, multi-step reasoning, reasoning traces
- **Retrieval**: Adaptive chunking
- **Infrastructure**: Multiple LLM/embedding providers, conversation memory, agent observability

## Milestone 7 — Multimodal Intelligence

Planned capabilities for visual document understanding:

- Image extraction, OCR, table/chart/figure understanding
- Multimodal prompt construction with vision context
- Visual reasoning and citations
- Vision provider abstraction and unified multimodal retrieval

## Milestone 8 — Web Search & External Knowledge

Planned capabilities for external knowledge integration:

- web_search tool with search provider abstraction
- Intelligent fallback from local retrieval to web search
- Document + Web answer synthesis with source attribution
- Confidence-aware tool selection and freshness-aware answers

## Milestone 9 — GraphRAG & Internal Knowledge Engine

Planned capabilities for relationship-aware knowledge retrieval:

- Knowledge graph generation from document corpus
- Hybrid vector + graph retrieval
- Internal wiki generation
- Graph-based reasoning across documents
- Relationship-aware retrieval via entity and relationship lookup
