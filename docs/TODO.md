# TODO.md

# Project Implementation Roadmap

## Purpose

This document tracks the implementation status of the project.

It is the single source of truth for:

- Current work
- Upcoming tasks
- Completed milestones
- Future enhancements

Unlike `PROJECT_PLAN.md`, which defines **what** the project aims to become, this document tracks **what is actively being built**.

---

# Project Status

**Current Phase**

Planning & Architecture

**Overall Progress**

```text
████████░░░░░░░░░░░░ 20%
```

---

# Milestone Overview

| Milestone                 | Status         |
| ------------------------- | -------------- |
| 1. Backend Foundation     | ⏳ Not Started |
| 2. React Frontend         | ⏳ Not Started |
| 3. Retrieval Improvements | ⏳ Not Started |
| 4. Conversation Memory    | ⏳ Not Started |
| 5. UI & UX Improvements   | ⏳ Not Started |
| 6. Advanced RAG           | ⏳ Not Started |

---

# Milestone 1 — Backend Foundation

**Goal**

Build a clean, modular backend that exposes a stable API.

## Tasks

### Project Structure

- [x] Create project directory structure
- [x] Create backend package
- [x] Create frontend package
- [x] Create documentation folder
- [x] Configure environment variables

---

### FastAPI

- [x] Initialize FastAPI
- [x] Configure application entry point
- [x] Configure routing
- [x] Add health endpoint

---

### PDF Upload

- [x] Upload endpoint
- [x] Validate PDF files
- [x] Save uploaded PDFs
- [x] Generate document IDs

---

### Loader

- [x] Read PDF
- [x] Extract text
- [x] Preserve metadata

---

### Splitter

- [x] Configure RecursiveCharacterTextSplitter
- [x] Chunk documents
- [x] Preserve chunk metadata

---

### Embeddings

- [x] Initialize embedding model
- [x] Generate embeddings
- [x] Handle embedding failures

---

### Vector Store

- [x] Initialize ChromaDB
- [x] Store embeddings
- [x] Delete embeddings
- [x] Similarity search

---

### Retrieval

- [x] Retrieve relevant chunks
- [x] Remove duplicate chunks
- [x] Return retrieval metadata

---

### Prompt Builder

- [x] Create system prompt
- [x] Inject retrieved context
- [x] Prevent prompt injection from retrieved documents

---

### Agent

- [x] Initialize LLM
- [x] Stream responses
- [x] Return citations

---

### APIs

- [x] Upload API
- [x] Chat API
- [x] Streaming Chat API
- [x] List Documents API
- [x] Delete Document API

---

### Completion Criteria

Milestone 1 is complete when:

- PDFs can be uploaded.
- PDFs are indexed.
- Questions can be answered.
- Responses are streamed.
- Sources are returned.
- APIs match `API_SPEC.md`.

---

# Milestone 2 — React Frontend

**Goal**

Build a clean, responsive frontend.

## Tasks

### Project Setup

- [ ] Initialize React
- [ ] Configure TypeScript
- [ ] Configure Tailwind CSS
- [ ] Configure routing

---

### Pages

- [ ] Home
- [ ] Chat
- [ ] Documents

---

### Components

- [ ] Navigation
- [ ] Upload component
- [ ] Chat window
- [ ] Message bubble
- [ ] Source card
- [ ] Loading indicator

---

### Features

- [ ] Upload PDFs
- [ ] List documents
- [ ] Delete documents
- [ ] Chat
- [ ] Stream responses
- [ ] Render Markdown

---

### Completion Criteria

Frontend communicates successfully with backend and supports the MVP workflow.

---

# Milestone 3 — Retrieval Improvements

## Planned Tasks

- [ ] Better chunk selection
- [ ] MMR retrieval
- [ ] Query rewriting
- [ ] Retrieval evaluation
- [ ] Improved citations

---

# Milestone 4 — Conversation Memory

## Planned Tasks

- [ ] SQLite database
- [ ] Conversation model
- [ ] Message model
- [ ] Persistent chat history
- [ ] Conversation management

---

# Milestone 5 — UI & UX Improvements

## Planned Tasks

- [ ] Drag & drop upload
- [ ] Better loading states
- [ ] Error handling
- [ ] Settings page
- [ ] Dark mode
- [ ] Retrieval inspection panel
- [ ] Better source display

---

# Milestone 6 — Advanced RAG

## Planned Tasks

### Retrieval

- [ ] Hybrid Search
- [ ] Metadata filtering
- [ ] Parent Document Retriever
- [ ] Context compression

---

### Ranking

- [ ] Cross-encoder reranker
- [ ] Score threshold filtering

---

### Providers

- [ ] Multiple LLM providers
- [ ] Multiple embedding providers
- [ ] Multiple vector databases

---

### Documents

- [ ] Multi-format support
- [ ] DOCX
- [ ] TXT
- [ ] Markdown

---

### Intelligence

- [ ] Suggested questions
- [ ] Automatic document summaries
- [ ] Confidence indicators

---

# Backlog

Ideas that are intentionally postponed.

- [ ] OCR
- [ ] Image extraction
- [ ] Table extraction
- [ ] Multi-modal RAG
- [ ] Web search integration
- [ ] Graph RAG
- [ ] Authentication
- [ ] Multi-user support
- [ ] Cloud deployment
- [ ] Docker support
- [ ] CI/CD
- [ ] Unit tests
- [ ] Integration tests

---

# Current Sprint

Focus only on the following:

1. Refactor current backend into the planned architecture.
2. Implement FastAPI.
3. Build upload endpoint.
4. Build chat endpoint.
5. Build document management.
6. Verify end-to-end RAG workflow.

Do **not** start frontend development until the backend architecture is stable.

---

# Definition of Done

A task is considered complete only if:

- The implementation works.
- Code follows the documented architecture.
- Existing functionality is not broken.
- Relevant documentation is updated if needed.
- Manual testing has been performed.

---

# Maintenance Rules

This document should always reflect the current state of the project.

When work starts:

- Move tasks into the current milestone if needed.

When work finishes:

- Mark tasks as completed.

When priorities change:

- Update this document before implementing new work.

This roadmap should remain synchronized with the codebase throughout the life of the project.
