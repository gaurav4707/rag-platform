# AGENTS.md

> **Quick Reference** — repo-specific facts most likely to trip up a new agent. Full project instructions follow below.

## Status
- **Phase:** Planning & Architecture (per `docs/TODO.md`). Milestone 1 (Backend) is **not started**.
- Architecture docs (`ARCHITECTURE.md`, `API_SPEC.md`) describe a **planned** state. The current codebase is simpler and has **drifted** from the docs.

## Quick Start
```sh
source venv/bin/activate && python backend/app.py
```
Requires `GOOGLE_API_KEY` in the environment (Gemini models for embeddings + LLM).

## Known Defects (fix before building on top)
- `backend/rag/embeddings.py:5` — string literal is broken (`"EMBEDDING_MODEL` instead of `EMBEDDING_MODEL`)
- `backend/rag/vector_store.py:10` — `CHROMA_DB_DIR` is imported twice on the same line

## Architecture Drift (current vs planned docs)
| Area | Docs say | Actually is |
|---|---|---|
| Entry point | FastAPI app | `backend/app.py` — CLI script using langchain directly |
| API layer | `backend/api/` dir | Does not exist |
| Models layer | `backend/models/` dir | Does not exist |
| Utils layer | `backend/utils/` dir | Does not exist |
| Frontend | React app | Does not exist |
| Service layer | `document_service.py`, `chat_service.py` | Only `rag_service.py` (stub) |

## Must-Read Before Changes
- `docs/ARCHITECTURE.md` — layered architecture, module responsibilities, dependency rules
- `docs/DECISIONS.md` — ADRs explaining why key trade-offs were made
- `docs/RAG_PIPELINE.md` — indexing + retrieval pipeline stages

## Tooling
- **No linting, typechecking, formatting, or test infrastructure** is configured.
- All verification is manual: run `backend/app.py` and inspect output.
- Adding a linter/formatter/tester would be valuable.

## Conventions
- RAG pipeline modules live in `backend/rag/` — each file has one responsibility.
- Paths, model names, chunking params go in `backend/config.py` (never hardcoded elsewhere).
- When the architecture changes, update the relevant `docs/` file.
- Prefer standard library before adding new dependencies.

---

# AI Coding Agent Instructions

This document defines how AI coding agents should work within this project.

The primary goal is to preserve a clean architecture while incrementally building a production-quality RAG application.

---

# 1. Project Overview

This project is a local, single-user AI Document Assistant built for learning modern AI engineering.

The application allows users to:

* Upload PDF documents
* Index them into a vector database
* Ask questions about uploaded documents
* Receive grounded answers with citations

The project prioritizes understanding over rapid feature development.

---

# 2. Primary Goals

When making changes, always prioritize:

1. Correctness
2. Simplicity
3. Readability
4. Modularity
5. Maintainability

Do not optimize for writing the fewest lines of code.

---

# 3. Architectural Rules
Before making changes, read:

1. PROJECT_PLAN.md
2. ARCHITECTURE.md

Never introduce code that violates the documented architecture.

Business logic belongs in Services.

RAG logic belongs in the RAG layer.

API endpoints should remain thin.

Frontend should never contain backend logic.

---

# 4. Coding Principles

Every file should have one primary responsibility.

Every function should have one clear purpose.

Avoid large functions.

Prefer descriptive variable names.

Write explicit code instead of clever code.

Favor composition over inheritance.

Avoid unnecessary abstractions.

Do not duplicate logic.

---

# 5. When Adding Features

Before implementing a feature:

* Understand the existing architecture.
* Reuse existing modules whenever possible.
* Extend the system instead of bypassing it.

If a feature requires architectural changes, update:

* ARCHITECTURE.md
* DECISIONS.md

before implementing.

---

# 6. Allowed Changes

Agents may:

* Add new modules
* Refactor code
* Improve readability
* Fix bugs
* Improve error handling
* Improve documentation
* Add tests
* Add logging

provided the architecture remains consistent.

---

# 7. Changes Requiring Extra Care

Do not modify without good reason:

* Folder structure
* Public API contracts
* Service boundaries
* RAG pipeline
* Data flow
* Storage layout

If modifications are necessary, explain why.

---

# 8. Code Style

Use:

* Type hints
* Small functions
* Docstrings for public functions
* Meaningful names

Prefer early returns over deeply nested conditionals.

Avoid magic numbers.

Avoid global mutable state.

---

# 9. Error Handling

Do not silently ignore exceptions.

Provide informative error messages.

Validate user input.

Handle expected failures gracefully.

Avoid broad exception handling unless justified.

---

# 10. Dependencies

Before adding a new dependency:

Ask:

* Can the standard library solve this?
* Does an existing dependency already provide this?
* Is this dependency actively maintained?
* Is it necessary?

Prefer fewer dependencies.

---

# 11. Backend Rules

Backend responsibilities include:

* File upload
* PDF processing
* Chunking
* Embeddings
* Retrieval
* Prompt construction
* LLM interaction

The backend should expose clean APIs.

Do not mix UI logic into backend modules.

---

# 12. Frontend Rules

Frontend responsibilities include:

* Rendering UI
* Uploading files
* Displaying chats
* Rendering markdown
* Displaying citations

Do not perform retrieval or LLM logic in the frontend.

---

# 13. RAG Rules

The retrieval pipeline should remain modular.

Preferred flow:

PDF

↓

Loader

↓

Splitter

↓

Embeddings

↓

Vector Store

↓

Retriever

↓

Prompt Builder

↓

LLM

Avoid combining multiple stages into one file.

---

# 14. Documentation Rules

Whenever architecture changes:

Update:

* ARCHITECTURE.md

Whenever project scope changes:

Update:

* PROJECT_PLAN.md

Whenever important technical decisions are made:

Update:

* DECISIONS.md

Whenever new work is identified:

Update:

* TODO.md

Documentation should remain synchronized with the codebase.

---

# 15. Testing Philosophy

New functionality should be manually verified before considering it complete.

When practical:

* Test edge cases.
* Test invalid input.
* Test empty documents.
* Test large documents.

Avoid introducing regressions.

---

# 16. Implementation Philosophy

Build incrementally.

Keep each commit focused on one logical change.

Prefer small, reviewable improvements over large rewrites.

Avoid premature optimization.

Do not implement speculative features.

---

# 17. Project Philosophy

This project exists to learn AI engineering.

Prefer solutions that improve understanding, even if they require slightly more code.

Frameworks should be used intentionally.

The project should remain easy for both humans and AI coding agents to understand and extend.
