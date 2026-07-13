# TODO.md

# Project Implementation Roadmap

## Purpose

This document tracks the implementation status of the project.

Unlike `PROJECT_PLAN.md`, which describes the long-term vision, this document reflects the current implementation state and active development priorities.

It should always remain synchronized with the codebase.

---

# Project Status

**Current Phase**

Milestone 3 — Retrieval Intelligence (Complete)

**Overall Progress**

```text
████████████████████ 100%
```

---

# Milestone Overview

| Milestone | Status |
|-----------|--------|
| 1. Backend Foundation | ✅ Completed |
| 2. Frontend Foundation | ✅ Completed |
| 3. Retrieval Intelligence | ✅ Completed |
| 4. Agent Foundations | ✅ Completed |
| 5. User Experience | ⏳ Planned |
| 6. Advanced Agentic RAG | ⏳ Planned |

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

### Initial Tools

- [x] retrieve_context

### Additional Tools

- [ ] list_documents
- [ ] summarize_document
- [ ] search_by_filename
- [ ] search_by_metadata

### Infrastructure

- [ ] Conversation state
- [ ] Agent observability
- [ ] Debug logging

---

# Milestone 5 — User Experience

### UI

- [ ] Theme support
- [ ] Settings page
- [ ] Conversation management
- [ ] Better loading states
- [ ] Richer citation cards

### Accessibility

- [ ] Accessibility audit
- [ ] Keyboard improvements
- [ ] Screen reader improvements

### Quality

- [ ] Error recovery
- [ ] Retry support
- [ ] Better notifications

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
- [ ] Tool routing
- [ ] Multiple simultaneous tools

## Infrastructure

- [ ] Multiple LLM providers
- [ ] Multiple embedding providers
- [ ] Multiple vector databases
- [ ] Conversation memory (SQLite)
- [ ] OCR
- [ ] Background indexing
- [ ] Monitoring

---

# Backlog

Future ideas intentionally postponed.

- [ ] Multi-modal RAG
- [ ] Image extraction
- [ ] Table extraction
- [ ] Graph RAG
- [ ] Web Search
- [ ] Authentication
- [ ] Multi-user support
- [ ] Cloud deployment
- [ ] Docker
- [ ] CI/CD

---

# Current Sprint (Priority Order)

Current focus (highest priority first):

1. **API Integration Tests** — End-to-end tests for upload/chat/stream/delete endpoints
2. **Docker + Docker Compose** — Containerize backend and frontend
3. **CI/CD Pipeline** — GitHub Actions: lint, test, build
4. **Structured Logging** — JSON logs with request IDs
5. **Health Checks with Dependencies** — Verify ChromaDB/LLM connectivity
6. **Conversation Memory** — SQLite-backed chat history with context injection
7. **Observability** — Request tracing, metrics endpoint
8. **Frontend: Settings Page** — Configure retrieval parameters
9. **Frontend: Conversation History** — Persist and display chat sessions
10. **Authentication** — API key based auth (future)

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