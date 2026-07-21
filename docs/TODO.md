# TODO.md

# Project Implementation Roadmap

## Purpose

This document tracks the implementation status of the project.

Unlike `PROJECT_PLAN.md`, which describes the long-term vision, this document reflects the current implementation state and active development priorities.

It should always remain synchronized with the codebase.

---

# Project Status

**Current Phase**

Milestone 6 — Advanced Agentic RAG (In Progress)

**Overall Progress**

```text
████████████████████ 83%
```

---

# Milestone Overview

| Milestone | Status |
|-----------|--------|
| 1. Backend Foundation | ✅ Completed |
| 2. Frontend Foundation | ✅ Completed |
| 3. Retrieval Intelligence | ✅ Completed |
| 4. Agent Foundations | ✅ Completed |
| 5. User Experience | ✅ Completed |
| 6. Advanced Agentic RAG | ⏳ In Progress |
| 7. Multimodal Intelligence | 📋 Planned |
| 8. Web Search & External Knowledge | 📋 Planned |
| 9. GraphRAG & Internal Knowledge Engine | 📋 Planned |

---

# Milestone 1 — Backend Foundation ✅

## Completed

### Project

- [x] Backend architecture
- [x] Configuration
- [x] Documentation

### FastAPI

- [x] Application setup
- [x] Routing
- [x] Health endpoint
- [x] Error handling

### Document Processing

- [x] PDF upload
- [x] Validation
- [x] PDF storage
- [x] Loader
- [x] Metadata enrichment
- [x] Chunking
- [x] Embeddings

### Vector Store

- [x] ChromaDB integration
- [x] Persistent storage
- [x] Similarity search
- [x] Delete documents
- [x] List documents

### Chat

- [x] Chat endpoint
- [x] Streaming endpoint
- [x] Source citations
- [x] Tool call metadata

### APIs

- [x] Upload
- [x] Chat
- [x] Streaming Chat
- [x] List Documents
- [x] Delete Documents

---

# Milestone 2 — Frontend Foundation ✅

## Completed

### Project Setup

- [x] React
- [x] TypeScript
- [x] Vite
- [x] Tailwind CSS

### Layout

- [x] Responsive layout
- [x] Sidebar
- [x] Header

### Upload

- [x] Drag-and-drop upload
- [x] File validation
- [x] Upload progress

### Documents

- [x] List documents
- [x] Delete documents
- [x] Loading states
- [x] Error states

### Chat

- [x] Streaming chat
- [x] Markdown rendering
- [x] Auto-scroll
- [x] Citation cards
- [x] Streaming cursor
- [x] Keyboard shortcuts

### Accessibility

- [x] Keyboard navigation
- [x] ARIA labels
- [x] Loading announcements
- [x] Focus management

---

# Milestone 3 — Retrieval Intelligence ✅

## Goal

Improve answer quality before expanding the Agent.

## Completed

### Retrieval

- [x] Hybrid Search (Dense + BM25 with Reciprocal Rank Fusion)
- [x] Maximum Marginal Relevance (MMR)
- [x] Metadata filtering
- [x] Query rewriting (LLM-based with heuristic skip)
- [x] Retrieval Strategy Pattern (Similarity, MMR, Hybrid)

### Ranking

- [x] Cross-encoder reranking (local HF model)
- [x] RetrievalConfig with centralized configuration
- [x] Retrieval Metadata for debugging/evaluation

### Prompting

- [x] Prompt optimization (structured sections, deduplication, truncation)
- [x] Context formatting with rich metadata
- [x] Better citation grounding

### Evaluation

- [x] Retrieval benchmarking (CLI-based offline evaluation)
- [x] Prompt evaluation
- [x] Retrieval inspection utilities
- [x] Metrics: Precision@K, Recall@K, Hit Rate, MRR, MAP, NDCG, F1

---

# Milestone 4 — Agent Foundations ✅

## Goal

Transform the current RAG pipeline into a robust Agentic RAG architecture.

### Agent

- [x] Stable agent implementation
- [x] Provider-independent agent layer (via provider abstraction)
- [x] Tool registry
- [x] Tool execution tracing
- [x] Streaming tool events
- [x] ToolExecutor multi-iteration orchestration loop
- [x] Configurable safety limits (MAX_TOOL_ITERATIONS, MAX_TOOLS_PER_RESPONSE)
- [x] Graceful error handling for tool failures

### Initial Tools

- [x] retrieve_context

### Additional Tools

- [x] list_documents
- [x] search_by_filename
- [ ] summarize_document
- [ ] search_by_metadata

### Infrastructure

- [x] Conversation state (ConversationState dataclass)
- [x] Debug logging
- [ ] Agent observability (tracing, metrics)

---

# Milestone 5 — User Experience ✅

## Goal

Polish the user experience with settings, conversation management, improved citations, and code cleanup.

### UI

- [x] Settings infrastructure (SettingsContext + settingsService + localStorage)
- [x] Settings panels (General, Retrieval, About)
- [x] Conversation management (ConversationContext, reset with confirmation)
- [x] Conversation summary header (message count, new chat button)
- [x] Richer citation cards (expand/collapse, clipboard copy, deduplication)
- [x] CitationViewModel for per-message citation UI state
- [x] citationUtils for deduplication and grouping
- [x] Streamlined streaming (scroll behavior, partial token handling)
- [x] UploadCard animations (drag states, progress, error transition)
- [x] Dark mode support via Tailwind `dark:` variant (OS preference)
- [x] Toast notification improvements (retry on connection lost)

### Code Quality

- [x] Dead code removal (empty hooks directory, unused imports)
- [x] Import cleanup across all components
- [x] React.memo usage for render optimization
- [x] ChatWindow optimization (useCallback, useMemo)
- [x] Copy handler pattern extraction to shared utils

### Accessibility (dark mode only, partial)

- [x] Tailwind dark mode classes present (OS-level)
- [ ] Full accessibility audit (deferred)
- [ ] Keyboard navigation improvements (deferred)
- [ ] Screen reader testing (deferred)

---

# Milestone 6 — Advanced Agentic RAG

## Retrieval

- [ ] Parent document retrieval
- [ ] Context compression
- [ ] Adaptive chunking
- [ ] Multi-query retrieval

## Agent

- [ ] Reflection
- [ ] Planning
- [ ] Multi-step reasoning
- [ ] Reasoning traces
- [ ] Agent observability (tracing, metrics)

## Tools

- [ ] summarize_document
- [ ] search_by_metadata

## Infrastructure

- [ ] Multiple LLM providers
- [ ] Multiple embedding providers
- [ ] Multiple vector databases
- [ ] Conversation memory (SQLite)
- [ ] Background indexing
- [ ] Monitoring

---

# Milestone 7 — Multimodal Intelligence

## Retrieval

- [ ] Image extraction from PDFs
- [ ] OCR for scanned PDFs
- [ ] Table understanding
- [ ] Chart understanding
- [ ] Figure understanding

## Prompting

- [ ] Multimodal prompt construction
- [ ] Vision context formatting

## Agent

- [ ] Visual reasoning
- [ ] Visual citations (image sources with page references)

## Infrastructure

- [ ] Vision provider abstraction
- [ ] Unified multimodal retrieval

---

# Milestone 8 — Web Search & External Knowledge

## Tools

- [ ] web_search tool
- [ ] Search provider abstraction (SerpAPI, Bing, Brave, etc.)

## Agent

- [ ] Intelligent fallback to web search
- [ ] Confidence-aware tool selection
- [ ] Configurable web search enable/disable

## Responses

- [ ] Document + Web answer synthesis
- [ ] Source attribution for web results
- [ ] Freshness-aware answers (timestamps for web-sourced content)

---

# Milestone 9 — GraphRAG & Internal Knowledge Engine

## Graph Construction

- [ ] Entity extraction
- [ ] Relationship extraction
- [ ] Graph builder
- [ ] Incremental graph updates

## Storage

- [ ] Graph database abstraction
- [ ] Node persistence
- [ ] Edge persistence

## Retrieval

- [ ] Graph traversal
- [ ] Hybrid retrieval
- [ ] Entity search
- [ ] Path search

## Agent

- [ ] graph_search tool
- [ ] entity_lookup tool
- [ ] relationship_lookup tool
- [ ] graph_explorer tool

## Internal Wiki

- [ ] Wiki generation
- [ ] Concept pages
- [ ] Relationship visualization
- [ ] Automatic summaries

---

# Backlog

Future ideas intentionally postponed.

- [ ] Authentication
- [ ] Multi-user support
- [ ] Cloud deployment
- [ ] Docker
- [ ] CI/CD

---

# Current Sprint (Priority Order)

Current focus (highest priority first) — Milestone 6: Advanced Agentic RAG:

1. **New tools** — summarize_document, search_by_metadata
2. **Agent improvements** — Reflection, planning, multi-step reasoning, reasoning traces
3. **Retrieval improvements** — Parent document retrieval, context compression, adaptive chunking, multi-query retrieval
4. **Multiple LLM providers** — Support OpenAI, Anthropic alongside Groq
5. **Multiple embedding providers** — Support OpenAI, Cohere alongside HuggingFace
6. **Conversation memory** — Persistent chat history via SQLite
7. **Agent observability** — Tracing, metrics, monitoring

---

# Definition of Done

A task is complete only when:

- [x] Functionality works correctly.
- [x] Architecture rules are respected.
- [x] Existing functionality remains unaffected.
- [x] Documentation is updated if necessary.
- [x] Manual testing has been completed.

---

# Maintenance Rules

Keep this document synchronized with the project.

When starting work:

- Move tasks into the active milestone.

When completing work:

- Mark tasks complete.

When priorities change:

- Update this roadmap before implementation.

This document should always represent the current state of the project.