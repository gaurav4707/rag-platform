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
│   │     ├── upload.py
│   │     ├── chat.py
│   │     └── documents.py
│   │
│   ├── services/
│   │     ├── rag_service.py
│   │     ├── document_service.py
│   │     └── chat_service.py
│   │
│   ├── rag/
│   │     ├── loader.py
│   │     ├── splitter.py
│   │     ├── embeddings.py
│   │     ├── vector_store.py
│   │     ├── retriever.py
│   │     ├── prompts.py
│   │     └── agent.py
│   │
│   ├── models/
│   │     └── schemas.py
│   │
│   ├── storage/
│   │     ├── uploads/
│   │     └── chroma/
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

The API layer must not implement business logic.

---

## Service Layer

Responsible for:

* Coordinating application workflows
* Calling RAG components
* Managing document lifecycle
* Managing conversations

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
* Vector database
* Future metadata database

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

↓

Loader

↓

Splitter

↓

Embeddings

↓

ChromaDB
```

---

## Chat

```
User Question

↓

Chat API

↓

Chat Service

↓

Retriever

↓

Prompt Builder

↓

LLM

↓

Stream Response

↓

Frontend
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

---

## retriever.py

Responsible only for retrieving relevant chunks.

It must not generate prompts.

---

## prompts.py

Responsible only for creating system prompts.

It must not retrieve documents.

---

## agent.py

Responsible only for interacting with the LLM.

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
