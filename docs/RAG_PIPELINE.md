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

↓

BM25 Index (rebuilt in-memory)
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
(via Tool Registry)

↓

Retriever Tool (retrieve_context)

↓

Query Rewriter (if enabled)
├── Rewrites ambiguous/follow-up queries
├── Skips already-specific queries
└── Preserves original + rewritten query

↓

Retriever (Strategy Dispatch)
├── SimilarityStrategy
├── MMRStrategy
├── HybridStrategy
├── QueryRewriteStrategy (future)
└── RerankStrategy (future)

↓

Vector Store

↓

Cross-Encoder Reranker (if enabled)
├── Receives query + candidate chunks
├── Computes relevance scores
├── Reranks by cross-encoder score
└── Returns top-K reranked chunks

↓

RetrievalResult
      │
      ├────────────► Prompt Builder (uses original_query)
      │
      ├────────────► Citation Builder
      │
      └────────────► Agent

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

## Step 7 — Rebuild BM25 Index

Module

```
bm25.py / hybrid_retriever.py
```

Responsibilities

- Fetch all documents from Vector Store
- Build in-memory BM25 index
- Called after successful vector storage

The BM25 index is ephemeral - ChromaDB remains the single source of truth.

---

## Step 8 — Verify Indexing

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

Modules

```
agent.py / tool_executor.py
```

Responsibilities

- Receive conversation
- Decide which tool(s) to invoke via LLM tool-calling
- Coordinate multi-tool execution in an iterative loop
- Stream generated tokens and tool events

The Agent does **not** perform retrieval directly.

Tool execution loop:

1. LLM receives conversation state with available tools bound
2. LLM decides which tools to call (if any)
3. ToolExecutor executes each tool, collects results
4. Results added to ConversationState
5. LLM re-invoked with updated state
6. Loop continues until final answer or max iterations

---

## Step 3 — Tool Selection

Current Tools

- `retrieve_context` — Semantic retrieval from indexed documents
- `list_documents` — List all indexed documents with metadata
- `search_by_filename` — Find documents by filename (case-insensitive, partial match)

Future Tools

- summarize_document
- search_by_metadata
- web_search
- calculator

The ToolExecutor binds all registered tools to the LLM. The LLM determines which tools are needed to answer the request. Tool results are fed back into the conversation for the next LLM iteration.

---

## Step 4 — Retrieve Context

Modules

```
tool_registry.py / retriever.py

↓

retrieval_pipeline.py (composable stages)
    │
    ├── RewriteStage      (if rewrite_enabled)
    ├── ExpansionStage    (if expand_enabled)
    ├── RetrievalStage    (strategy + executor)
    ├── MergeStage        (dedup across queries)
    ├── RerankStage       (if reranker != "none")
    └── ResultBuilderStage

↓

retrieval_strategies.py

↓

vector_store.py + bm25.py
```

The retrieval tool supports two modes:

- **Single-query** (default): Rewrite → Retrieve → Rerank. Backward compatible.
- **Multi-query** (when `expand_enabled=True`): Rewrite → Expand → Parallel Retrieve → Merge → Rerank.

Responsibilities

The retrieval tool:

- receives the user query
- parses page references and metadata constraints from the query
- routes to the appropriate path (single-query or pipeline)
- returns a RetrievalResult

The retriever (single-query path):

- optionally rewrites the query via `get_query_rewriter()`
- selects a retrieval strategy via `get_strategy(search_type)`
- delegates to the strategy's `retrieve()` method
- strategies handle vector store and BM25 queries
- invokes reranker (if enabled) on retrieved chunks
- returns a RetrievalResult with retrieval_metadata

The Retrieval Pipeline (multi-query path):

- `RewriteStage`: optionally rewrites the query
- `ExpansionStage`: generates N diverse queries via `QueryExpander`
- `RetrievalStage`: executes retrieval for all queries via `RetrievalExecutor` (parallel threads)
- `MergeStage`: flattens, deduplicates, and merges results across queries
- `RerankStage`: optionally reranks merged results
- `ResultBuilderStage`: applies final top-k and builds metadata

Example

```python
RetrievalResult(
    original_query="How does RAG work?",
    retrieval_query="How does RAG work?",
    chunks=[
        RetrievedChunk(...),
        RetrievedChunk(...),
    ],
    retrieval_metadata={
        "strategy": "hybrid",
        "dense_results": 10,
        "bm25_results": 10,
        "duplicates_removed": 4,
        "fusion": "rrf",
        "rrf_k": 60,
        "reranker": "cross_encoder",
        "reranking_applied": true,
        "candidate_count": 20,
        "final_count": 6,
        "reranking_latency_ms": 42.3,
    },
)
```

The RetrievalResult becomes the single source of truth for the remainder of the request lifecycle.

No other component should perform another retrieval.

---

## Step 5 — Cross-Encoder Reranking (if enabled)

Module

```
reranker.py
```

Input

- User query (retrieval_query)
- Candidate chunks from retrieval strategy

Responsibilities

- Load cross-encoder model (lazy singleton)
- Compute relevance scores for (query, chunk) pairs via batch inference
- Rerank chunks by cross-encoder score (descending)
- Preserve all chunk metadata and content
- Return top-K reranked chunks

The Reranker:

- Runs after retrieval strategy, before prompt construction
- Never performs retrieval or accesses the vector store
- Only reorders existing chunks
- Gracefully falls back to original order on failure

---

## Step 6 — Build Prompt

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

### Prompt Structure

The Prompt Builder constructs a prompt with four clearly separated sections:

```
========================
SYSTEM INSTRUCTIONS
========================

[Grounding rules, citation guidance, behavior constraints]

========================
USER QUESTION
========================

[Original user question]

========================
RETRIEVED CONTEXT
========================

[Source 1]
Document: filename.pdf
Page: 7
Chunk: 15
Relevance Score: 0.1234

Content:
[chunk text]

--------------------------------------------------

[Source 2]
Document: another.pdf
Page: 3
Chunk: 2
Relevance Score: 0.2345

Content:
[chunk text]

========================
ANSWER
========================

Provide your answer based on the retrieved context above.
```

### Context Formatting

Every retrieved chunk includes user-friendly metadata:

- **Document**: Original filename (e.g., `architecture.pdf`)
- **Page**: Page number from PyPDFLoader (0-indexed)
- **Chunk**: Chunk index within the document
- **Relevance Score**: Cross-encoder or vector similarity score (4 decimal places)

Internal IDs (document_id, chunk_index as stored in ChromaDB) are never exposed in the prompt.

### Context Processing

Before formatting, the Prompt Builder applies:

1. **Deduplication**: Removes chunks with identical content (exact string match). Preserves the first occurrence (highest rank).
2. **Truncation**: If total context exceeds the configured character budget (default 8000 chars), removes lowest-ranked chunks from the end. Never truncates individual chunks.
3. **Ordering**: Preserves the retrieval/reranking order exactly. Never re-sorts chunks.

### Grounding Instructions

The SYSTEM INSTRUCTIONS section enforces:

- **Strict Grounding**: Answer ONLY using provided context
- **Explicit Uncertainty**: State "I don't know based on the available documents" when context is insufficient
- **No Hallucination**: Do not fabricate or infer unsupported facts
- **Precision Over Speculation**: Prefer direct, precise answers
- **Multi-Source Synthesis**: Combine information from multiple sources while preserving attribution
- **Terminology Preservation**: Keep technical terms from source documents

### Citation Guidance

The prompt instructs the LLM to:

- Reference sources naturally (e.g., "According to Document X..." or "Source 1 states...")
- Not cite every sentence, but make key claims attributable
- Never reference internal chunk IDs or hidden metadata fields

### Provider-Agnostic Design

The Prompt Builder produces plain text with no:

- Special tokens (`<|`, `<<SYS>>`, etc.)
- Model-specific formatting
- Provider detection logic

The same prompt works with any chat model (Groq, OpenAI, Anthropic, local models).

## Step 7 — Generate Response

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

## Step 8 — Build Source Citations

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

## Step 9 — Build Chat Result

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

---

# 5. Current Pipeline

```
Question

↓

Agent

↓

Tool Selection
(via Tool Registry)

↓

retrieve_context

↓

┌─────────────────────────────────────────────────┐
│             RETRIEVAL PIPELINE                   │
│  (single-query or multi-query)                  │
│                                                 │
│  RewriteStage (if rewrite_enabled)              │
│  ├── Rewrites ambiguous/follow-up queries       │
│  ├── Skips already-specific queries             │
│  └── Preserves original + rewritten query       │
│                                                 │
│  ExpansionStage (if expand_enabled)             │
│  ├── Generates N diverse queries                │
│  └── Uses LLM for multi-query expansion         │
│                                                 │
│  RetrievalStage                                 │
│  ├── Single query → direct retrieval            │
│  └── Multiple queries → parallel via executor   │
│                                                 │
│  MergeStage (multi-query only)                  │
│  ├── Flattens results from all queries          │
│  ├── Deduplicates by (doc_id, chunk_index)      │
│  └── Preserves first/highest-scored occurrence  │
│                                                 │
│  RerankStage (if reranker != "none")            │
│  ├── Cross-encoder relevance scoring            │
│  └── Reorders by relevance score                │
│                                                 │
│  ResultBuilderStage                             │
│  ├── Applies final top-k                        │
│  ├── Builds pipeline trace metadata             │
│  └── Returns RetrievalResult                    │
└─────────────────────────────────────────────────┘

↓

RetrievalResult
      │
      ├────────────► Prompt Builder (uses original_query)
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

- Hybrid Search (implemented)
- Query Rewriting (implemented)
- Cross-Encoder Reranking (implemented)
- Multi-query Retrieval (implemented)
- Context Compression (planned)
- Parent Document Retrieval (planned)
- Adaptive Chunking (planned)

---

## Agent

- Reflection (planned)
- Planning (planned)
- Multi-step reasoning (planned)
- Reasoning traces (planned)
- Tool routing (planned)
- Agent observability (planned)
- Confidence-aware tool selection (planned)

---

## Tools

- summarize_document (planned, Milestone 6)
- search_by_metadata (planned, Milestone 6)
- web_search (planned, Milestone 8)
- graph_search (planned, Milestone 9)
- entity_lookup (planned, Milestone 9)
- relationship_lookup (planned, Milestone 9)
- graph_explorer (planned, Milestone 9)
- knowledge_summary (planned, Milestone 9)

---

## Multimodal (Milestone 7)

- Image extraction from PDFs
- OCR for scanned PDFs
- Table understanding
- Chart understanding
- Figure understanding
- Multimodal prompt construction
- Visual reasoning
- Vision provider abstraction

---

## Web Search (Milestone 8)

- Search provider abstraction
- Document + Web answer synthesis
- Source attribution for web results
- Freshness-aware answers
- Intelligent fallback to web search

---

## GraphRAG (Milestone 9)

- Entity extraction and relationship extraction
- Knowledge graph construction and incremental updates
- Graph traversal and multi-hop retrieval
- Hybrid Vector + Graph retrieval
- Graph-aware reranking
- Internal wiki generation
- Graph search, entity lookup, relationship lookup, graph explorer, knowledge_summary tools

---

## Documents

- Collections
- Tags
- Metadata search

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

- Stores and retrieves vectors.
- Owns all ChromaDB-specific logic including similarity search, MMR, and metadata filtering.
- Never constructs prompts or performs orchestration.

BM25

- Provides in-memory lexical retrieval.
- Thread-safe index management.
- Rebuilt from Vector Store on document changes.
- Never persists to disk.

Retrieval Strategies

- Encapsulate specific retrieval algorithms.
- Selected via Strategy Pattern.
- Return RetrievalResult with metadata.
- New strategies can be added without modifying existing code.

Reranker

- Only reranks retrieved chunks.
- Never performs retrieval or accesses the vector store.
- Preserves all metadata and content.

Retriever

- Only performs retrieval orchestration.
- Selects retrieval strategy.
- Invokes reranker (if enabled).
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

Agent / ToolExecutor

- Only orchestrates tool execution and communicates with the LLM.
- Delegates tool implementation to individual tool modules.
- Never performs retrieval, prompt construction, or citation building.

ConversationState

- Only tracks state during a single request.
- Contains messages, tool calls, and retrieval results.
- Never performs business logic.

Responsibilities should never overlap.

---

# 9. Retrieval Invariant

Exactly one retrieval operation should occur for each user request.

The resulting RetrievalResult is shared across downstream components, including:

- Prompt Builder
- Citation Builder
- Agent

Reusing the RetrievalResult improves performance, ensures citation consistency, and maintains a clear separation of responsibilities.

Future retrieval enhancements (reranking, hybrid search, metadata filtering, query rewriting, etc.) should operate on the RetrievalResult rather than triggering additional searches.

---

# 10. Debugging Strategy

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

# 11. Future Pipeline: Web Search Integration

A planned extension for Milestone 8. This pipeline does not exist yet.

```
Question

↓

Agent

↓

retrieve_context

↓

RetrievalResult

↓

Prompt Builder → LLM

↓

No answer? (Agent detects insufficient context)
    │
    ├────────────► web_search tool
    │                   │
    │                   ▼
    │             Search Provider
    │             (SerpAPI / Bing / Brave / etc.)
    │                   │
    │                   ▼
    │             Web Search Results
    │                   │
    └───────────────────┘
            │
            ▼
    Merged Context (Document + Web)
            │
            ▼
    Prompt Builder → LLM → Answer with citations
```

Key design principles:

- **Web search is an Agent Tool**, not part of the Retriever. This keeps retrieval dedicated to local knowledge.
- **The Agent decides** when local context is insufficient and web search is needed.
- **Document and web results** are merged before prompt construction for coherent synthesis.
- **Web sources include attribution** (URL, title, snippet, timestamp).
- **Configurable** via settings to enable/disable web search per request.

---

# 12. Future Pipeline: Multimodal Indexing

A planned extension for Milestone 7. This pipeline does not exist yet.

```
PDF

↓

Multimodal Extraction
├── Text extraction (existing)
├── Image extraction (planned)
├── OCR for scanned pages (planned)
├── Table extraction (planned)
├── Chart extraction (planned)
└── Figure extraction (planned)

↓

Multimodal Processing
├── Text → Text embeddings (existing provider)
├── Images → Image embeddings (planned, via vision provider)
├── Tables → Table representations (planned)
├── Charts → Chart representations (planned)
└── OCR text → Text embeddings (existing provider)

↓

Vector Store (single unified index)
    │
    ▼
RetrievalResult (modality-agnostic)
    │
    ├────────► Prompt Builder (multimodal prompts)
    │
    ├────────► Citation Builder (visual + text citations)
    │
    └────────► Agent (visual reasoning)
```

Key design principles:

- **Unified retrieval**: Regardless of modality (text, image, table, chart, OCR), the Retriever returns a single `RetrievalResult`.
- **Modality-agnostic downstream**: Prompt Builder and Agent receive the same `RetrievalResult` structure. Only the Prompt Builder changes to construct multimodal prompts.
- **Provider-agnostic vision**: Vision models are accessed through `providers/vision.py` abstraction.
- **Modular extraction**: Each extraction type lives in its own module.
- **Metadata preserves modality**: Each `RetrievedChunk` includes a `source_type` field (text, image, table, chart, ocr) so downstream components can handle it appropriately.

---

# 13. Future Pipeline: GraphRAG Integration

A planned extension for Milestone 9. This pipeline does not exist yet.

## GraphRAG Indexing Pipeline

Runs after document indexing to build the knowledge graph.

```
Documents

↓

Entity Extraction
├── Named entities (people, organizations, APIs, classes)
├── Concepts and topics
└── Document references

↓

Relationship Extraction
├── Entity-to-entity relationships
├── Document-to-entity links
└── Cross-document connections

↓

Knowledge Graph

↓

Graph Database
(node persistence, edge persistence, indexing)
```

## GraphRAG Execution Pipeline

Graph retrieval augments — not replaces — the existing vector retrieval pipeline.

```
Question

↓

Agent

↓

retrieve_context (existing)

↓

Retriever (Strategy Dispatch)
├── SimilarityStrategy
├── MMRStrategy
├── HybridStrategy (Dense + BM25)
└── Cross-Encoder Reranker (if enabled)

↓

RetrievalResult (vector context)

↓

graph_search (new tool)
├── Entity lookup in Knowledge Graph
├── Relationship traversal
├── Multi-hop path retrieval
└── Neighbor expansion

↓

Graph Results (entities, relationships, paths)

↓

Hybrid Graph + Vector Retrieval
(merge graph context into RetrievalResult)

↓

Prompt Builder → LLM → Response
```

Key design principles:

- **GraphRAG augments vector retrieval**: Graph retrieval provides additional context alongside dense and lexical retrieval. It does not replace the existing pipeline.
- **Unified RetrievalResult**: Graph-retrieved context is merged into the existing `RetrievalResult` abstraction rather than introducing a separate downstream data model.
- **Prompt Builder remains unaware**: The Prompt Builder does not need to know whether retrieved context originated from vectors or graph traversal. It formats the unified `RetrievalResult` as before.
- **Agent decides tool usage**: The Agent selects `graph_search` when relationship-based questions are detected (e.g., "what depends on X?", "who implements Y?").
- **Composable**: Graph retrieval is composable with existing retrieval strategies and can be enabled or disabled per request.

---

# 14. Future Vision

The pipeline should evolve into a general-purpose Agentic RAG engine.

Future capabilities should be introduced by adding new tools rather than redesigning the architecture.

Examples include

- Knowledge Graph lookup (planned, Milestone 9)
- SQL querying
- Document summarization
- Multi-agent collaboration
- Long-term memory

The surrounding application should remain unchanged as these capabilities are added.