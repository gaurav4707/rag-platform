# DECISIONS.md

# Architecture Decision Log (ADL)

## Purpose

This document records significant architectural and technical decisions made during the project.

Its purpose is to answer:

* Why was this decision made?
* What alternatives were considered?
* What trade-offs were accepted?
* When should this decision be revisited?

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

* Multi-user application
* Cloud-hosted application
* User authentication

### Consequences

Pros

* Simpler architecture
* Faster development
* Easier debugging

Cons

* Not production ready
* Cannot support multiple users simultaneously

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

* PDF + DOCX
* PDF + TXT
* All common document formats

### Consequences

Pros

* Smaller scope
* Faster implementation
* Easier testing

Cons

* Less flexible

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

* Monolithic script
* MVC
* Feature-first architecture

### Consequences

Pros

* Clear boundaries
* Easier testing
* Better scalability

Cons

* More files
* Slightly more boilerplate

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

* Fat API routes
* Business logic inside RAG modules

### Consequences

Pros

* Better separation of concerns
* Easier testing
* Reusable services

Cons

* Additional abstraction

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

* FAISS
* Qdrant
* Pinecone
* Milvus

### Consequences

Pros

* Simple setup
* Local persistence
* Good developer experience

Cons

* May not be ideal for large-scale deployments

### Revisit When

Production-scale requirements emerge or advanced retrieval capabilities are needed.

---

# ADR-006

## Title

Gemini Models for Initial Development

**Status**

Accepted

### Decision

Use Gemini for both embeddings and text generation during the initial implementation.

### Reason

The current backend already uses Gemini successfully, minimizing additional changes while building the architecture.

The design remains provider-agnostic so that models can be replaced later.

### Alternatives Considered

* OpenAI
* Hugging Face
* Local models
* OpenRouter

### Consequences

Pros

* Fast implementation
* Existing integration
* Minimal refactoring

Cons

* Provider dependency during early development

### Revisit When

Multiple provider support is introduced.

---

# ADR-007

## Title

Provider-Agnostic Design

**Status**

Accepted

### Decision

The architecture must not depend on any specific:

* LLM
* Embedding model
* Vector database

### Reason

Core application logic should remain unchanged when infrastructure components are replaced.

### Consequences

Future replacements should only require changes inside dedicated modules.

---

# ADR-008

## Title

Incremental Development Strategy

**Status**

Accepted

### Decision

The project will be developed through small milestones.

### Reason

Incremental development makes debugging easier and reduces architectural mistakes.

### Milestones

1. Backend
2. Frontend
3. Better Retrieval
4. Memory
5. UI Improvements
6. Advanced RAG

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

* what a component does
* why it exists
* what alternatives exist
* how it could be implemented manually

---

# Future Decisions

This section will grow throughout the project.

Potential future decisions include:

* Conversation storage strategy
* Hybrid search
* Reranking model selection
* Metadata schema
* Deployment architecture
* OCR integration
* Authentication
* Background task processing
* Provider selection strategy
* Caching strategy

---

# Decision Guidelines

A new decision should be recorded when:

* The project architecture changes.
* A major dependency is introduced or replaced.
* A significant trade-off is made.
* Multiple valid approaches exist and one is selected.
* Future contributors would benefit from understanding the reasoning.

Small implementation details should not be recorded here.

This document should explain **why** decisions were made, not **how** they were implemented.
