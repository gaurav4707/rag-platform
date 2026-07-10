# ARCHITECTURE.md

# System Architecture

## 1. Purpose

This document defines the overall architecture of the project.

It explains:

- Project structure
- Responsibilities of each module
- Data flow
- Design rules
- Architectural constraints

This project follows an **Agentic Retrieval-Augmented Generation (Agentic RAG)** architecture.

The system is designed to be:

- Modular
- Provider-agnostic
- Local-first
- Single-user (MVP)
- Easy to extend with additional tools and retrieval strategies

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
          |                                         |
   Document Service                          Chat Service
          |                                         |
          +--------------------+--------------------+
                               |
                         Agentic RAG Engine
                               |
               +---------------+---------------+
               |                               |
            Agent                       Prompt Builder
               |
        Tool Registry
               |
    +----------+-----------+----------------+
    |                      |                |
Retriever Tool       Future Tools       Future Tools
(retrieve_context)   (Web Search,       (Calculator,
                     Metadata, etc.)    Summarizer...)
    |
Retriever (Strategy Dispatch)
    |
Vector Store (Similarity / MMR / Metadata Filtering)
    |
    RetrievalResult
    │
    ├────────────► Prompt Builder
    │
    ├────────────► Citation Builder
    │
    └────────────► Agent
    |
Embeddings
    |
Splitter
    |
Loader
    |
Storage (PDFs)
```

---

# 3. Project Structure

```
project/

├── backend/
│
├── app.py
├── config.py
│
├── api/
│   ├── chat.py
│   ├── documents.py
│   ├── upload.py
│   ├── health.py
│   └── errors.py
│
├── services/
│   ├── document_service.py
│   └── rag_service.py
│
├── rag/
│   ├── loader.py
│   ├── splitter.py
│   ├── embeddings.py
│   ├── vector_store.py
│   ├── retriever.py
│   ├── retrieval_config.py
│   ├── tool_registry.py
│   ├── agent.py
│   ├── prompts.py
│   └── citations.py
│
├── models/
│   ├── schemas.py
│   └── rag_models.py
│
├── tests/
│   ├── __init__.py
│   ├── conftest.py
│   └── test_retriever.py
│
├── storage/
│   ├── uploads/
│   └── chroma_langchain_db/
│
├── utils/

frontend/

docs/

README.md

AGENTS.md
```

---

# 4. Layer Responsibilities

## Frontend

Responsible for:

- User interface
- File upload
- Chat interface
- Rendering streamed responses
- Showing citations

The frontend must never contain RAG logic.

---

## API Layer

Responsible for:

- Receiving requests
- Validating inputs
- Returning responses
- Streaming tokens
- Standardized error responses

The API layer must remain thin.

---

## Service Layer

Responsible for:

- Coordinating application workflows
- Managing uploads
- Managing document lifecycle
- Orchestrating Agentic RAG execution

No retrieval logic should live here.

---

## RAG Layer

Responsible for:

- Loading
- Chunking
- Embeddings
- Retrieval (strategy-based)
- Tool registration
- Agent orchestration
- Prompt construction
- Citation building

The RAG layer must never know about HTTP or React.

---

## Storage Layer

Responsible for:

- Uploaded PDFs
- Persistent vector database

Storage contains data only.

No business logic.

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

Metadata Enrichment

↓

Embeddings

↓

Vector Store
```

---

## Chat

```
User Question

↓

Chat API

↓

RAG Service

↓

Agent

↓

Chooses Tool
(via Tool Registry)

↓

Retriever Tool (retrieve_context)

↓

Retriever (Strategy Dispatch)
├── Similarity
└── MMR

↓

Vector Store

↓

RetrievalResult
      │
      ├────────────► Prompt Builder
      │
      ├────────────► Citation Builder
      │
      └────────────► Agent

↓

LLM

↓

ChatResult

↓

Streaming Response
```

The Agent decides which tool(s) to invoke.

For the MVP there is only one tool:

- retrieve_context

The architecture is intentionally designed so additional tools can be added without changing the API layer.

---

## List Documents

```
GET /documents

↓

Document Service

↓

Vector Store

↓

Response
```

---

## Delete Document

```
DELETE /documents/{document_id}

↓

Document Service

↓

Vector Store

↓

Delete PDF

↓

Response
```

---

# 6. Module Responsibilities

## loader.py

Reads PDF files.

Only responsible for document loading.

---

## splitter.py

Splits documents into chunks.

---

## embeddings.py

Generates embeddings.

No retrieval logic.

---

## vector_store.py

Responsible for:

- Chroma client lifecycle
- Similarity search with scores and metadata filtering
- MMR search with scores and metadata filtering
- All ChromaDB-specific logic (embedding calls, `maximal_marginal_relevance`, `_results_to_docs`)

Examples:

- add_documents()
- delete_document()
- similarity_search_with_scores()
- similarity_search_with_scores_filtered()
- mmr_search_with_scores()
- list_documents()

The vector store is the only module that imports Chroma or generates embeddings.

---

## retriever.py

Responsible only for retrieval orchestration.

It should:

- select a retrieval strategy (similarity vs MMR)
- call the Vector Store
- build RetrievedChunk objects
- return a RetrievalResult

It must never:

- import Chroma
- generate embeddings
- interact with the LLM
- build prompts
- build citations

The RetrievalResult is the single source of truth for downstream components.

---

## prompts.py

Responsible only for prompt construction.

Consumes:

- user question
- RetrievalResult

Produces:

- messages for the LLM

The Prompt Builder never performs retrieval.

---

## citations.py

Responsible only for building API source citations.

Consumes:

- RetrievalResult

Produces:

- list[SourceItem]

The Citation Builder never queries the vector store.

It reuses the RetrievalResult produced earlier in the request.

---

## retrieval_config.py

Defines the `RetrievalConfig` dataclass for configuring retrieval behavior.

Fields:

- top_k: int (default 4)
- search_type: "similarity" | "mmr" (default "similarity")
- score_threshold: float | None
- fetch_k: int (default 20)
- lambda_mult: float (default 0.5)
- metadata_filter: dict | None

Provides a `DEFAULT_RETRIEVAL_CONFIG` singleton.

---

## tool_registry.py

Registers all Agent tools and provides them to the Agent.

Current:

- retrieve_context

Future:

- list_documents
- summarize_document
- search_by_filename
- search_by_metadata
- web_search
- calculator

Tool implementations should remain thin and delegate business logic to the appropriate modules.

---

## agent.py

Responsible only for:

- creating the LangChain agent
- registering tools via the Tool Registry
- coordinating tool execution
- assembling the ChatResult (answer + citations + tool_calls)
- exposing a streaming interface

The Agent:

- selects tools via LangChain tool-calling
- consumes RetrievalResult
- streams model output

The Agent must never query the vector store directly.

---

## api/errors.py

Responsible for standardized API errors.

---

## RetrievalResult

The RetrievalResult is a shared data model produced by the retriever.

It represents the outcome of a single retrieval operation and is reused throughout the request lifecycle.

Consumers include:

- Prompt Builder
- Citation Builder
- Agent

This ensures that retrieval occurs exactly once per user request while maintaining consistent citations and reducing unnecessary vector store queries.

---

# 7. Dependency Rules

Allowed

```
Frontend

↓

API

↓

Services

↓

RAG

↓

Storage
```

Inside the RAG layer

```
Agent
      │
      ▼
Tool Registry
      │
      ▼
Tools (retrieve_context, etc.)
      │
      ▼
Retriever
      │
      ▼
Vector Store
      │
      ▼
RetrievalResult
      │
      ├────────► Prompt Builder
      └────────► Citation Builder
```

Dependencies must always point downward.

---

# 8. Design Principles

- Single Responsibility
- Explicit data flow
- Thin APIs
- Modular RAG components
- Provider agnostic
- Tool-oriented architecture
- Composition over inheritance
- Clear separation between orchestration and implementation

---

# 9. Future Extension Points

The architecture should allow adding:

## Retrieval

- Hybrid Search
- Query Rewriting
- Reranking

## Agent

- Multiple tools
- Tool routing
- Multi-step reasoning
- Reflection
- Planning

## Infrastructure

- New LLM providers
- New embedding models
- New vector databases
- OCR
- Conversation memory

without changing unrelated modules.

---

# 10. Architecture Constraints

The following rules should not be violated without recording an architectural decision:

- The frontend must never contain backend logic.
- API endpoints must remain thin.
- Business logic belongs in services.
- Agent orchestration belongs inside the RAG layer.
- Retrieval orchestration belongs inside retriever.py.
- Retrieval implementation (ChromaDB calls, embeddings) belongs inside vector_store.py.
- Tool definitions belong inside tool_registry.py.
- Prompt construction belongs inside prompts.py.
- Storage must never contain business logic.
- Every module should have one primary responsibility.
- New capabilities should extend the architecture instead of bypassing it.
- Exactly one retrieval operation should occur for each user request.
- All downstream components must reuse the RetrievalResult instead of issuing additional vector store queries.