# RAG_PIPELINE.md

# Retrieval-Augmented Generation (RAG) Pipeline

## 1. Purpose

This document describes how data flows through the Retrieval-Augmented Generation (RAG) system.

It serves as the technical reference for the core intelligence of the application.

Any modifications to the retrieval pipeline should be documented here.

---

# 2. Pipeline Overview

The application follows a two-phase architecture:

1. **Indexing Pipeline** (performed once when a PDF is uploaded)
2. **Retrieval Pipeline** (performed every time the user asks a question)

```text
                 PDF Upload
                      │
                      ▼
                Indexing Pipeline
                      │
                      ▼
                 Chroma Vector DB

                      ▲
                      │
              Retrieval Pipeline
                      ▲
                      │
                User Question
```

---

# 3. Indexing Pipeline

The indexing pipeline prepares documents for future retrieval.

It runs once for every uploaded PDF.

## Step 1 — Upload PDF

Input:

```text
research-paper.pdf
```

The file is uploaded through the Upload API.

The original PDF is saved to `storage/uploads/{document_id}.pdf`.

Responsibilities:

* Validate file type (PDF only)
* Reject empty files
* Generate UUID document ID
* Save original file to disk

Output:

```text
Stored PDF at storage/uploads/{document_id}.pdf
```

---

## Step 2 — Load Document

Module:

```text
loader.py
```

Tool: `PyPDFLoader`

Responsibilities:

* Read PDF
* Extract text per page
* Preserve metadata (page number, source path)

Output:

```text
List[Document] — one per page, with metadata.source and metadata.page
```

The loader should not:

* Split text
* Generate embeddings
* Perform retrieval

---

## Step 3 — Enrich Metadata

Before splitting, each Document's metadata is enriched with:

* `document_id` — UUID string, identifies the uploaded document
* `filename` — original filename from the upload

This metadata is preserved through splitting and stored in ChromaDB alongside each chunk.

---

## Step 4 — Split Document

Module:

```text
splitter.py
```

Tool: `RecursiveCharacterTextSplitter`

Parameters from `config.py`:

* `CHUNK_SIZE = 1000` characters
* `CHUNK_OVERLAP = 200` characters
* `add_start_index = True` — tracks position in original text

Responsibilities:

* Split document into chunks
* Preserve overlap for context continuity
* Preserve all metadata from parent document

After splitting, each chunk additionally receives:

* `chunk_index` — ordinal position within the document (0-based)

Output:

```text
List[Document] — chunks with inherited metadata
```

---

## Step 5 — Generate Embeddings

Module:

```text
embeddings.py
```

Model: `BAAI/bge-base-en-v1.5` via HuggingFaceEmbeddings

Responsibilities:

* Convert each chunk into a numerical vector (768 dimensions)

The embedding module is provider-agnostic and can be replaced without affecting other components.

---

## Step 6 — Store Vectors

Module:

```text
vector_store.py
```

Database: ChromaDB (PersistentClient)

Storage: `storage/chroma_langchain_db/chroma.sqlite3`

Responsibilities:

* Store embeddings
* Store chunk text (for retrieval)
* Store metadata (document_id, filename, page, chunk_index)

Each Chroma entry contains:

| Field         | Source              |
|---------------|---------------------|
| `page_content`| Chunk text          |
| `document_id` | From metadata       |
| `filename`    | From metadata       |
| `page`        | From PyPDFLoader    |
| `chunk_index` | From splitter       |
| `source`      | File path           |

### Persistence

ChromaDB's PersistentClient auto-persists all data to SQLite on every write operation. No explicit `persist()` call is needed.

The `_collection` instance is cached as a module-level singleton to avoid creating multiple connections to the same database during the application lifecycle.

### Atomic Rollback

If any step in the indexing pipeline fails:

1. The saved PDF file is removed from `storage/uploads/`
2. Vector entries for that `document_id` are deleted from ChromaDB
3. The error is propagated to the API layer

This prevents orphaned files or ghost vectors.

---

## Step 7 — Verify Indexing

Output:

```json
{
  "document_id": "uuid-string",
  "filename": "research.pdf",
  "status": "indexed"
}
```

---

# 4. Retrieval Pipeline

The retrieval pipeline runs for every user question.

---

## Step 1 — User Question

Example:

```text
"What are the advantages of ReAct?"
```

The question is sent to the Chat API.

---

## Step 2 — Build Prompt Context

Module:

```text
prompts.py
```

The `prompt_with_context` middleware:

1. Extracts the last user message from the conversation state
2. Calls `similarity_search(query, TOP_K=8)` to retrieve relevant chunks
3. Deduplicates by page content
4. Inserts retrieved content into the system prompt

---

## Step 3 — Retrieve Context (Tool)

Module:

```text
retriever.py
```

The `retrieve_context` tool (used by the agent):

1. Receives the user query
2. Calls `similarity_search(query, k=2)` — a focused retrieval
3. Returns serialized content for the LLM, with Document objects as artifact

---

## Step 4 — Generate Response

Module:

```text
rag_agent.py
```

Process:

1. Agent receives the prompt with context (from Step 2)
2. Agent may call the retrieve_context tool (from Step 3)
3. LLM generates the answer grounded in the retrieved context
4. Tokens are streamed back to the API

Current LLM:

```text
groq:llama-3.1-8b-instant
```

---

## Step 5 — Build Source Citations

Module:

```text
api/chat.py
```

After the LLM response is complete, the chat endpoint:

1. Runs an independent `similarity_search_with_scores(query, k=4)`
2. Extracts metadata from each returned document
3. Builds `SourceItem` objects:

```json
{
  "document": "research.pdf",
  "page": 7,
  "document_id": "uuid-string",
  "score": 0.4521
}
```

Note: The score is a raw distance value from ChromaDB (lower = more similar). This will be replaced with a normalized relevance score in a future iteration.

---

## Step 6 — Return Response

Final response includes:

* `answer` — LLM-generated text
* `sources` — list of SourceItem with metadata
* `tool_calls` — debug information about tool invocations

---

# 5. Current Pipeline

```text
PDF

↓

Loader (PyPDFLoader)

↓

Metadata Enrichment (document_id, filename)

↓

RecursiveCharacterTextSplitter

↓

HuggingFace Embeddings (BGE)

↓

ChromaDB (PersistentClient)

────────────────────────────

Question

↓

Prompt Builder (TOP_K=8)

↓

Agent

  ├── Retriever Tool (k=2)

  └── LLM (groq:llama-3.1-8b-instant)

↓

Source Builder (similarity_search_with_scores, k=4)

↓

Answer + Sources + Tool Calls
```

---

# 6. Planned Improvements

The retrieval pipeline should evolve incrementally.

Planned enhancements include:

## Retrieval

* Hybrid Search
* MMR Retrieval
* Query Rewriting
* Multi-query Retrieval
* Context Compression

---

## Ranking

* Cross-Encoder Reranking
* Reciprocal Rank Fusion
* Score Threshold Filtering

---

## Documents

* Multiple PDFs
* Metadata Filtering
* Collections
* Tags

---

## Generation

* Better prompt templates
* Structured output
* Citation improvements
* Answer confidence indicators

---

# 7. Design Principles

The RAG pipeline should remain:

* Modular
* Replaceable
* Observable
* Testable

Each stage should have one responsibility.

Every stage should be independently replaceable without affecting unrelated components.

---

# 8. Pipeline Rules

The following rules should always hold:

* Loader only loads documents.
* Splitter only splits documents.
* Embedding module only generates embeddings.
* Vector store only manages vectors.
* Retriever only retrieves context.
* Prompt builder only builds prompts.
* Agent only communicates with the LLM.

Responsibilities should never overlap.

---

# 9. Debugging Strategy

When investigating incorrect answers, debug the pipeline in order:

1. Was the PDF loaded correctly?
2. Was the text extracted correctly?
3. Were chunks created appropriately?
4. Were embeddings generated successfully?
5. Did retrieval return relevant chunks?
6. Was the prompt constructed correctly?
7. Did the LLM receive the expected context?
8. Were sources returned correctly?

Debug one stage at a time.

---

# 10. Future Goal

The RAG pipeline should evolve into a provider-agnostic engine.

Changing any of the following should require minimal code changes:

* LLM
* Embedding model
* Vector database
* Retrieval strategy
* Prompt template

The surrounding application should remain unchanged when individual pipeline components are replaced.
