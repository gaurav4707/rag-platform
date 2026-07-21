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

Planned capabilities focusing on Agent intelligence and autonomy:

- **New tools**: summarize_document, search_by_metadata
- **Agent improvements**: Reflection, planning, multi-step reasoning, reasoning traces
- **Retrieval**: Multi-query retrieval, parent document retrieval, context compression, adaptive chunking
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
