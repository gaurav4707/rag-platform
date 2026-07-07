# RAG_PIPELINE.md

# Agentic Retrieval-Augmented Generation (Agentic RAG) Pipeline

# 1. Purpose

This document describes the complete Agentic RAG execution pipeline.

It explains how documents are indexed, how user queries are processed, how the Agent interacts with tools, and how responses are streamed back to the user.

This document serves as the technical reference for the application's intelligence layer.

---

# 2. Pipeline Overview

The system consists of two independent pipelines.

## Indexing Pipeline

Runs once whenever a PDF is uploaded.

```
PDF

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

## Agent Execution Pipeline

Runs for every user question.

```
User Question

↓

Chat API

↓

RAG Service

↓

Agent

↓

Tool Selection

↓

Retriever Tool

↓

Retriever

↓

Vector Store

↓

RetrievalResult
      │
      ├────────────► Prompt Builder
      │
      └────────────► Citation Builder

↓

LLM

↓

Streaming Response

↓

ChatResult

↓

API Response
```

---

# 3. Indexing Pipeline

The indexing pipeline prepares uploaded documents for semantic retrieval.

It executes exactly once for every uploaded PDF.

---

## Step 1 — Upload PDF

Responsibilities

- Validate PDF
- Reject empty files
- Generate UUID
- Save original PDF

Output

```
storage/uploads/{document_id}.pdf
```

---

## Step 2 — Load Document

Module

```
loader.py
```

Responsibilities

- Read PDF
- Extract text
- Preserve page metadata

Output

```
List[Document]
```

The loader never performs:

- chunking
- embeddings
- retrieval

---

## Step 3 — Enrich Metadata

Every page receives

- document_id
- filename

Metadata is preserved throughout the pipeline.

---

## Step 4 — Split Document

Module

```
splitter.py
```

Responsibilities

- Split text
- Preserve overlap
- Preserve metadata
- Assign chunk_index

Output

```
List[Document]
```

---

## Step 5 — Generate Embeddings

Module

```
embeddings.py
```

Responsibilities

- Convert text into embedding vectors

The embedding provider should be replaceable without affecting the rest of the system.

---

## Step 6 — Store Vectors

Module

```
vector_store.py
```

Responsibilities

- Store vectors
- Store metadata
- Store chunk text

Stored metadata includes

- document_id
- filename
- page
- chunk_index

---

## Step 7 — Verify Indexing

Return

```json
{
  "document_id": "...",
  "filename": "...",
  "status": "indexed"
}
```

---

# 4. Agent Execution Pipeline

This pipeline executes for every user question.

Unlike traditional RAG, the LLM acts as an Agent capable of selecting tools.

For the MVP the Agent has one tool:

```
retrieve_context
```

Future milestones will introduce additional tools.

---

## Step 1 — Receive User Question

Example

```
How do transformers work?
```

The Chat API forwards the request to the RAG Service.

---

## Step 2 — Agent Receives Request

Module

```
agent.py
```

Responsibilities

- Receive conversation
- Decide which tool(s) to invoke
- Coordinate tool execution
- Stream generated tokens

The Agent does **not** perform retrieval directly.

---

## Step 3 — Tool Selection

Current Tool

```
retrieve_context
```

Future Tools

- list_documents
- summarize_document
- search_by_metadata
- search_by_filename
- web_search
- calculator

The Agent determines which tools are needed to answer the request.

---

## Step 4 — Retrieve Context

Modules

```
tools.py

↓

retriever.py

↓

vector_store.py
```

Responsibilities

The retrieval tool

- receives the user query
- invokes the retriever
- returns a RetrievalResult

The retriever

- queries the vector store
- ranks results
- preserves metadata
- returns retrieved chunks with their scores

Example

```python
RetrievalResult(
    query="How does RAG work?",
    chunks=[
        RetrievedChunk(...),
        RetrievedChunk(...),
    ],
)
```

The RetrievalResult becomes the single source of truth for the remainder of the request lifecycle.

No other component should perform another retrieval.

---

## Step 5 — Build Prompt

Module

```
prompts.py
```

Input

- User question
- RetrievalResult

Responsibilities

- Format retrieved chunks
- Format metadata
- Build the final prompt/messages for the LLM

The Prompt Builder never performs retrieval.

It consumes the RetrievalResult produced by the retriever.

---

## Step 6 — Generate Response

Module

```
agent.py
```

Responsibilities

- send prompt to the configured LLM
- stream tokens
- collect tool execution metadata

Current Provider

```
Groq
```

The provider may change without affecting the surrounding pipeline.

---

## Step 7 — Build Source Citations

Module

```
citations.py
```

Input

- RetrievalResult

Responsibilities

- Convert retrieved chunk metadata into API source objects
- Preserve filename, page, document ID, and retrieval score

The Citation Builder reuses the same RetrievalResult that was used to construct the prompt.

No additional vector search should occur.

This guarantees that citations always correspond to the exact documents used by the LLM.

---

## Step 8 — Build Chat Result

The Agent returns a ChatResult containing

- generated answer
- source citations
- tool execution metadata

Example

```python
ChatResult(
    answer="...",
    sources=[...],
    tool_calls=[...],
)
```

The Chat API serializes the ChatResult into the public HTTP response.

This separation keeps the API layer independent of the Agent implementation.

---

# 5. Current Pipeline

```
Question

↓

Agent

↓

Tool Selection

↓

retrieve_context

↓

Retriever

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

---

# 6. Planned Improvements

## Retrieval

- Hybrid Search
- Query Rewriting
- Metadata Filtering
- MMR
- Multi-query Retrieval
- Context Compression
- Parent Document Retrieval

---

## Ranking

- Cross Encoder Reranking
- Reciprocal Rank Fusion
- Score Thresholding

---

## Agent

- Multiple tools
- Reflection
- Planning
- Multi-step reasoning
- Tool routing
- Tool retries

---

## Documents

- Collections
- Tags
- Metadata search
- OCR

---

## Generation

- Better prompts
- Structured outputs
- Confidence estimation
- Rich citations

---

# 7. Design Principles

The pipeline should always remain

- Modular
- Observable
- Replaceable
- Provider-agnostic
- Tool-oriented

Every stage should have one primary responsibility.

---

# 8. Pipeline Rules

Loader

- Only loads documents.

Splitter

- Only splits documents.

Embeddings

- Only generates vectors.

Vector Store

- Only stores and retrieves vectors.

Retriever

- Only performs retrieval.
- Produces a RetrievalResult.
- Never constructs prompts.

Prompt Builder

- Only constructs prompts.
- Never performs retrieval.

Citation Builder

- Only converts retrieved metadata into source citations.
- Never queries the vector store.

Tools

- Only expose capabilities to the Agent.
- Never duplicate retrieval already performed by the retriever.

Agent

- Only orchestrates tool execution and communicates with the LLM.

Responsibilities should never overlap.

---

# Retrieval Invariant

Exactly one retrieval operation should occur for each user request.

The resulting RetrievalResult is shared across downstream components, including:

- Prompt Builder
- Citation Builder
- Agent

Reusing the RetrievalResult improves performance, ensures citation consistency, and maintains a clear separation of responsibilities.

Future retrieval enhancements (reranking, hybrid search, metadata filtering, query rewriting, etc.) should operate on the RetrievalResult rather than triggering additional searches.

---

# 9. Debugging Strategy

Debug the pipeline in execution order.

1. Was the PDF stored?
2. Was text extracted correctly?
3. Were chunks created correctly?
4. Were embeddings generated?
5. Did retrieval return relevant chunks?
6. Did the Agent choose the correct tool?
7. Was the prompt built correctly?
8. Did the LLM receive the expected prompt?
9. Were citations built correctly?
10. Were tool calls recorded correctly?

Investigate one stage at a time.

---

# 10. Future Vision

The pipeline should evolve into a general-purpose Agentic RAG engine.

Future capabilities should be introduced by adding new tools rather than redesigning the architecture.

Examples include

- Web Search
- Knowledge Graph lookup
- SQL querying
- OCR
- Document summarization
- Multi-agent collaboration
- Long-term memory

The surrounding application should remain unchanged as these capabilities are added.