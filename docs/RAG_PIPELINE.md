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

The original PDF is stored locally.

Responsibilities:

* Validate file type
* Generate document ID
* Save original file

Output:

```text
Stored PDF
```

---

## Step 2 — Load Document

Module:

```text
loader.py
```

Responsibilities:

* Read PDF
* Extract text
* Preserve metadata

Output:

```text
Document
```

The loader should not:

* Split text
* Generate embeddings
* Perform retrieval

---

## Step 3 — Split Document

Module:

```text
splitter.py
```

Responsibilities:

* Split document into chunks
* Preserve overlap
* Preserve metadata

Example:

```text
Page 1

↓

Chunk 1
Chunk 2
Chunk 3
```

Current strategy:

* Recursive Character Text Splitter

Future strategies may include:

* Semantic chunking
* Markdown-aware chunking
* Token-aware chunking

---

## Step 4 — Generate Embeddings

Module:

```text
embeddings.py
```

Responsibilities:

Convert each chunk into a numerical vector.

Example:

```text
Chunk

↓

Embedding Vector
```

Current embedding model:

* Gemini Embeddings

Future providers:

* Hugging Face
* OpenAI
* Nomic
* Local models

The embedding module should be replaceable without affecting the rest of the system.

---

## Step 5 — Store Vectors

Module:

```text
vector_store.py
```

Responsibilities:

Store:

* Embeddings
* Chunk text
* Metadata

Current implementation:

```text
ChromaDB
```

Future implementations may include:

* FAISS
* Qdrant
* Pinecone
* Milvus

The rest of the application should not depend on a specific vector database.

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

## Step 2 — Retrieve Relevant Chunks

Module:

```text
retriever.py
```

Responsibilities:

* Search vector database
* Find most relevant chunks
* Remove duplicates if necessary

Current retrieval:

```text
Similarity Search
```

Future improvements:

* MMR (Maximal Marginal Relevance)
* Hybrid Search
* Metadata Filtering
* Query Expansion
* Parent Document Retrieval

The retriever should only retrieve documents.

It should never construct prompts.

---

## Step 3 — Build Prompt

Module:

```text
prompts.py
```

Responsibilities:

Create the final prompt for the LLM.

The prompt should contain:

* System instructions
* Retrieved context
* User question

Example structure:

```text
System Instructions

Retrieved Context

User Question
```

The prompt builder should never perform retrieval.

---

## Step 4 — Generate Response

Module:

```text
agent.py
```

Responsibilities:

* Call the LLM
* Stream tokens
* Return final response

Current LLM:

* Gemini Flash

Future providers:

* OpenAI
* Anthropic
* Local models
* OpenRouter

---

## Step 5 — Return Sources

The final response should include:

* Answer
* Source chunks
* Document names
* Page numbers (when available)

This enables users to verify where information originated.

---

# 5. Current Pipeline

```text
PDF

↓

Loader

↓

Recursive Splitter

↓

Gemini Embeddings

↓

ChromaDB

────────────────────────────

Question

↓

Retriever

↓

Prompt Builder

↓

Gemini Flash

↓

Answer + Sources
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
