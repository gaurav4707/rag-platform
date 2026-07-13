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

- Conversation memory strategy
- Agent planning strategy
- Tool selection policies
- Hybrid retrieval (implemented - see ADR-016)
- Reranking models
- OCR integration
- Multi-agent workflows
- Authentication
- Deployment architecture
- Caching strategy
- Observability and tracing

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

# Decision Guidelines

A new decision should be recorded when:

- The project architecture changes.
- A major dependency is introduced or replaced.
- A significant trade-off is made.
- Multiple valid approaches exist and one is selected.
- Future contributors would benefit from understanding the reasoning.

Small implementation details should not be recorded here.

This document should explain **why** decisions were made, not **how** they were implemented.

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

# Decision Guidelines

