# 🤖 Agents Architecture (AGENTS.md)

> This document defines the AI agents, coding personas, autonomous workflows, MCP integrations, and execution policies used throughout this repository.
>
> It serves as the primary reference for both human contributors and AI coding agents working on this project.

---

# 📌 Overview

This project is a **production-style Agentic Retrieval-Augmented Generation (Agentic RAG) Platform** designed to demonstrate modern AI engineering practices while maintaining a clean, modular, provider-agnostic architecture.

Unlike traditional RAG systems that execute a fixed retrieval pipeline, this project uses an **LLM-powered Agent** capable of selecting tools to accomplish user requests.

The system intentionally separates responsibilities into independent modules so each component has one primary responsibility and can evolve independently.

The current MVP supports:

- PDF upload
- Document indexing
- Semantic retrieval
- Tool-calling Agent
- Streaming responses
- Source citations
- Document management

Future milestones will expand the platform into a true multi-tool AI system while preserving the existing API contract.

---

# 🏗 Architecture Summary

```
User

↓

React Frontend

↓

FastAPI API

↓

Application Services

↓

Agent

↓

Tool Registry

↓

Retriever Tool

↓

Retriever

↓

Vector Store

↓

Embeddings

↓

Document Chunks

↓

LLM

↓

Streaming Response
```

The architecture follows strict layered boundaries documented in:

- `ARCHITECTURE.md`
- `RAG_PIPELINE.md`
- `DECISIONS.md`

---

# 🎭 Agent Profiles

---

## 1. Conversational RAG Agent

### Role / Persona

AI Research Assistant specializing in answering questions using uploaded documents.

---

### Goal / Objective

Provide accurate, grounded answers by retrieving relevant document context before generating a response.

---

### Responsibilities

- Receive user questions
- Decide which tools are required
- Invoke retrieval tools
- Generate grounded responses
- Stream output
- Return citations
- Record tool execution metadata

---

### System Prompt / Backstory

Acts as an intelligent document assistant.

Must never fabricate information.

Must ground answers in retrieved context.

Must remain provider-agnostic.

Must orchestrate tools rather than implementing business logic.

---

### Primary Implementation

```
backend/rag/agent.py
```

---

### Tools & Capabilities

Current

- retrieve_context

Future

- summarize_document
- search_by_metadata
- search_documents
- list_documents
- web_search
- calculator

---

### Inputs Expected

- User question
- Conversation messages
- RetrievalResult
- Retrieval configuration

---

### Outputs Expected

```
ChatResult
```

Containing

- Answer
- Source citations
- Tool execution metadata

---

## 2. Retrieval Agent (Retriever)

### Role / Persona

Semantic Retrieval Specialist

---

### Goal / Objective

Retrieve the most relevant document chunks while remaining independent from prompt construction and LLM generation.

---

### Responsibilities

- Choose retrieval strategy
- Invoke vector store
- Build RetrievalResult
- Preserve metadata
- Return ranked chunks

---

### System Prompt / Backstory

Acts as a retrieval orchestrator only.

Never performs:

- Prompt construction
- Citation generation
- LLM interaction

---

### Primary Implementation

```
backend/rag/retriever.py
```

---

### Tools & Capabilities

Supports

- Similarity Search
- Maximum Marginal Relevance (MMR)
- Metadata filtering
- RetrievalConfig

Future

- Hybrid Search
- Query Rewriting
- Multi-query Retrieval
- Reranking

---

### Inputs Expected

- Query
- RetrievalConfig

---

### Outputs Expected

```
RetrievalResult
```

---

## 3. Prompt Builder Agent

### Role / Persona

Prompt Engineering Specialist

---

### Goal / Objective

Convert retrieved context into an optimal prompt for the LLM.

---

### Responsibilities

- Format retrieved chunks
- Build system/user messages
- Preserve metadata
- Never perform retrieval

---

### Primary Implementation

```
backend/rag/prompts.py
```

---

### Inputs Expected

- User question
- RetrievalResult

---

### Outputs Expected

LLM-ready messages

---

## 4. Citation Builder Agent

### Role / Persona

Evidence & Attribution Specialist

---

### Goal / Objective

Generate citations corresponding exactly to the retrieved context.

---

### Responsibilities

- Convert metadata into API citations
- Preserve filename
- Preserve page number
- Preserve document ID
- Preserve retrieval score

Never performs retrieval.

---

### Primary Implementation

```
backend/rag/citations.py
```

---

### Inputs Expected

```
RetrievalResult
```

---

### Outputs Expected

```
list[SourceItem]
```

---

## 5. Tool Registry Agent

### Role / Persona

Capability Manager

---

### Goal / Objective

Expose available tools to the Agent.

---

### Responsibilities

- Register tools
- Provide tool definitions
- Keep tools thin
- Delegate work to appropriate modules

---

### Primary Implementation

```
backend/rag/tool_registry.py
```

---

### Current Tools

- retrieve_context

---

### Planned Tools

- search_documents
- summarize_document
- web_search
- calculator
- search_by_filename
- search_by_metadata

---

### Inputs Expected

Tool registration requests

---

### Outputs Expected

Registered LangChain tools

---

## 6. Document Processing Agent

### Role / Persona

Document Ingestion Specialist

---

### Goal / Objective

Transform uploaded PDFs into searchable vector representations.

---

### Responsibilities

Sequentially execute

- PDF loading
- Metadata enrichment
- Chunking
- Embeddings
- Vector storage

---

### Primary Modules

```
backend/rag/loader.py

backend/rag/splitter.py

backend/rag/embeddings.py

backend/rag/vector_store.py
```

---

### Inputs Expected

Uploaded PDF

---

### Outputs Expected

Indexed document inside ChromaDB

---

## 7. RAG Service Agent

### Role / Persona

Workflow Orchestrator

---

### Goal /Objective

Coordinate the complete chat workflow.

---

### Responsibilities

- Receive API request
- Invoke Agent
- Return ChatResult

Contains orchestration only.

---

### Primary Implementation

```
backend/services/rag_service.py
```

---

## 8. Document Service Agent

### Role / Persona

Document Lifecycle Manager

---

### Goal / Objective

Manage uploaded documents.

---

### Responsibilities

- Upload
- Delete
- List
- Index

---

### Primary Implementation

```
backend/services/document_service.py
```

---

### Inputs Expected

PDF uploads

Document IDs

---

### Outputs Expected

Document lifecycle operations

---

# 🤖 AI Coding Agent (OpenCode)

This repository is optimized for AI-assisted development using OpenCode.

Unlike runtime agents, this agent assists developers during implementation.

---

## Role / Persona

Senior AI Software Engineer

Senior Python Engineer

Senior React Engineer

Senior AI Systems Architect

Technical Reviewer

---

## Goal / Objective

Produce production-quality code while preserving the documented architecture.

---

## Responsibilities

- Implement features
- Refactor safely
- Fix bugs
- Update documentation
- Preserve architecture
- Avoid technical debt

---

## Required Reading Before Every Task

Always read:

```
PROJECT_PLAN.md

ARCHITECTURE.md

RAG_PIPELINE.md

DECISIONS.md

API_SPEC.md

AGENTS.md
```

---

## Coding Principles

Must follow

- Single Responsibility Principle
- Layered Architecture
- Provider Agnostic Design
- Explicit Data Flow
- Thin API Layer
- Business Logic in Services
- Retrieval Orchestration in Retriever
- Prompt Construction in Prompt Builder
- Tool-Oriented Design

---

## Never

- Duplicate business logic
- Bypass architecture
- Mix layers
- Hardcode provider-specific logic
- Introduce hidden dependencies

---

# 🧠 MCP Tool Integrations

The development environment includes several MCP servers.

These should be used proactively whenever appropriate.

---

## Context7 MCP

### Purpose

Official framework and library documentation.

### Use For

- FastAPI
- LangChain
- ChromaDB
- React
- Tailwind
- TypeScript
- Pydantic
- Python libraries

### Rules

- Prefer official documentation over memory.
- Never invent APIs.
- Verify method signatures before implementation.

---

## Filesystem MCP

### Purpose

Repository understanding and file manipulation.

### Use For

- Searching code
- Reading files
- Refactoring
- Updating documentation
- Locating implementations

### Rules

Before creating new files:

- Search the repository.
- Reuse existing modules.
- Avoid duplication.

---

## Knowledge Graph MCP

### Purpose

Dependency and relationship analysis.

### Use For

- Refactoring
- Dependency tracing
- Call graph analysis
- Architecture impact analysis
- Rename operations

---

## Sequential Thinking MCP

### Purpose

Structured reasoning.

### Required For

- Complex features
- Multi-file changes
- Debugging
- Architecture work
- Retrieval improvements
- Agent modifications

Implementation should follow planning.

---

## Playwright MCP

### Purpose

Browser automation.

### Use For

- UI testing
- Upload verification
- Streaming verification
- API integration
- Responsive testing

Required workflow

1. Launch application
2. Execute scenario
3. Check browser console
4. Verify UI behavior
5. Report findings

Never claim success without verification.

---

## Memory MCP

### Purpose

Long-term project memory.

### Store

- Stable architectural decisions
- Project conventions
- Reusable implementation patterns

Do NOT store

- Temporary bugs
- Experimental code
- Sensitive information

---

# 🔄 Workflows & Collaboration

## Document Indexing

```
Upload API

↓

Document Service

↓

Loader

↓

Metadata Enrichment

↓

Splitter

↓

Embeddings

↓

Vector Store
```

---

## Chat Execution

```
User

↓

Chat API

↓

RAG Service

↓

Conversational Agent

↓

Tool Registry

↓

retrieve_context

↓

Retriever

↓

Vector Store

↓

RetrievalResult

↓

Prompt Builder

↓

LLM

↓

Citation Builder

↓

ChatResult

↓

Streaming Response
```

---

## Development Workflow

```
Task

↓

Sequential Thinking MCP

↓

Filesystem MCP

↓

Knowledge Graph MCP

↓

Context7 MCP

↓

Implementation

↓

Playwright Verification

↓

Documentation Update

↓

Completion
```

---

# 🛠 Environment & Configuration

## Backend

```
Python

FastAPI

LangChain

ChromaDB

HuggingFace Embeddings

Groq (Current LLM)

Pydantic
```

---

## Frontend

```
React

TypeScript

Vite

Tailwind CSS
```

---

## Primary Configuration

```
backend/config.py
```

Contains

- Model names
- Storage paths
- Chunk size
- Chunk overlap
- Vector database configuration

---

## Environment Variables

Typical examples

```
GOOGLE_API_KEY

GROQ_API_KEY
```

Provider selection should remain isolated from business logic.

---

## Core Modules

| Module                         | Responsibility          |
| ------------------------------ | ----------------------- |
| `backend/api/`                 | HTTP endpoints          |
| `backend/services/`            | Business workflows      |
| `backend/rag/agent.py`         | Agent orchestration     |
| `backend/rag/tool_registry.py` | Tool registration       |
| `backend/rag/retriever.py`     | Retrieval orchestration |
| `backend/rag/vector_store.py`  | ChromaDB implementation |
| `backend/rag/prompts.py`       | Prompt construction     |
| `backend/rag/citations.py`     | Citation generation     |
| `backend/models/`              | Shared data models      |

---

# 📐 Architecture Invariants

The following rules must never be violated:

1. Retrieval occurs exactly once per request.
2. `RetrievalResult` is the single source of truth for downstream components.
3. API endpoints remain thin.
4. Business logic belongs in Services.
5. Agent orchestrates tools but does not implement business logic.
6. Prompt Builder never performs retrieval.
7. Citation Builder never performs retrieval.
8. Vector Store owns provider-specific implementation.
9. Retriever owns retrieval orchestration only.
10. Dependencies always flow downward:

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

---

# 📚 Documentation Policy

Whenever changes affect architecture or behavior, update the appropriate documentation:

| Change             | Update            |
| ------------------ | ----------------- |
| Architecture       | `ARCHITECTURE.md` |
| Retrieval pipeline | `RAG_PIPELINE.md` |
| Technical decision | `DECISIONS.md`    |
| API contract       | `API_SPEC.md`     |
| Project scope      | `PROJECT_PLAN.md` |
| Agent behavior     | `AGENTS.md`       |

Documentation is considered part of the implementation and must remain synchronized with the codebase.
