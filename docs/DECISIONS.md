# DECISIONS.md

# Architecture Decision Log (ADL)

## Purpose

This document records significant architectural and technical decisions made during the project.

Its purpose is to answer:

- Why was this decision made?
- What alternatives were considered?
- What trade-offs were accepted?
- When should this decision be revisited?

This document should evolve throughout the project's lifetime.

---

# Status Definitions

| Status     | Meaning                      |
| ---------- | ---------------------------- |
| Accepted   | Current project decision     |
| Proposed   | Under discussion             |
| Superseded | Replaced by a newer decision |
| Deprecated | No longer recommended        |

---

# ADR-001

## Title

Single User Local Application

**Status**

Accepted

### Decision

The application will initially support a single local user.

No authentication or user management will be implemented.

### Reason

The project's primary objective is learning AI engineering and RAG architecture.

Authentication, authorization, and multi-user support would introduce significant complexity without improving understanding of the RAG system.

### Alternatives Considered

- Multi-user application
- Cloud-hosted application
- User authentication

### Consequences

Pros

- Simpler architecture
- Faster development
- Easier debugging

Cons

- Not production ready
- Cannot support multiple users simultaneously

### Revisit When

The project transitions toward production deployment.

---

# ADR-002

## Title

PDF-Only Support for MVP

**Status**

Accepted

### Decision

The first version of the application will support only PDF documents.

### Reason

Supporting multiple file formats would require additional parsing logic and testing.

Restricting the MVP to PDFs allows focus on the RAG pipeline rather than document ingestion.

### Alternatives Considered

- PDF + DOCX
- PDF + TXT
- All common document formats

### Consequences

Pros

- Smaller scope
- Faster implementation
- Easier testing

Cons

- Less flexible

### Revisit When

After the MVP is complete.

---

# ADR-003

## Title

Layered Architecture

**Status**

Accepted

### Decision

The project will follow a layered architecture:

```text
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

### Reason

Separating responsibilities makes the application easier to understand, maintain, and extend.

### Alternatives Considered

- Monolithic script
- MVC
- Feature-first architecture

### Consequences

Pros

- Clear boundaries
- Easier testing
- Better scalability

Cons

- More files
- Slightly more boilerplate

### Revisit When

A future requirement cannot be cleanly implemented within the existing layers.

---

# ADR-004

## Title

Business Logic Lives in Services

**Status**

Accepted

### Decision

Business logic must reside in the Service layer.

API routes should remain thin.

### Reason

This keeps HTTP concerns separate from application behavior and makes the core logic reusable.

### Alternatives Considered

- Fat API routes
- Business logic inside RAG modules

### Consequences

Pros

- Better separation of concerns
- Easier testing
- Reusable services

Cons

- Additional abstraction

---

# ADR-005

## Title

Use ChromaDB for Vector Storage

**Status**

Accepted

### Decision

Use ChromaDB as the initial vector database.

### Reason

ChromaDB is lightweight, local-first, easy to integrate with LangChain, and suitable for development.

### Alternatives Considered

- FAISS
- Qdrant
- Pinecone
- Milvus

### Consequences

Pros

- Simple setup
- Local persistence
- Good developer experience

Cons

- May not be ideal for large-scale deployments

### Revisit When

Production-scale requirements emerge or advanced retrieval capabilities are needed.

---

# ADR-006

## Title

Provider Selection for Initial Development

**Status**

Accepted

### Decision

The project may use different providers during development (Groq, Gemini, OpenAI, etc.), but the architecture remains provider-agnostic.

The current implementation uses the provider that best supports the required features while keeping the remainder of the codebase independent of provider-specific APIs.

### Reason

Provider capabilities evolve rapidly. Selecting providers at the infrastructure layer allows experimentation without affecting the application architecture.

### Alternatives Considered

- Gemini
- Groq
- OpenAI
- Hugging Face
- Local models

### Consequences

Pros

- Easy provider experimentation
- No vendor lock-in
- Minimal refactoring when switching providers

Cons

- Requires abstraction layers
- Feature parity may vary across providers

### Revisit When

A production deployment standardizes on a specific provider.

---

# ADR-007

## Title

Provider-Agnostic Design

**Status**

Accepted

### Decision

The architecture must not depend on any specific:

- LLM
- Embedding model
- Vector database

### Reason

Core application logic should remain unchanged when infrastructure components are replaced.

### Consequences

Future replacements should only require changes inside dedicated modules.

---

# ADR-008A

## Title

Adopt an Agentic RAG Architecture

**Status**

Accepted

### Decision

The project adopts an Agentic Retrieval-Augmented Generation (Agentic RAG) architecture instead of a traditional deterministic RAG pipeline.

The LLM acts as an agent that can decide which tools to invoke in order to answer a user's request.

During the MVP, the agent has a single tool:

- retrieve_context

Additional tools will be introduced in later milestones.

### Reason

The project's primary goal is to learn modern AI engineering practices rather than only build a document chatbot.

An agent-based architecture provides a flexible foundation for adding capabilities without changing the API or service layers.

### Alternatives Considered

- Traditional RAG pipeline
- Workflow-based orchestration (LangGraph)
- Multiple specialized APIs

### Consequences

Pros

- Extensible architecture
- Natural support for multiple tools
- Provider-independent tool abstraction
- Easier expansion into autonomous workflows

Cons

- Higher implementation complexity
- Greater dependence on model tool-calling support
- More difficult debugging during early development

### Revisit When

If future requirements favor deterministic workflows over dynamic tool selection.

---

# ADR-008

## Title

Incremental Development Strategy

**Status**

Accepted

### Decision

The project will be developed through incremental milestones, with each milestone building on the previous one while maintaining a working application.

### Reason

Incremental development keeps the architecture stable, reduces debugging complexity, and allows each subsystem to mature before introducing additional capabilities.

### Milestones

1. Backend Foundation
   - FastAPI
   - PDF upload
   - ChromaDB
   - Basic retrieval
   - Streaming chat

2. Frontend Foundation
   - React UI
   - Upload interface
   - Document management
   - Streaming chat interface
   - Source citations

3. Retrieval Intelligence
   - Better chunking
   - Metadata filtering
   - Query rewriting
   - Hybrid retrieval
   - MMR
   - Reranking

4. Agent Foundations
   - Tool registry
   - Agent orchestration
   - Tool execution
   - Streaming tool calls
   - Conversation state

5. User Experience
   - Responsive UI
   - Accessibility
   - Settings
   - Better citations
   - Conversation management

6. Advanced Agentic RAG
   - Multiple tools
   - Reflection
   - Planning
   - Multi-step reasoning
   - Multiple LLM providers
   - OCR
   - Memory

---

# ADR-009

## Title

Understanding Over Abstraction

**Status**

Accepted

### Decision

Every major framework component should be understood before it is adopted.

### Reason

The project is educational.

Framework abstractions should not hide important concepts.

When practical, developers should understand:

- what a component does
- why it exists
- what alternatives exist
- how it could be implemented manually

---

# ADR-010

## Title

Persistent Local Document Storage

**Status**

Accepted

### Decision

Uploaded PDFs are stored on the local filesystem under `storage/uploads/{document_id}.pdf`.

### Reason

The application is single-user and local. File system storage is the simplest option that meets the requirement.

### Alternatives Considered

- In-memory storage (lost on restart)
- Database BLOB storage (premature for current scope)
- Object storage (S3, GCS — adds unnecessary complexity)

### Consequences

Pros

- Simple implementation
- No additional dependencies
- Files survive server restarts
- Easy manual inspection

Cons

- Not suitable for multi-server deployments
- No built-in backup strategy

### Revisit When

Multi-user support or cloud deployment is needed.

---

# ADR-011

## Title

Document Metadata Schema

**Status**

Accepted

### Decision

Document metadata is stored only in ChromaDB alongside each chunk.

The metadata schema for each chunk is:

| Field       | Type | Example                         |
| ----------- | ---- | ------------------------------- |
| document_id | str  | uuid.uuid4()                    |
| filename    | str  | "research.pdf"                  |
| page        | int  | 7 (0-indexed, from PyPDFLoader) |
| chunk_index | int  | 0 (ordinal within document)     |
| source      | str  | File path                       |

Documents are uniquely identified by `document_id`. The ChromaDB metadata is the source of truth for document existence — the uploads directory is never scanned.

### Reason

Storing metadata in ChromaDB keeps the architecture simple (no additional database) while allowing the document list and deletion features to work correctly.

### Alternatives Considered

- SQLite database for document registry (cleaner separation, but adds complexity)
- File-system scan (unreliable, conflicts with vector data)
- JSON manifest file (race conditions on concurrent uploads)

### Consequences

Pros

- Single source of truth
- No additional database dependency
- Document list available without file-system access
- Delete operation can find all vectors by document_id

Cons

- Cannot retrieve document list if vector store is corrupted
- Metadata is tightly coupled to vector storage

### Revisit When

A dedicated metadata database (e.g., SQLite) is introduced for conversation history or user settings.

---

# ADR-012

## Title

Standardized Error Response Format

**Status**

Accepted

### Decision

All API errors follow a consistent JSON format:

```json
{
  "error": {
    "code": "MACHINE_READABLE_CODE",
    "message": "Human-readable description"
  }
}
```

Error codes are defined as constants in `api/errors.py`.

### Reason

A consistent error format simplifies frontend error handling and debugging.

### Error Codes

| Code                  | HTTP Status | Description                   |
| --------------------- | ----------- | ----------------------------- |
| INVALID_FILE          | 400         | Bad file type or empty file   |
| DOCUMENT_NOT_FOUND    | 404         | Document does not exist       |
| INDEXING_FAILED       | 422         | PDF extraction/indexing error |
| VECTOR_STORE_ERROR    | 500         | ChromaDB operation failure    |
| INTERNAL_SERVER_ERROR | 500         | Unexpected error              |

### Consequences

Pros

- Predictable error structure
- Machine-readable codes for conditional handling
- Human-readable messages for display

Cons

- Requires error handler registration in app.py

---

# ADR-013

## Title

Chroma Singleton Caching

**Status**

Accepted

### Decision

The Chroma vector store client is cached as a module-level singleton in `vector_store.py`.

### Reason

Creating a new `Chroma` instance on every request is wasteful. LangChain's Chroma wrapper uses the same approach internally with `get_or_create_collection()`.

### Consequences

Pros

- Reuses the same persistent connection
- Reduces latency on repeated requests
- Consistent collection reference

Cons

- Module-level global state
- Not thread-safe (acceptable for single-user)

---

# ADR-014

## Title

Tool-Oriented RAG Design

**Status**

Accepted

### Decision

Capabilities exposed to the LLM are implemented as tools rather than embedding business logic inside the agent.

Each tool should have a single responsibility and delegate work to the appropriate module.

Examples include:

- retrieve_context
- list_documents
- summarize_document
- search_by_metadata

### Reason

Keeping tools small and focused improves maintainability, testing, and future extensibility.

The agent becomes an orchestrator rather than an implementation layer.

### Alternatives Considered

- Large monolithic agent
- Business logic inside prompts
- Direct LLM access to storage

### Consequences

Pros

- Clear separation of concerns
- Reusable functionality
- Easier addition of new tools

Cons

- More modules
- Slightly higher initial complexity

### Revisit When

The application introduces complex multi-agent workflows.

---

## ADR-00X: Single Retrieval per Request

### Status

Accepted

---

### Context

Earlier versions of the system performed multiple retrieval operations for a single user request.

Typical execution looked like:

```
User Question

↓

Retriever

↓

Prompt Construction

↓

LLM

↓

Retriever (again)

↓

Source Citations
```

Although functional, this approach had several drawbacks:

- Duplicate vector store queries
- Additional latency
- Increased compute cost
- Risk of citations differing from the context actually provided to the LLM
- Blurred responsibility between retrieval and citation generation

As the project evolves toward Agentic RAG, retrieval becomes an increasingly important capability that may include hybrid search, reranking, metadata filtering, and query rewriting. Repeating these operations multiple times per request would be inefficient and difficult to maintain.

---

### Decision

Exactly one retrieval operation will occur for each user request.

The retriever returns a `RetrievalResult` containing the retrieved chunks and associated metadata.

This `RetrievalResult` is reused throughout the remainder of the request lifecycle.

Consumers include:

- Prompt Builder
- Citation Builder
- Agent

No downstream component may issue another vector store query for the same request.

---

### Consequences

#### Advantages

- Reduced latency
- Fewer vector database queries
- Lower compute cost
- Consistent citations
- Clear separation of responsibilities
- Easier debugging
- Simpler future integration of reranking and hybrid retrieval

#### Trade-offs

- RetrievalResult becomes a shared domain model between components.
- Downstream modules depend on retrieval metadata being preserved.

These trade-offs are acceptable because they improve architectural clarity and scalability.

---

### Alternatives Considered

#### Repeat Retrieval

Advantages

- Simple implementation
- Independent citation generation

Disadvantages

- Duplicate work
- Inconsistent citations
- Harder to evolve retrieval

Rejected.

---

#### Prompt Parsing

Generate citations by parsing the final prompt.

Rejected because:

- Prompt formatting may change.
- Prompt contents are not a reliable API.
- Couples citation generation to prompt templates.

---

### Rationale

Retrieval is an expensive operation and should be treated as the single source of truth for the lifetime of a request.

Future retrieval improvements—including hybrid search, reranking, metadata filtering, and query rewriting—should operate once and produce a reusable `RetrievalResult`.

This design keeps the retrieval pipeline modular while ensuring that all downstream components operate on identical context.

---

# Future Decisions

This section will grow throughout the project.

Potential future decisions include:

- Conversation memory strategy
- Agent planning strategy
- Tool selection policies
- Hybrid retrieval
- Reranking models
- OCR integration
- Multi-agent workflows
- Authentication
- Deployment architecture
- Caching strategy
- Observability and tracing

---

# Decision Guidelines

A new decision should be recorded when:

- The project architecture changes.
- A major dependency is introduced or replaced.
- A significant trade-off is made.
- Multiple valid approaches exist and one is selected.
- Future contributors would benefit from understanding the reasoning.

Small implementation details should not be recorded here.

This document should explain **why** decisions were made, not **how** they were implemented.
