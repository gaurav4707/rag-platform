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
   - Reflection, planning, multi-step reasoning
   - Advanced retrieval (parent document, context compression, multi-query)
   - New tools (summarize_document, search_by_metadata)
   - Multiple LLM and embedding providers
   - Agent observability and reasoning traces
   - Conversation memory

7. Multimodal Intelligence
   - Image extraction, OCR, table/chart/figure understanding
   - Multimodal prompt construction
   - Visual reasoning and citations
   - Vision provider abstraction
   - Unified multimodal retrieval

8. Web Search & External Knowledge
   - web_search tool with search provider abstraction
   - Intelligent fallback between document and web search
   - Document + Web answer synthesis
   - Confidence-aware tool selection
   - Configurable enable/disable

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

# ADR-015: Encapsulation of Provider-Specific Retrieval Logic

### Status

Accepted

---

### Context

Earlier versions of the retriever module directly imported and used ChromaDB-specific APIs including `Chroma`, `maximal_marginal_relevance`, `_results_to_docs`, and embedding generation via `embeddings.embed_query()`.

The retriever had three concerns mixed into one module:

- Retrieval orchestration (strategy selection, result construction)
- Provider-specific implementation (Chroma queries, MMR, embedding calls)
- Collection lifecycle management (`_collection` cache)

This made it difficult to:

- Test retrieval strategies independently of ChromaDB
- Switch to a different vector database
- Reason about responsibilities at a glance
- Add new retrieval strategies without touching Chroma internals

---

### Decision

Provider-specific retrieval logic is encapsulated entirely within `vector_store.py`.

`retriever.py` is responsible only for:

- Selecting a retrieval strategy (similarity or MMR)
- Calling the Vector Store
- Building `RetrievedChunk` and `RetrievalResult`

`vector_store.py` is responsible for:

- Chroma client lifecycle
- Similarity search with metadata filtering
- MMR search with metadata filtering
- All Chroma/embedding calls

The `retriever.py` module no longer:

- Imports `Chroma`
- Generates embeddings
- Calls `_collection.query()`
- Imports `_results_to_docs` or `maximal_marginal_relevance`

---

### Alternatives Considered

#### Keep retrieval logic in retriever

Simpler, but tightly couples orchestration to ChromaDB internals.

Rejected because it violates single-responsibility and makes provider swaps costly.

#### Introduce a separate retrieval provider abstraction

A full `BaseRetrievalProvider` interface with Chroma implementation. More formally correct but introduces abstraction overhead without a current need for multiple providers.

Deferred until a second provider is introduced.

#### Move only MMR logic to vector_store

Incomplete solution — would still leave similarity search and embedding calls in the retriever.

Rejected.

---

### Consequences

#### Advantages

- Clear separation of orchestration from implementation
- Provider-specific code is isolated in one file
- Simplified testing — retriever tests can mock the vector store
- Adding a new retrieval strategy only requires changes in retriever.py (dispatch) and vector_store.py (implementation)
- Switching vector databases only requires changing vector_store.py

#### Trade-offs

- The vector_store module grows larger as more strategies are added
- Tests that verify internals (e.g., embedding calls, MMR parameter passing) must target vector_store namespaces
- Re-exporting `embeddings` and `maximal_marginal_relevance` from `retriever.py` is required for backward compatibility with existing test patches

These trade-offs are acceptable because the module boundary is clear and the vector store is the natural home for provider-specific logic.

---

### Revisit When

A second vector database is introduced and a formal provider abstraction is warranted.

---

# Future Decisions

This section will grow throughout the project.

Potential future decisions include:

- Conversation memory strategy (SQLite-backed)
- Agent planning and reflection strategy
- Reranking models (LLM-based, API-based)
- OCR integration
- Multi-agent workflows
- Authentication
- Deployment architecture
- Caching strategy
- Observability and tracing
- Prompt injection defense
- Knowledge graph schema design
- Graph database selection (Neo4j, Memgraph, FalkorDB)
- Entity and relationship extraction models
- Graph traversal algorithms

---

# ADR-016

## Title

Hybrid Retrieval with Reciprocal Rank Fusion

**Status**

Accepted

### Context

The initial retrieval implementation used only dense vector similarity search (or MMR). While effective for semantic matching, dense retrieval alone struggles with:

- Exact keyword matches (e.g., specific technical terms, product names, error codes)
- Short queries where semantic meaning is ambiguous
- Cases where users expect literal text matching

Lexical search (BM25) complements dense retrieval by excelling at exact term matching while dense retrieval handles semantic similarity.

The challenge was combining both approaches effectively while maintaining the single-retrieval-per-request invariant.

---

### Decision

Implement Hybrid Retrieval as a first-class retrieval strategy alongside Similarity and MMR.

**Architecture:**

1. **Retrieval Strategy Pattern**: Introduced `retrieval_strategies.py` with `RetrievalStrategy` abstract base class and concrete implementations:
   - `SimilarityStrategy`: Dense vector similarity search
   - `MMRStrategy`: Maximum Marginal Relevance search
   - `HybridStrategy`: Combined dense + BM25 with Reciprocal Rank Fusion (RRF)

2. **Reciprocal Rank Fusion (RRF)**: Used to merge dense and BM25 results.
   - Formula: `score = Σ 1 / (k + rank)` for each result list
   - Default `k = 60` (RRF_K in RetrievalConfig)
   - Deduplication by stable chunk identifier `(document_id, chunk_index)`

3. **BM25 Implementation**: In-memory only using `rank-bm25`
   - Built from Vector Store documents on demand
   - No persistence - ChromaDB remains the single source of truth
   - Thread-safe rebuild/refresh/invalidate operations
   - Rebuilt after document upload/deletion

4. **Centralized Configuration**: Extended `RetrievalConfig` with hybrid-specific parameters:
   - `search_type: "similarity" | "mmr" | "hybrid"` (default: "hybrid")
   - `dense_top_k: int` (default: 10)
   - `bm25_top_k: int` (default: 10)
   - `final_top_k: int` (default: 6)
   - `rrf_k: int` (default: 60)
   - `hybrid_enabled: bool` (default: True)

5. **Retrieval Metadata**: `RetrievalResult` now includes optional `retrieval_metadata` dict containing:
   ```python
   {
       "strategy": "hybrid",
       "dense_results": 10,
       "bm25_results": 10,
       "fused_results": 15,
       "duplicates_removed": 5,
       "fusion": "rrf",
       "rrf_k": 60,
       "final_results": 6,
   }
   ```

---

### Alternatives Considered

#### Weighted Score Combination

Linear combination of dense and BM25 scores: `score = α * dense_score + β * bm25_score`.

Rejected because:
- Requires score normalization across different scales
- Weight tuning is brittle and query-dependent
- RRF is parameter-free and more robust

#### Interleaved Merging

Alternate dense and BM25 results (1st dense, 1st BM25, 2nd dense, 2nd BM25...).

Rejected because:
- Doesn't account for relative ranking quality
- No score-based ordering

#### Separate Hybrid Retrieval Module

Initially implemented as `hybrid_retriever.py` with a `hybrid_retrieve()` function.

Refactored to Strategy Pattern because:
- Strategy Pattern allows adding new strategies (Query Rewriting, Reranking) without modifying existing code
- Consistent interface for all retrieval methods
- Better testability and separation of concerns

#### External Search Service (Elasticsearch, OpenSearch)

Rejected because:
- Adds operational complexity
- Not necessary for single-user local application
- BM25 via `rank-bm25` is sufficient for current scale

---

### Consequences

#### Advantages

- **Better recall**: Combines semantic and lexical matching
- **Robust ranking**: RRF is parameter-free and handles score scale differences
- **Extensible architecture**: New strategies (Query Rewriting, Reranking) can be added as Strategy implementations
- **Single retrieval invariant preserved**: Hybrid is one logical retrieval composed of multiple internal strategies
- **Debugging support**: Retrieval metadata provides visibility into the fusion process
- **Provider-agnostic**: BM25 runs locally; dense retrieval uses existing Vector Store abstraction

#### Trade-offs

- **Increased latency**: Two retrieval operations (dense + BM25) per request
- **Memory overhead**: BM25 index held in memory
- **Configuration complexity**: More retrieval parameters to tune
- **Index rebuild required**: BM25 must be refreshed when documents change

These trade-offs are acceptable because:
- Latency is manageable for single-user local use
- Memory usage is proportional to corpus size (typically < 100MB)
- Default parameters work well out of the box
- Rebuild is triggered automatically on document changes

---

### Revisit When

- Reranking is implemented (should operate on RetrievalResult, not trigger new searches)
- Query rewriting is added (should run before strategy selection)
- Multi-vector retrieval is needed (e.g., ColBERT, SPLADE)
- Production-scale requirements emerge

---

---

# ADR-017

## Title

LLM-Based Query Rewriting Before Retrieval

**Status**

Accepted

### Context

User queries in conversational RAG systems are often ambiguous, conversational, or follow-up questions that reference previous context. For example:

- "How does it work?" (after discussing RAG)
- "Explain this section." (referring to a previous retrieval)
- "What about the attention mechanism?" (follow-up)

These queries perform poorly with direct vector similarity search because they lack the context needed to match relevant document chunks.

### Decision

Implement LLM-based query rewriting as a configurable step that runs **before** retrieval strategy selection.

**Architecture:**

1. **Provider-Agnostic Interface**: `BaseQueryRewriter` protocol allows swapping implementations (LLM-based, rule-based, cached, etc.)
2. **Configurable**: Controlled via `RetrievalConfig.query_rewrite` ("none" | "llm") and `RetrievalConfig.query_rewriting_enabled` (bool)
3. **Heuristic Skip**: The LLM rewriter detects queries that are already specific enough (technical terms, standalone questions) and skips rewriting to avoid unnecessary LLM calls
4. **Graceful Fallback**: If rewriting fails (LLM unavailable, timeout, error), falls back to original query without failing the request
5. **Preserved Queries**: Both original and rewritten queries are stored in `RetrievalResult`:
   - `original_query`: Used by Prompt Builder for context-aware prompting
   - `retrieval_query`: Used by Retriever for vector search

**Pipeline Position:**
```
User Question
      │
      ▼
Query Rewriter (if enabled)
      │
      ▼
Retrieval Strategy (Hybrid/MMR/Similarity)
      │
      ▼
Vector Store
```

### Alternatives Considered

#### 1. No Query Rewriting (Baseline)
- Pro: Simple, no additional latency
- Con: Poor retrieval for conversational/follow-up queries

#### 2. Multi-Query Retrieval (Generate multiple queries, merge results)
- Pro: Better recall for complex queries
- Con: Multiple retrieval operations per request; violates single-retrieval invariant; higher latency and cost

#### 3. Query Expansion with Fixed Rules/Synonyms
- Pro: No LLM call needed
- Con: Brittle; doesn't handle conversational context; limited coverage

#### 4. Rewrite Inside Retrieval Strategy
- Pro: Encapsulated
- Con: Couples rewriting to specific strategies; makes strategy selection more complex; harder to test in isolation

### Consequences

**Advantages:**
- Significantly improves retrieval for conversational and follow-up queries
- Provider-agnostic design allows future implementations (local models, cached rewrites, rule-based)
- Heuristic skip avoids unnecessary LLM calls for already-specific queries
- Graceful degradation ensures chat never fails due to rewriting
- Preserves original query for prompt building (citations, context)

**Trade-offs:**
- Additional LLM call latency (~100-300ms) when rewriting is triggered
- Requires LLM availability (falls back gracefully if unavailable)
- Configuration complexity (two flags: strategy + enabled)

### Revisit When

- Reranking is implemented (should operate on RetrievalResult, not trigger new searches)
- Multi-query retrieval is needed for complex questions
- Local/small-model rewriting becomes viable for lower latency

---

# ADR-018

## Title

Cross-Encoder Reranking After Retrieval

**Status**

Accepted

### Context

Hybrid retrieval (dense + BM25 with RRF) significantly improves recall by combining semantic and lexical matching. However, the initial retrieval scores from dense vectors and BM25 are not directly comparable and may not accurately reflect true relevance to the user's query.

Cross-encoders address this by jointly encoding the query and candidate passage, producing a more accurate relevance score. Unlike bi-encoders (used for dense retrieval), cross-encoders attend to both the query and document simultaneously, capturing fine-grained interactions.

The challenge was adding reranking without:
- Triggering additional vector store queries (violating the single-retrieval invariant)
- Changing the public API
- Tightly coupling to a specific reranking model

---

### Decision

Implement Cross-Encoder Reranking as a post-retrieval step that operates on the `RetrievalResult` produced by the retrieval strategy.

**Architecture:**

1. **Provider-Agnostic Abstraction**: `BaseReranker` protocol in `reranker.py` allows swapping implementations.
2. **Default Implementation**: `CrossEncoderReranker` using a local Hugging Face model (default: `cross-encoder/ms-marco-MiniLM-L-6-v2`).
3. **No-Op Implementation**: `NoOpReranker` for when reranking is disabled.
4. **Factory Function**: `get_reranker()` for instantiation.
5. **Configuration**: Extended `RetrievalConfig` with:
   - `reranker: "none" | "cross_encoder"` (default: "cross_encoder")
   - `reranker_top_k: int` (default: 6) — final chunk count after reranking
   - `reranker_candidate_count: int` (default: 20) — candidate count before reranking (set via hybrid's `final_top_k`)

**Pipeline Position:**
```
User Question
      │
      ▼
Query Rewriter (if enabled)
      │
      ▼
Retrieval Strategy (Hybrid/MMR/Similarity)
      │
      ▼
Vector Store + BM25
      │
      ▼
RetrievalResult (candidates)
      │
      ▼
Cross-Encoder Reranker
      │
      ▼
RetrievalResult (reranked, top-k)
      │
      ├────────────► Prompt Builder
      │
      ├────────────► Citation Builder
      │
      └────────────► Agent
```

**Behavior:**

- Reranker receives the retrieval query and candidate chunks
- Computes relevance scores via cross-encoder batch inference
- Reorders chunks by score (highest first)
- Returns top `reranker_top_k` chunks
- All chunk metadata and content preserved; only order changes
- Latency logged for observability

**Performance Optimizations:**

- Singleton model instance (lazy-loaded on first use)
- Thread-safe initialization
- Batch inference (all pairs in one forward pass)
- CPU-compatible model (~22M parameters, ~100MB)

**Error Handling:**

- If reranking fails (model load error, inference error), log exception and return original chunk order
- Request continues normally — chat never fails due to reranking

---

### Alternatives Considered

#### 1. No Reranking (Baseline)
- Pro: Simple, no additional latency
- Con: Relies on retrieval scores that may not reflect true relevance

#### 2. LLM-Based Reranking (e.g., GPT-4, local LLM)
- Pro: Can reason about relevance with full context
- Pro: No additional model dependency
- Con: High latency (seconds per request)
- Con: Non-deterministic, harder to evaluate
- Con: Expensive API calls or heavy local compute

#### 3. API-Based Rerankers (Cohere, Jina, Voyage)
- Pro: State-of-the-art relevance
- Pro: No local model management
- Con: External dependency, API keys required
- Con: Latency variance, rate limits
- Con: Data leaves local environment

#### 4. Reranking as a Retrieval Strategy
- Pro: Encapsulated in strategy pattern
- Con: Would trigger separate retrieval operation
- Con: Violates single-retrieval invariant
- Con: Couples reranking to specific retrieval methods

#### 5. Learn-to-Rank / Lightweight Neural Rerankers (e.g., monoT5)
- Pro: Effective, smaller than cross-encoders
- Con: Additional model dependency
- Con: More complex implementation

---

### Consequences

**Advantages:**

- **Improved precision**: Cross-encoder scores better reflect true query-document relevance
- **Preserves single-retrieval invariant**: Reranking operates on existing `RetrievalResult`, no new vector queries
- **Provider-agnostic**: Abstraction allows future rerankers (LLM, API, no-op) without changing retriever
- **Local-first**: Default model runs on CPU, no external API, no GPU required
- **Efficient**: Singleton model, batch inference, lightweight model (~22M params)
- **Observable**: Retrieval metadata includes reranker info, candidate count, final count, latency
- **Graceful degradation**: Failures fall back to original order, request succeeds

**Trade-offs:**

- **Additional latency**: ~30-80ms for cross-encoder inference on CPU (depends on candidate count)
- **Memory overhead**: Model weights (~100MB) loaded in memory
- **Model dependency**: Requires `sentence-transformers` package
- **Configuration**: Two new config parameters (`reranker`, `reranker_top_k`)

These trade-offs are acceptable because:
- Latency is minimal compared to LLM generation
- Model is small and CPU-friendly
- Default enables reranking for better quality out of the box
- Can be disabled via config if needed

---

### Revisit When

- LLM-based reranking becomes practical for local inference (e.g., via Ollama, llama.cpp)
- Multi-stage reranking (e.g., cross-encoder → LLM) is needed
- GPU acceleration becomes standard for local inference
- Evaluation shows marginal gains for specific domains

---

# ADR-020

## Title

Provider Abstraction Layer for Embeddings and LLM

**Status**

Accepted

### Context

The original implementation created concrete provider instances directly inside modules:
- `embeddings.py` instantiated `HuggingFaceEmbeddings` at module level
- `llm.py` instantiated `ChatGroq` inside `get_llm()`

This violated the provider-agnostic architecture (ADR-007) and made it impossible to:
- Switch providers without modifying RAG module code
- Test with mock providers
- Add new providers without touching core RAG logic

### Decision

Create a dedicated `backend/providers/` package with factory functions:

1. **Provider Registry Pattern**: Dictionary mapping provider name → factory function
2. **Lazy Singleton**: `@functools.lru_cache(maxsize=1)` on factory functions
3. **Configuration-Driven**: Provider selection via `config.py` constants (`EMBEDDING_PROVIDER`, `LLM_PROVIDER`)
4. **Extensible Registration**: `register_embedding_provider()` and `register_llm_provider()` for future additions
5. **Custom Exception**: `ProviderConfigurationError` for invalid provider configuration

Architecture:
```
backend/providers/
├── __init__.py           # Exports factories + exception
├── embeddings.py         # get_embedding_provider() + registry
├── llm.py                # get_llm() + registry
└── exceptions.py         # ProviderConfigurationError
```

RAG modules now import from `backend.providers`:
- `vector_store.py` uses `get_embedding_provider()`
- `agent.py` uses `get_llm()`
- `query_rewriter.py` uses `get_llm()`

### Alternatives Considered

#### 1. Keep Direct Instantiation
- Pro: Simple
- Con: Violates ADR-007; cannot swap providers; hard to test

#### 2. Full Abstract Factory with Base Classes
- Pro: Formal interface contracts
- Con: Overhead for current single-provider needs; premature abstraction

#### 3. Dependency Injection Container
- Pro: Formal DI
- Con: Heavy framework; overkill for this project

### Consequences

**Advantages:**
- Provider selection centralized in `config.py`
- Adding new providers only requires registry registration
- RAG modules remain unchanged when providers change
- Tests can mock at provider factory level
- Consistent with existing registry patterns (reranker, query rewriter, retrieval strategies)

**Trade-offs:**
- Additional `backend/providers/` package
- Factory functions instead of direct module-level instances
- Configuration must include provider name constants

### Revisit When

- Second embedding provider is added
- Second LLM provider is added
- Need for per-request provider selection arises

---

# ADR-019

## Title

Separate Prompt Construction from Retrieval and Generation

**Status**

Accepted

### Context

In the initial implementation, prompt construction was embedded within the LangChain agent middleware as a static system prompt. The agent received the user question, called the retrieve_context tool, and then generated an answer using the tool results as context. This approach had several limitations:

1. **Tight coupling to LangChain**: The prompt was constructed via middleware, making it difficult to customize the prompt structure or test independently.
2. **No context formatting control**: The tool's serialized output was a simple "Source: metadata\nContent: text" format that didn't include clear metadata fields, separators, or structured sections.
3. **No deduplication**: Duplicate chunks from hybrid retrieval could appear in the context, wasting tokens.
4. **No context length management**: Long contexts could exceed model limits without graceful handling.
5. **Weak grounding instructions**: The system prompt had basic grounding rules but lacked explicit citation guidance, hallucination prevention, and behavior constraints.
6. **Provider-specific assumptions**: The middleware approach assumed LangChain's message format.

As retrieval quality improved (hybrid search, reranking), the need for better prompt construction became more critical to fully leverage the retrieved context.

### Decision

Extract prompt construction into a dedicated **Prompt Builder** module (`prompts.py`) with the following responsibilities:

1. **Build structured prompts** with four clearly separated sections:
   - SYSTEM INSTRUCTIONS (grounding rules, citation guidance, behavior)
   - USER QUESTION (original question)
   - RETRIEVED CONTEXT (formatted chunks with metadata)
   - ANSWER (generation instruction)

2. **Format context with rich metadata**: Each chunk includes Document (filename), Page, Chunk index, and Relevance Score — never internal IDs.

3. **Deduplicate chunks**: Remove exact-content duplicates before formatting, preserving the highest-ranked occurrence.

4. **Manage context length**: Truncate from the end to fit within a character budget (default 8000 chars), preserving retrieval order. Never truncate individual chunks.

5. **Strengthen grounding**: Explicit instructions to answer only from context, state when information is unavailable, avoid fabrication, prefer precision, synthesize multi-source answers, preserve terminology.

6. **Guide citations**: Instruct the LLM to reference sources naturally, attribute key claims, and avoid internal metadata references.

7. **Provider-agnostic output**: Plain text that works with any chat model — no special tokens, no model detection, no provider-specific formatting.

8. **Modular design**: Separate functions for each section (`build_system_prompt`, `build_user_question_section`, `build_context_section`, `build_final_instruction`, `build_prompt`) enable testing and future iteration.

The Agent (`agent.py`) now orchestrates:
1. Call `retrieve_context` tool to get `RetrievalResult`
2. Call `build_prompt(question, retrieval_result)` from Prompt Builder
3. Send prompt to LLM for answer generation
4. Build citations from same `RetrievalResult`
5. Return `ChatResult`

This preserves the single-retrieval invariant: the `RetrievalResult` flows to Prompt Builder, Citation Builder, and Agent without additional vector store queries.

### Alternatives Considered

#### 1. Keep LangChain Middleware Prompt
- Pro: Minimal change
- Con: Cannot customize structure, format context, or manage length; tied to LangChain internals

#### 2. Embed Prompt Logic in Agent
- Pro: Co-located with orchestration
- Con: Violates single responsibility; harder to test; mixes business logic with prompt engineering

#### 3. Prompt Templates in Config Files
- Pro: Non-code changes
- Con: Logic (deduplication, truncation, metadata formatting) cannot live in templates; still need code

#### 4. LLM-Based Prompt Optimization
- Pro: Could optimize prompts automatically
- Con: Adds latency, complexity, non-determinism; overkill for current needs

### Consequences

**Advantages:**
- Clear separation: Prompt Builder only constructs prompts; never performs retrieval
- Structured context improves LLM comprehension and grounding
- Deduplication and truncation prevent token waste and overflow
- Strong grounding instructions reduce hallucinations
- Citation guidance produces more attributable answers
- Provider-agnostic: works with Groq, OpenAI, Anthropic, local models
- Testable: Each section builder is a pure function
- Extensible: Easy to add new sections, modify formatting, adjust config

**Trade-offs:**
- Additional module (`prompts.py`)
- Agent now explicitly calls Prompt Builder (was implicit in middleware)
- Context length budget requires tuning (default 8000 chars)

### Revisit When

- Structured output parsing is needed (JSON, function calling)
- Multi-modal prompts (images, tables) are introduced
- Conversation history requires context injection
- Evaluation shows prompt format significantly impacts quality

---

# ADR-021

## Title

Native Tool Calling via ToolExecutor

**Status**

Accepted

### Context

Initial agent implementation embedded orchestration directly in `agent.py` with a single `retrieve_context` tool. As more tools were planned (`list_documents`, `search_by_filename`), the orchestration logic needed to support:
- Multiple tools
- Iterative tool selection (LLM chooses different tools across iterations)
- Per-request conversation state
- Configurable safety limits (max iterations, max tools per response)
- Graceful error handling for unknown tools and tool failures
- Streaming support for both tool events and answer tokens

### Decision

Introduce a dedicated **ToolExecutor** class in `tool_executor.py` that owns the tool orchestration loop:

1. **Multi-Iteration Loop**: The executor calls the LLM with bound tools, executes any tool calls the LLM requests, adds results to conversation state, and re-invokes the LLM — until the LLM produces a final answer or the iteration limit is reached.
2. **ConversationState**: A per-request dataclass tracking messages (Human, AI, Tool), tool call metadata, and retrieval results.
3. **Safety Limits**: Configurable `max_iterations` (default 10, prevents infinite loops) and `max_tools_per_response` (default 5, limits parallel tool calls).
4. **Graceful Error Handling**: Unknown tools and tool exceptions produce structured `ToolExecutionResult` with error details, allowing the LLM to recover or explain.
5. **Two Entry Points**: `ToolExecutor.execute()` for synchronous use and `agent.stream_events()` for streaming via async generator.
6. **Singleton**: Default executor cached via `get_tool_executor()` for backward compatibility; `_reset_executor()` exists only for test isolation.

### Alternatives Considered

#### 1. LangChain AgentExecutor

LangChain's built-in `AgentExecutor` class provides similar functionality. Rejected because:
- Tight coupling to LangChain's message format and execution model
- Difficult to customize tool result handling and error recovery
- Streaming behavior is harder to control

#### 2. Embedded in agent.py

Keep orchestration in agent.py. Rejected because:
- Violates single responsibility as agent.py grew
- Harder to test orchestration independently
- Duplicated logic between streaming and non-streaming paths

#### 3. State Machine

Formal state machine for orchestration. Rejected because:
- Over-engineered for current needs
- LLM already acts as the decision-maker

### Consequences

**Advantages:**
- Clean separation: ToolExecutor owns orchestration, agent.py provides entry points
- Testable: Orchestration logic can be tested with mocked LLM and tools
- Extensible: New safety limits, tool types, and iteration strategies can be added without changing agent.py
- Streaming: Single orchestration that works for both synchronous and async streaming

**Trade-offs:**
- Additional module and class
- Singleton pattern requires test isolation helper
- `_reset_executor()` is a private testing-only API

### Revisit When

- Multi-agent orchestration is needed
- Complex planning strategies replace iterative tool selection
- Workflow-based orchestration (DAG, LangGraph) is introduced

---

# ADR-022

## Title

ConversationState for Per-Request State Tracking

**Status**

Accepted

### Context

During a single request, the ToolExecutor loop may invoke the LLM multiple times with different tool results. State management requires:
- Tracking conversation history (user message, AI responses, tool results)
- Collecting tool call metadata for the final response
- Accumulating retrieval results for citation generation
- Proper LangChain message format for LLM consumption

Previously, state was managed ad-hoc in agent.py without a structured container.

### Decision

Introduce `ConversationState` dataclass in `tool_executor.py`:

```python
@dataclass
class ConversationState:
    messages: list                      # LangChain messages (Human, AI, Tool)
    tool_calls: list[dict]             # Tool call metadata for final response
    retrieval_results: list[RetrievalResult]  # Accumulated for citation building
    tool_execution_results: list[ToolExecutionResult]
```

Methods provide typed message creation:
- `add_user_message(content)` → HumanMessage
- `add_assistant_message(content, tool_calls)` → AIMessage with tool_calls
- `add_tool_message(tool_call_id, content, artifact)` → ToolMessage
- `get_messages_for_llm()` → Returns messages in LLM-compatible format

### Alternatives Considered

#### 1. Ad-hoc lists in agent.py

Simple but leads to scattered state management and makes testing harder.

#### 2. LangChain's built-in state

LangChain provides conversation buffers, but they don't track tool calls and retrieval results separately.

#### 3. Dedicated database

Overkill for per-request state. Conversations are ephemeral within a single request.

### Consequences

**Advantages:**
- Single place for per-request state
- Clear message creation API
- Easy to test and extend
- Separate tracking of tool calls, retrieval results, and execution results

**Trade-offs:**
- Creates a dependency on LangChain message types
- State is memory-only for the duration of a single request

### Revisit When

- Persistent conversation memory is introduced (cross-request state)
- Multi-agent conversations need shared state

---

# ADR-023

## Title

Dynamic Tool Registry with Individual Tool Modules

**Status**

Accepted

### Context

Adding new tools required modifying the registry and understanding the tool registration mechanism. Each tool previously had its implementation scattered across modules. As the platform grows to support more tools, a clear tool registration pattern is needed.

### Decision

Organize tools as individual modules in `backend/rag/tools/` with a central registry in `tools/__init__.py`:

```
backend/rag/tools/
├── __init__.py           # Exports get_tools() + individual tool functions
├── retrieve_context.py   # Re-exports from retriever.py
├── list_documents.py     # LangChain @tool, delegates to Document Service
└── search_by_filename.py # LangChain @tool, delegates to Document Service
```

Each tool:
- Is a LangChain `@tool` with `response_format="content_and_artifact"`
- Has a clear description for LLM tool selection
- Delegates business logic to the appropriate service
- Returns `(serialized_string, artifact)` tuple

The registry:
- `tool_registry.py` provides backward-compatible `get_tools()` that delegates to `tools.get_tools()`
- Adding a new tool requires: create module in `tools/`, add to `tools/__init__.py`, done

### Alternatives Considered

#### 1. All tools in one file

Simple but becomes unwieldy as tool count grows.

#### 2. Decorator-based auto-registration

Convenient but creates magic imports and makes it harder to see all available tools.

#### 3. Configuration-driven registry

YAML/JSON tool definitions. Rejected because tool logic still needs Python.

### Consequences

**Advantages:**
- Clear pattern for adding tools: one file per tool
- Tools are self-documenting (description + type hints)
- Central registry provides visibility into all available tools
- Backward compatible via `tool_registry.py`

**Trade-offs:**
- More files than monolithic approach
- Each tool must be explicitly imported in `__init__.py`

### Revisit When

- 10+ tools exist and discovery/search becomes useful
- Dynamic tool loading from plugins is needed

---

# ADR-024

## Title

Configurable Safety Limits for Tool Execution

**Status**

Accepted

### Context

The tool execution loop can iterate indefinitely if the LLM keeps requesting tool calls. Without safety limits, a misbehaving LLM or buggy tool could:
- Consume excessive tokens and time
- Loop infinitely
- Execute too many parallel tool calls

### Decision

Introduce two configurable safety limits in `config.py`:

```
MAX_TOOL_ITERATIONS = 10     # Maximum tool loop iterations per request
MAX_TOOLS_PER_RESPONSE = 5   # Maximum tool calls in a single LLM response
```

Both are configurable via `ToolExecutor.__init__()` parameters and via config constants:

- **MAX_TOOL_ITERATIONS**: When exceeded, execution stops with "Maximum tool iterations exceeded" message. Prevents infinite loops.
- **MAX_TOOLS_PER_RESPONSE**: When an LLM response requests more tools than this limit, excess calls are truncated. Prevents resource exhaustion from parallel tool calls.

### Alternatives Considered

#### 1. No limits

Simple but dangerous — production systems need guardrails against runaway loops.

#### 2. Timeout-based limits

Limit by wall-clock time instead of iteration count. More robust but harder to implement correctly across async/sync paths.

#### 3. Token budget limits

Limit by estimated token consumption. More precise but complex and model-dependent.

### Consequences

**Advantages:**
- Prevents infinite loops and resource exhaustion
- Simple to understand and configure
- Both limits can be tuned per deployment

**Trade-offs:**
- Hard iteration limits may cut off legitimate multi-step reasoning
- Time-based limits would be more robust for long-running tools

### Revisit When

- Timeout-based or token-budget limits are needed
- Per-request configuration of safety limits is required

---

# ADR-025

## Title

Frontend-Only Settings via React Context + localStorage

**Status**

Accepted

### Context

The MVP needed user-configurable preferences (confirm-before-delete, show-citations toggle) without introducing a settings API or database. Settings are per-browser UI preferences, not backend configuration.

### Decision

Store settings in localStorage via a `settingsService.ts` wrapper, served to components via `SettingsContext` (React Context + `useState` + `useCallback`):

- `settingsService.ts` handles serialization, deserialization, defaults, and reset
- `SettingsContext` provides `settings`, `updateSettings()`, `resetToDefaults()`
- Defaults are defined in the service, not duplicated across consumers

Settings are intentionally **not** sent to the API. They affect only frontend behavior:
- `confirmBeforeDelete` → shows confirmation dialog before document deletion
- `showCitations` → toggles citation card visibility

### Alternatives Considered

#### Settings API Endpoint
Too heavy for UI-only preferences. Adds backend complexity for data the frontend manages exclusively.

#### Zustand / Redux
Overkill for two boolean toggles. React Context + useState is sufficient and avoids additional dependencies.

#### URL Parameters
Impractical for persistent preferences across sessions.

### Consequences

**Advantages:**
- Zero backend changes for settings
- Survives page refreshes (localStorage)
- Simple, testable service layer
- Easy to extend with new settings

**Trade-offs:**
- Settings are per-browser (lost on cache clear)
- No server-side configuration
- Cannot share settings across devices

### Revisit When

Settings need to affect backend behavior (e.g., retrieval config sent with chat requests).

---

# ADR-026

## Title

ConversationContext for Frontend-Only Conversation State

**Status**

Accepted

### Context

The chat interface needs to track message state (user messages, AI responses, streaming status) and support reset. The backend has no conversation history endpoint — each request is stateless.

### Decision

Manage conversation state via `ConversationContext` (React Context):

- Stores `messages: Message[]` — ordered list of chat messages
- Provides `addMessage()`, `resetConversation()` (with confirmation dialog)
- Uses `useRef` for stable callback identity during streaming
- Reset triggers a `confirm()` dialog before clearing state

The context is consumed by `ChatWindow`, `ChatInput`, `ConversationHeader` and `Message` components.

### Alternatives Considered

#### Backend Conversation History API
Post-MVP feature. Current stateless design is simpler and sufficient.

#### URL State
Impractical for multi-message conversations.

#### Zustand / Redux
Not warranted for a single array of messages with two operations.

### Consequences

**Advantages:**
- Simple, React-native state management
- No backend changes needed
- Confirmation dialog prevents accidental data loss

**Trade-offs:**
- State lost on page refresh (no persistence)
- No conversation history across sessions

### Revisit When

Conversation persistence (SQLite backend) is implemented as a planned feature.

---

# ADR-027

## Title

citationUtils — Pure Functions for Citation Display

**Status**

Accepted

### Context

Citation cards displayed source documents for each AI response. Multiple citations from the same document appeared as separate cards, and the UI needed deduplication and grouping without coupling display logic to component internals.

### Decision

Extract citation display logic into `citationUtils.ts` as pure functions:

- `deduplicateCitations(sources)` — Removes duplicate citations by `document_id`, preserving the highest-score entry
- `groupCitationsByDocument(sources)` — Groups deduplicated citations by source document for structured display

These are consumed by `citationUtils` module and `CitationCard` / `Message` components. No component imports the service layer directly for citation formatting.

### Alternatives Considered

#### Deduplication in Component
Duplicates logic across components. Harder to test.

#### Deduplication in CitationCard
Wrong layer — card should receive ready-to-render data.

### Consequences

**Advantages:**
- Testable pure functions
- Reusable across components
- Single place for citation formatting logic

**Trade-offs:**
- Additional file (`citationUtils.ts`)

### Revisit When

Citation display needs server-side grouping or more complex transformation.

---

# ADR-028

## Title

CitationViewModel — Component-Level Citation State

**Status**

Accepted

### Context

Each citation card needs local UI state (expanded/collapsed, clipboard copy feedback) independent of the citation data model. Tracking this in a separate state variable per card was verbose and error-prone.

### Decision

Introduce a per-card `CitationViewModel` pattern in the `Message` component:

```typescript
interface CitationViewModel {
  open: Record<string, boolean>;   // citation_id → expanded state
  copyState: Record<string, "idle" | "copied">; // citation_id → copy feedback
}
```

Each citation card reads its `open` and `copyState` from the view model. The `Message` component owns the view model and passes derived values to each `CitationCard`.

### Alternatives Considered

#### State Inside CitationCard
Each card manages its own expanded/copy state. Pros: encapsulated. Cons: parent cannot programmatically collapse all; state resets on re-render.

#### Global State (Context)
Over-engineered for local UI state that only affects one message's citations.

### Consequences

**Advantages:**
- Clean separation of UI state from data
- Parent can control all citation cards
- Clipboard feedback is local and resets after timeout
- No global state pollution

**Trade-offs:**
- View model must be maintained alongside data model
- Slightly more code than inline state

### Revisit When

Citation state becomes complex enough to warrant a dedicated store or hook.

---

# ADR-029

## Title

SSE Event Format: Token Events + Done Event

**Status**

Accepted

### Context

The streaming chat endpoint needed a format that supported progressive token rendering and final metadata delivery (sources, tool calls). The initial implementation used raw token strings as SSE data, which couldn't distinguish token events from terminal events.

### Decision

Use a structured JSON format for all SSE events:

**Token Events** (zero or more):
```json
{"token": "Re"}
```

**Done Event** (exactly one, sent last):
```json
{"done": true, "sources": [...], "tool_calls": [...]}
```

The frontend parses each `data:` line:
- If `parsed.token` is a string → append to displayed answer
- If `parsed.done === true` → finalize with sources and tool calls

### Alternatives Considered

#### Raw Token Strings
```text
data: Re
```
Pros: Simpler parsing. Cons: Cannot distinguish tokens from terminal metadata; stream ends without structured completion.

#### Chunked JSON array
Yield a single JSON array of all tokens after generation. Pros: Atomic. Cons: No progressive rendering; higher time-to-first-token.

#### Multiple event types (event: token / event: done)
SSE `event` field. Pros: Semantic. Cons: More complex frontend parsing; some SSE clients handle event differently.

### Consequences

**Advantages:**
- Progressive rendering (TTFT ~ first token)
- Structured completion metadata
- Single field check (`parsed.token` vs `parsed.done`) for routing
- Compatible with standard EventSource parsing

**Trade-offs:**
- Slightly more bytes per token (JSON overhead)
- Frontend must buffer incomplete lines

### Revisit When

Multiple event types (tool_call_start, tool_call_end, error) need distinct frontend handlers.

---

# ADR-030

## Title

No Settings API — Settings Are Frontend-Only

**Status**

Accepted

### Context

Milestone 5 planned a settings page. Settings could be stored on the backend (via API) or on the frontend (localStorage). The MVP settings are UI-only preferences that affect only frontend behavior.

### Decision

Settings are strictly frontend-only. No backend settings API is implemented.

Settings managed via localStorage + SettingsContext:
- `confirmBeforeDelete` — UI behavior preference
- `showCitations` — display preference

If future settings need to affect backend behavior (retrieval mode, top-K, temperature), those should be sent as query parameters or request body fields on the chat endpoint rather than via a separate settings API.

### Alternatives Considered

#### Full Settings API (GET/PUT /settings)
Adds backend CRUD complexity for data that only the frontend consumes. Over-engineered for two boolean toggles.

#### Settings as Chat Request Fields
Send `message + settings` to `/chat/stream`. Appropriate when settings affect retrieval/LLM behavior, but current settings are UI-only.

### Consequences

**Advantages:**
- Zero backend changes
- Simple persistence
- Fast iteration (no API versioning)

**Trade-offs:**
- Settings are per-browser, not per-user
- No server-side defaults
- Cannot extend to backend-affecting settings without API changes

### Revisit When

Settings need to affect retrieval or LLM behavior (e.g., retrieval mode, top-K, temperature).

---

# ADR-031

## Title

Future Vision Provider Abstraction

**Status**

Proposed

### Context

Milestone 7 introduces multimodal capabilities including image extraction, OCR, table/chart understanding, and visual reasoning. These capabilities require vision-capable models (GPT-4V, Claude Vision, Gemini Vision, local multimodal models).

Without a provider abstraction, vision model selection would be hardcoded into extraction and reasoning modules, creating vendor lock-in and violating the existing provider-agnostic architecture (ADR-007).

### Decision

Vision models must be accessed through provider abstractions exactly like LLM and embedding providers.

The planned structure:

```
backend/providers/
├── __init__.py
├── embeddings.py      # existing
├── llm.py             # existing
├── exceptions.py      # existing
├── vision.py          # planned
└── search.py          # planned
```

The vision provider will follow the same patterns as ADR-020:

1. **Factory function**: `get_vision_provider()` returns a configured vision-capable model
2. **Registry pattern**: Dictionary mapping provider name → factory function
3. **Lazy singleton**: `@functools.lru_cache(maxsize=1)` for efficiency
4. **Configuration-driven**: Provider selection via `config.py` constant (`VISION_PROVIDER`)
5. **Unified interface**: Supports multimodal inputs (text + image)

### Alternatives Considered

#### 1. Direct Vision Model Instantiation

Simpler but violates provider-agnostic architecture. Hard to switch between vision providers.

#### 2. Single Multimodal LLM Provider

Merge vision into the existing LLM provider. Rejected because not all LLMs support vision, and the abstraction would need to handle both text-only and multimodal scenarios differently.

#### 3. External Vision Service

Separate microservice for vision processing. Over-engineered for current scope.

### Consequences

**Advantages:**

- Consistent with existing provider architecture (ADR-007, ADR-020)
- Easy to add new vision providers without changing extraction or reasoning modules
- Provider selection centralized in config.py
- Testable with mock vision providers

**Trade-offs:**

- Additional provider module
- Vision providers must implement the same interface despite different capabilities
- Some vision features (OCR, chart understanding) may need finer-grained abstraction

### Revisit When

- Vision models are added and the abstraction proves too coarse
- A vision-specific registry pattern is needed (e.g., separate OCR vs. visual reasoning providers)

---

# ADR-032

## Title

Web Search as an Agent Tool

**Status**

Proposed

### Context

Milestone 8 introduces external knowledge retrieval via web search. The question is whether web search should be:

- Part of the Retrieval pipeline (alongside similarity, MMR, hybrid)
- An Agent Tool (alongside retrieve_context, list_documents)

### Decision

Web search is implemented as an **Agent Tool**, not inside the Retriever.

### Reason

- Keeps the Retriever dedicated to local knowledge (uploaded documents).
- Allows the Agent to decide when external knowledge is necessary, maintaining the Agent's role as the orchestrator.
- Supports future tools consistently — web search follows the same pattern as summarize_document, search_by_metadata, etc.
- The Retriever remains a pure document retrieval pipeline without branching logic for external sources.

### Alternatives Considered

#### 1. Web Search as a Retrieval Strategy

Add a `WebSearchStrategy` alongside Similarity, MMR, and Hybrid. Rejected because it would couple web search to the retrieval pipeline, making the Retriever responsible for external knowledge. This violates single responsibility.

#### 2. Automatic Fallback Inside Retriever

Retriever automatically falls back to web search when document retrieval returns no results. Rejected because it removes the Agent's decision-making capability and couples web search logic to retrieval orchestration.

#### 3. Separate Retrieval Pipeline for Web

A parallel retrieval pipeline for web results merged with document results. Over-engineered — an Agent tool is simpler and follows existing patterns.

### Consequences

**Advantages:**

- Consistent with tool-oriented architecture (ADR-014)
- Retriever remains focused on local document retrieval only
- Agent controls when to use web search
- Web search can be enabled/disabled per request via tool selection
- Same streaming, citation, and error handling as other tools

**Trade-offs:**

- The Agent must explicitly decide to call web_search (not automatic)
- Web results merged with document results at the prompt level, not the retrieval level
- May need heuristics for when to trigger web search (confidence scoring)

### Revisit When

- Web search becomes a primary retrieval path rather than a fallback
- Automatic web search triggering (without Agent invocation) is needed for specific query types

---

# ADR-033

## Title

Unified Multimodal Retrieval

**Status**

Proposed

### Context

Milestone 7 introduces multimodal document understanding — images, tables, charts, and OCR text extracted from PDFs. Each modality has different characteristics:

- Text is embedded via text embeddings
- Images may need separate vision embeddings
- Tables may need hybrid representations
- OCR text is plain text extracted from images

The question is whether each modality should have its own retrieval pathway or share a unified abstraction.

### Decision

Regardless of whether context originates from text, images, tables, or OCR, the Retriever exposes a single `RetrievalResult` abstraction.

All modalities share the same Vector Store. The `RetrievedChunk` metadata includes a `source_type` field to distinguish modalities.

### Reason

- Downstream Prompt Builder and Agent should remain modality-agnostic.
- The single-retrieval-per-request invariant (ADR-00X) should hold regardless of modality.
- Modality-specific handling belongs in the Prompt Builder (formatting), not the retrieval layer.

### Alternatives Considered

#### 1. Separate Retrieval Pipelines per Modality

Each modality has its own retriever and vector index. Rejected because it significantly increases complexity, violates the single-retrieval invariant, and forces downstream components to merge results.

#### 2. Modality-Aware RetrievalResult

Add modality-specific fields to RetrievalResult (e.g., extracted_images, tables). Rejected because it couples downstream components to specific modalities and breaks the clean abstraction.

#### 3. Prompt-Time Modality Handling

Retrieval remains completely modality-agnostic. The Prompt Builder handles formatting differences. This is the chosen approach.

### Consequences

**Advantages:**

- Prompt Builder and Agent remain unchanged for text-only vs. multimodal scenarios
- Single RetrievalResult flows through the existing architecture
- Modality metadata in each chunk enables flexible downstream handling
- New modalities can be added without changing the retrieval abstraction

**Trade-offs:**

- Prompt Builder must handle different modalities in formatting
- Unified embeddings across modalities may lose modality-specific signals
- May need modality-specific retrieval strategies for optimal quality

### Revisit When

- Modality-specific retrieval strategies (e.g., separate image/table indexes) measurably improve quality
- Downstream components need modality-specific processing before prompt construction

---

# ADR-034

## Title

Knowledge Graph Abstraction

**Status**

Proposed

### Context

Milestone 9 introduces GraphRAG, which constructs a knowledge graph from the document corpus. The knowledge graph represents entities (concepts, people, organizations, APIs, classes, files, components, documents) and their relationships (references, depends_on, implements, calls, extends, belongs_to, mentions).

Without a provider-independent graph abstraction, business logic would be coupled to a specific graph database, violating the provider-agnostic architecture (ADR-007).

### Decision

Represent document knowledge through a provider-independent graph abstraction rather than coupling business logic to a specific graph database.

Graph operations are accessed through `providers/graph.py` following the same factory + registry pattern as LLM and embedding providers.

### Reason

Maintain provider independence. The graph database can be swapped without changing RAG modules, retrieval strategies, or agent tools.

### Alternatives Considered

#### 1. Direct Graph Database Integration

Embed Neo4j/Memgraph/FalkorDB client directly in retrieval modules. Rejected because it violates ADR-007 and creates vendor lock-in.

#### 2. In-Memory Graph Only

Use networkx or similar for in-memory graph only. Rejected because it doesn't scale and can't be persisted across restarts.

### Consequences

**Advantages:**

- Consistent with existing provider architecture (ADR-007, ADR-020)
- Easy to add new graph providers without changing business logic
- Provider selection centralized in config.py
- Testable with mock graph providers

**Trade-offs:**

- Additional provider module
- Graph databases have different query languages and capabilities
- Abstraction may not expose database-specific optimizations

### Revisit When

- A second graph database provider is introduced
- Graph-specific query optimizations are needed that the abstraction cannot express

---

# ADR-035

## Title

Graph Retrieval Complements Vector Retrieval

**Status**

Proposed

### Context

Milestone 9 introduces GraphRAG for relationship-aware retrieval. The question is whether graph retrieval should replace vector retrieval or complement it.

Vector retrieval excels at semantic similarity search. Graph retrieval excels at relationship traversal and multi-hop reasoning. Neither alone covers all retrieval scenarios.

### Decision

Graph retrieval is an additional retrieval strategy. It does not replace similarity retrieval, hybrid retrieval, or reranking.

Graph retrieval should be composable with existing retrieval strategies.

### Reason

Different retrieval approaches serve different query types:

- Semantic queries → vector retrieval
- Exact keyword queries → BM25/hybrid retrieval
- Relationship queries ("what depends on X?", "who calls Y?") → graph retrieval
- Complex queries may benefit from combining multiple strategies

### Alternatives Considered

#### 1. Replace Vector Retrieval with Graph Retrieval

Graph-only retrieval loses semantic similarity capabilities. Rejected because vector retrieval handles semantic queries better than graph traversal.

#### 2. Separate Graph and Vector Pipelines

Run graph and vector retrieval independently with separate downstream components. Rejected because it complicates the architecture and creates duplicate prompt construction and citation paths.

### Consequences

**Advantages:**

- Each retrieval strategy handles what it does best
- Composable — strategies can be combined
- Existing vector retrieval pipeline remains unchanged
- New graph-specific tools can be added without modifying existing tools

**Trade-offs:**

- More retrieval strategies to manage
- Graph retrieval adds complexity to the retrieval layer
- May need strategy selection heuristics for optimal query routing

### Revisit When

- Evaluation shows graph retrieval alone outperforms vector retrieval for specific domains
- A unified retrieval abstraction that subsumes all strategies is needed

---

# ADR-036

## Title

Internal Wiki Generation from Knowledge Graph

**Status**

Proposed

### Context

Milestone 9 builds a knowledge graph from the document corpus. The knowledge graph captures entities and their relationships across documents.

Beyond retrieval, the knowledge graph can serve as the source for automatically generated documentation — concept pages, relationship maps, and summaries that help users explore the corpus.

### Decision

The knowledge graph becomes the source for automatically generated internal wiki pages and concept summaries.

### Reason

Allow users to explore relationships across the corpus instead of searching only by keywords. The wiki provides a browsable, structured view of the document corpus that complements keyword-based retrieval.

### Alternatives Considered

#### 1. Wiki as Separate System

Build a standalone wiki system independent of the knowledge graph. Rejected because it duplicates data and creates synchronization overhead.

#### 2. Static Documentation Only

Generate static pages at indexing time. Rejected because the knowledge graph evolves incrementally and wiki pages should reflect the current state.

### Consequences

**Advantages:**

- Wiki stays in sync with the knowledge graph automatically
- Users can browse relationships without formulating queries
- Concept pages provide overviews that are hard to discover through search alone
- Internal wiki tool can be invoked by the Agent when users ask exploratory questions

**Trade-offs:**

- Wiki quality depends on extraction quality
- Large corpora may produce overwhelming wiki output
- Wiki generation adds processing time during indexing

### Revisit When

- Extraction quality is insufficient for useful wiki content
- Users need persistent, versioned wiki pages rather than on-demand generation
- Wiki output needs to be stored and served as static content

---

# ADR-037

## Title

Unified RetrievalResult Across All Retrieval Strategies

**Status**

Proposed

### Context

Milestone 9 adds graph retrieval alongside vector retrieval. Milestone 8 adds web search. Multiple retrieval strategies now produce results that need to flow through the same downstream pipeline (Prompt Builder, Citation Builder, Agent).

Without a unified abstraction, each retrieval strategy would require its own downstream handling, multiplying complexity.

### Decision

Regardless of whether retrieved context originates from:

- Vector Search
- Graph Search
- Future Web Search

all retrieval outputs should continue using the existing `RetrievalResult` abstraction.

### Reason

Keep Prompt Builder, Agent, and downstream components provider- and retrieval-strategy agnostic. The `RetrievalResult` is the single source of truth for the remainder of a request lifecycle.

### Alternatives Considered

#### 1. Strategy-Specific Result Types

Each retrieval strategy returns its own result type. Rejected because it multiplies downstream handling and violates the single-retrieval invariant.

#### 2. Merged Result at Retrieval Layer

Merge all retrieval results into a single result inside the Retriever. This is the chosen approach — but the merged result must use the same `RetrievalResult` structure.

### Consequences

**Advantages:**

- Prompt Builder, Citation Builder, and Agent remain unchanged
- New retrieval strategies can be added without modifying downstream components
- Single retrieval invariant preserved across all strategy types
- Debugging is consistent — same result structure regardless of strategy

**Trade-offs:**

- `RetrievalResult` may need to carry metadata indicating which strategies contributed
- Graph-specific metadata (entities, relationships, paths) must be expressible within the existing chunk/metadata model

### Revisit When

- Retrieval strategies produce fundamentally different output structures that cannot be unified
- Downstream components need strategy-specific processing before prompt construction

---

# Decision Guidelines

