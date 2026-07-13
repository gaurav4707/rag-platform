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
            +-------------------+-------------------+
            |                                       |
     Document Service                          Chat Service
            |                                       |
            +-------------------+-------------------+
                                |
                          Agentic RAG Engine
                                |
                  +-------------+-------------+
                  |                           |
               Agent                       Prompt Builder
                  |
            Tool Registry
                  |
     +------------+------------+--------------+
     |                         |               |
 Retriever Tool           Future Tools      Future Tools
 (retrieve_context)      (Web Search,       (Calculator,
                         Metadata, etc.)    Summarizer...)
     |
 Retriever (Strategy Dispatch)
     |
 +---+---+---+---+---+---+
 |   |   |   |   |   |   |
 ▼   ▼   ▼   ▼   ▼   ▼   ▼
Similarity MMR Hybrid Query Rewrite Rerank Future
     |
 Query Rewriter (if enabled)
     |
 Vector Store (ChromaDB)
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
│   ├── retrieval_strategies.py
│   ├── bm25.py
│   ├── hybrid_retriever.py
│   ├── reranker.py
│   ├── tool_registry.py
│   ├── agent.py
│   ├── prompts.py
│   ├── citations.py
│   └── query_rewriter.py
│
├── evaluation/
│   ├── __init__.py
│   ├── README.md
│   ├── cli.py
│   ├── evaluator.py
│   ├── dataset.py
│   ├── metrics.py
│   ├── models.py
│   └── reports/
│
├── models/
│   ├── schemas.py
│   └── rag_models.py
│
├── tests/
│   ├── __init__.py
│   ├── conftest.py
│   └── test_evaluation_metrics.py
│   └── test_retriever.py
│
├── storage/
│   ├── uploads/
│   └── chroma_langchain_db/
│
├── utils/
│

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

↓

BM25 Index (rebuilt in-memory)
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

Retriever Tool (retrieve_context)

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

RetrievalResult
      │
      ├────────────► Prompt Builder (prompts.py)
      │                  │
      │                  ▼
      │            Formatted Prompt
      │                  │
      │                  ▼
      └────────────► LLM ──► Answer
      │
      ├────────────► Citation Builder
      │
      └────────────► Agent

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

BM25 Index (rebuilt in-memory)

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
- Retrieving all documents for BM25 index building

Examples:

- add_documents()
- delete_document()
- similarity_search_with_scores()
- similarity_search_with_scores_filtered()
- mmr_search_with_scores()
- get_all_documents()
- list_documents()

The vector store is the only module that imports Chroma or generates embeddings.

---

## bm25.py

Responsible for:

- In-memory BM25 index (rank-bm25)
- Building index from Vector Store documents
- Lexical search with BM25 scoring
- Thread-safe index management
- Index rebuild, refresh, and invalidation

No persistence - ChromaDB remains the single source of truth.

---

## query_rewriter.py

Responsible for rewriting user queries into more effective search queries
for vector retrieval.

- Defines `BaseQueryRewriter` protocol for provider-agnostic design
- Implements `LLMQueryRewriter` using the project's configured LLM
- Implements `NoOpQueryRewriter` for when rewriting is disabled
- Provides `get_query_rewriter()` factory function

The Query Rewriter:
- Runs before retrieval strategy selection
- Preserves both original and rewritten queries in RetrievalResult
- Never performs retrieval or accesses the vector store
- Logs rewrite decisions for debugging

---

## retrieval_strategies.py

Implements the Strategy Pattern for retrieval:

- **SimilarityStrategy**: Dense vector similarity search
- **MMRStrategy**: Maximum Marginal Relevance search
- **HybridStrategy**: Dense + BM25 with Reciprocal Rank Fusion (RRF)

Each strategy:
- Takes a query and RetrievalConfig
- Returns a RetrievalResult with retrieval_metadata

Future strategies:
- QueryRewriteStrategy
- RerankStrategy

---

## reranker.py

Responsible only for reranking retrieved chunks by relevance to the query.

- Defines `BaseReranker` protocol for provider-agnostic design
- Implements `CrossEncoderReranker` using a local Hugging Face cross-encoder model (default: `cross-encoder/ms-marco-MiniLM-L-6-v2`)
- Implements `NoOpReranker` for when reranking is disabled
- Provides `get_reranker()` factory function

The Reranker:
- Runs after retrieval strategy execution (on the RetrievalResult)
- Never performs retrieval or accesses the vector store
- Preserves all chunk metadata and content, only reorders
- Lazy-loads model as singleton for efficiency
- Logs reranking decisions and latency

---

## retriever.py

Responsible only for retrieval orchestration.

It should:

- Select a retrieval strategy via `get_strategy()`
- Call the strategy's `retrieve()` method
- Invoke reranker (if enabled) on the retrieved chunks
- Return a RetrievalResult

It must never:

- Import Chroma
- Generate embeddings
- Interact with the LLM
- Build prompts
- Build citations

The RetrievalResult is the single source of truth for downstream components.

---

## retrieval_config.py

Defines the `RetrievalConfig` dataclass for configuring retrieval behavior.

Fields:

- top_k: int (default 4)
- search_type: "similarity" | "mmr" | "hybrid" (default "hybrid")
- score_threshold: float | None
- fetch_k: int (default 20)
- lambda_mult: float (default 0.5)
- metadata_filter: dict | None
- query_rewrite: "none" | "llm" (default "none")
- query_rewriting_enabled: bool (default True)

Hybrid-specific:
- dense_top_k: int (default 10)
- bm25_top_k: int (default 10)
- final_top_k: int (default 6)
- rrf_k: int (default 60)
- hybrid_enabled: bool (default True)

Reranking settings:
- reranker: "none" | "cross_encoder" (default "cross_encoder")
- reranker_top_k: int (default 6)

Provides a `DEFAULT_RETRIEVAL_CONFIG` singleton.

---

## hybrid_retriever.py

Utility module for BM25 index management:

- rebuild_bm25_index()
- refresh_bm25_index()
- invalidate_bm25_index()
- get_bm25_stats()

Actual hybrid retrieval logic is in `retrieval_strategies.py` (HybridStrategy).

---

## prompts.py

Responsible only for prompt construction.

Consumes:

- user question
- RetrievalResult

Produces:

- Formatted prompt string for the LLM
- LangChain-compatible messages list

The Prompt Builder never performs retrieval. It formats retrieved context into a structured prompt with clearly separated sections:

1. **SYSTEM INSTRUCTIONS** — Grounding rules, citation guidance, behavior constraints
2. **USER QUESTION** — The original user question
3. **RETRIEVED CONTEXT** — Formatted chunks with metadata (filename, page, chunk index, relevance score)
4. **ANSWER** — Instruction to generate the response

Key behaviors:

- **Deduplication**: Removes duplicate chunks by exact content match before formatting
- **Context Length Management**: Truncates from the end to fit within configured character budget, preserving retrieval ranking order
- **Provider-Agnostic**: Produces plain text compatible with any chat model
- **Metadata Display**: Shows user-friendly metadata (filename, page, chunk) — never exposes internal IDs
- **Clear Separation**: Uses distinct section markers and chunk separators for reliable parsing

The Prompt Builder is invoked by the Agent after the retrieve_context tool returns a RetrievalResult.

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

- Orchestrating the RAG workflow: retrieve → build prompt → generate answer
- Calling the retrieve_context tool via the Tool Registry
- Building the prompt using the Prompt Builder (prompts.py)
- Sending the prompt to the LLM for answer generation
- Streaming the LLM response
- Building citations from the RetrievalResult via the Citation Builder
- Assembling the ChatResult (answer + citations + tool_calls)

The Agent:

- Invokes retrieve_context tool to get RetrievalResult
- Calls build_prompt(question, retrieval_result) from Prompt Builder
- Streams model output using the LLM's native streaming
- Never queries the vector store directly
- Contains no retrieval logic — that lives in retriever.py

---

## api/errors.py

Responsible for standardized API errors.

---

## RetrievalResult

The RetrievalResult is a shared data model produced by the retriever.

It represents the outcome of a single retrieval operation and is reused throughout the request lifecycle.

It now includes optional `retrieval_metadata` for debugging and evaluation:

```python
@dataclass
class RetrievalResult:
    original_query: str
    retrieval_query: str
    chunks: list[RetrievedChunk]
    retrieval_metadata: dict = field(default_factory=dict)  # strategy, counts, etc.
```

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

- Hybrid Search (implemented)
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

# 11. Offline Evaluation

The `backend/evaluation/` module provides an **offline development tool** for measuring retrieval quality.

## Purpose

- Measure retrieval quality before and after retrieval improvements
- Test chunking changes, query rewriting, hybrid retrieval, reranking
- Compare retrieval configurations without affecting production

## Architecture Separation

```
Developer
   |
Evaluation CLI
   |
Retriever (reuses existing rag/retriever.py)
   |
Vector Store
   |
Metrics Report
```

**Strictly separate from production:**
- No FastAPI routes
- No Service layer integration
- No Agent tool integration
- No runtime pipeline changes
- No database modifications

## Components

| Module | Responsibility |
|--------|----------------|
| `models.py` | Evaluation data structures (EvaluationQuery, RetrievalEvaluationResult, EvaluationReport) |
| `dataset.py` | Load/save JSON evaluation datasets |
| `metrics.py` | Precision@K, Recall@K, Hit Rate, MRR, NDCG, MAP, F1 |
| `evaluator.py` | Orchestration: load dataset → run retriever → calculate metrics → generate report |
| `cli.py` | Command-line interface for running evaluations |

## Usage

```bash
python -m backend.evaluation.cli \
    --dataset backend/evaluation/data/test_queries.json \
    --top-k 5 \
    --search-type hybrid
```

## Reports

Saved to `backend/evaluation/reports/evaluation_<timestamp>.json`:

```json
{
  "timestamp": "2024-01-15T10:30:00",
  "total_queries": 10,
  "top_k": 5,
  "metrics": {
    "precision@5": 0.72,
    "recall@5": 0.81,
    "hit_rate@5": 0.90,
    "mrr": 0.76,
    "map": 0.68
  },
  "results": [...]
}
```

---

# 10. Architecture Constraints

The following rules should not be violated without recording an architectural decision:

- The frontend must never contain backend logic.
- API endpoints must remain thin.
- Business logic belongs in services.
- Agent orchestration belongs inside the RAG layer.
- Retrieval orchestration belongs inside retriever.py.
- Retrieval implementation (ChromaDB calls, embeddings) belongs inside vector_store.py.
- BM25 lexical retrieval belongs inside bm25.py.
- Tool definitions belong inside tool_registry.py.
- Prompt construction belongs inside prompts.py.
- Storage must never contain business logic.
- Every module should have one primary responsibility.
- New capabilities should extend the architecture instead of bypassing it.
- Exactly one retrieval operation should occur for each user request.
- All downstream components must reuse the RetrievalResult instead of issuing additional vector store queries.
- Retrieval strategies are selected via the Strategy Pattern - new strategies can be added without modifying existing code.
- BM25 index is in-memory only; ChromaDB remains the single source of truth.
