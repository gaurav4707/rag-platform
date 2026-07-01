# ARCHITECTURE.md

# System Architecture

## 1. Purpose

This document defines the overall architecture of the project.

It explains:

* Project structure
* Responsibilities of each module
* Data flow
* Design rules
* Architectural constraints

Every future feature should follow this architecture unless an explicit architectural decision is recorded in `DECISIONS.md`.

---

# 2. High-Level Architecture

```
                    +----------------------+
                    |     React Frontend   |
                    +----------+-----------+
                               |
                        HTTP / Streaming
                               |
                    +----------v-----------+
                    |      FastAPI API     |
                    +----------+-----------+
                               |
                    Application Services
                               |
          +--------------------+--------------------+
          |                    |                    |
          |                    |                    |
   Document Service      Chat Service      Document Service
          |                    |                    |
          +--------------------+--------------------+
                               |
                         RAG Engine
                               |
      +------------+-----------+-----------+------------+
      |            |           |           |            |
  Loader      Splitter    Embeddings   Retriever   Prompt Builder
                               |
                          Vector Store
                               |
                           ChromaDB
```

---

# 3. Project Structure

```
project/

│
├── backend/
│   │
│   ├── app.py
│   ├── config.py
│   │
│   ├── api/
│   │     ├── errors.py
│   │     ├── chat.py
│   │     ├── documents.py
│   │     ├── health.py
│   │     └── upload.py
│   │
│   ├── services/
│   │     ├── document_service.py
│   │     └── rag_service.py
│   │
│   ├── rag/
│   │     ├── loader.py
│   │     ├── splitter.py
│   │     ├── embeddings.py
│   │     ├── vector_store.py
│   │     ├── retriever.py
│   │     ├── prompts.py
│   │     └── rag_agent.py
│   │
│   ├── models/
│   │     └── schemas.py
│   │
│   ├── storage/
│   │     ├── uploads/
│   │     └── chroma_langchain_db/
│   │
│   └── utils/
│
├── frontend/
│
├── docs/
│
├── README.md
│
└── AGENTS.md
```

---

# 4. Layer Responsibilities

## Frontend

Responsible for:

* User interface
* File upload
* Chat interface
* Rendering streamed responses
* Showing citations

The frontend must never contain RAG logic.

---

## API Layer

Responsible for:

* Receiving requests
* Validating inputs
* Returning responses
* Streaming tokens
* Standardized error responses (via `api/errors.py`)

The API layer must not implement business logic.

---

## Service Layer

Responsible for:

* Coordinating application workflows
* Calling RAG components
* Managing document lifecycle (upload, list, delete)
* Atomic cleanup on failure

This is the project's orchestration layer.

---

## RAG Layer

Responsible for:

* Loading documents
* Chunking
* Embeddings
* Retrieval
* Prompt construction
* Agent execution

The RAG layer should never know about HTTP, React, or UI concerns.

---

## Storage Layer

Responsible for:

* Uploaded PDFs
* Vector database (ChromaDB SQLite)

Storage should not contain application logic.

---

# 5. Data Flow

## Upload

```
PDF

↓

Upload API

↓

Document Service
  - Save PDF to storage/uploads/{document_id}.pdf
  - Generate UUID document_id
  - If any step fails: remove saved file + vector entries (atomic rollback)

↓

Loader (PyPDFLoader)

↓

Splitter (RecursiveCharacterTextSplitter)

↓

Metadata Enrichment
  - document_id
  - filename
  - chunk_index
  - page number (from loader)

↓

Embeddings (HuggingFace BGE)

↓

ChromaDB (PersistentClient, auto-persisted to SQLite)
```

---

## Chat

```
User Question

↓

Chat API
  - Build sources from similarity search

↓

RAG Service

↓

Agent
  - Retrieves context via retriever tool
  - Builds prompt via prompt_with_context middleware
  - Generates answer via LLM

↓

Chat Response
  - answer (text)
  - sources (filename, page, document_id, score)
  - tool_calls (debug info)
```

---

## List Documents

```
GET /documents

↓

Document Service
  list_indexed_documents()

↓

Vector Store
  Chroma.get() → unique document_ids from metadata

↓

Response
  [{document_id, filename, status}]
```

---

## Delete Document

```
DELETE /documents/{document_id}

↓

Document Service
  delete_document(document_id)
  - Check document exists → 404 if not
  - Delete vectors from ChromaDB
  - Delete PDF from storage/uploads/

↓

Response
  {status: "deleted"}
```

---

# 6. Module Responsibilities

## loader.py

Responsible only for reading PDF files.

Must not perform chunking.

---

## splitter.py

Responsible only for chunking documents.

Must not generate embeddings.

---

## embeddings.py

Responsible only for embedding generation.

Must not interact with the UI.

---

## vector_store.py

Responsible only for vector database operations.

Examples:

* add documents
* delete documents
* similarity search
* similarity search with scores
* list unique documents from metadata

Uses a cached singleton `Chroma` instance for connection reuse.

---

## retriever.py

Responsible only for retrieving relevant chunks.

Returns both serialized content (for the LLM) and document objects (as artifact).

---

## prompts.py

Responsible only for creating system prompts.

---

## rag_agent.py

Responsible only for building the LangChain agent with tools and middleware.

---

## api/errors.py

Responsible for standardized error responses.

Provides:

* `AppError` exception class with machine-readable error codes
* Exception handlers for `AppError` and `HTTPException`
* Error code constants (INVALID_FILE, DOCUMENT_NOT_FOUND, INDEXING_FAILED, VECTOR_STORE_ERROR, INTERNAL_SERVER_ERROR)

---

# 7. Dependency Rules

Allowed:

```
API

↓

Services

↓

RAG

↓

Storage
```

Not allowed:

```
Frontend

↓

RAG
```

or

```
Vector Store

↓

API
```

Dependencies should always point downward.

---

# 8. Design Principles

Every module should have a single responsibility.

Every file should have a clear purpose.

Avoid global state whenever possible.

Favor dependency injection over hidden dependencies.

Prefer composition over inheritance.

Prefer explicit behavior over implicit behavior.

---

# 9. Future Extension Points

The architecture should allow adding:

* New embedding models
* New LLM providers
* New vector databases
* OCR
* Conversation memory
* Hybrid retrieval
* Metadata filtering
* Reranking

without changing unrelated modules.

---

# 10. Architecture Constraints

The following rules should not be violated without recording an architectural decision:

* The frontend must never contain backend logic.
* API endpoints must remain thin.
* Business logic belongs in services.
* RAG logic belongs in the RAG layer.
* Storage must not contain application logic.
* Every module should have one primary responsibility.
* New features should extend the architecture rather than bypass it.
