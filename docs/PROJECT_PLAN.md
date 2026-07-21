# PROJECT_PLAN.md

# Agentic RAG Platform

## 1. Project Overview

### Goal

Build a production-style **Agentic Retrieval-Augmented Generation (Agentic RAG)** platform that enables users to upload PDF documents and interact with them through an intelligent conversational interface.

Unlike a traditional RAG application, this project uses an **LLM-powered agent** capable of selecting and invoking tools to answer user requests.

The project is designed primarily for learning modern AI engineering practices while maintaining a clean, modular, provider-agnostic architecture suitable for future expansion.

---

## 2. Objectives

### Primary Objectives

- Learn Agentic RAG architecture end to end.
- Understand Retrieval-Augmented Generation from first principles.
- Learn how AI agents interact with tools.
- Build a modular backend using FastAPI and LangChain.
- Build a modern frontend using React.
- Understand every architectural decision instead of relying on framework abstractions.
- Maintain a provider-agnostic architecture.

### Secondary Objectives

- Produce a portfolio-quality project.
- Create a reusable Agentic RAG framework.
- Support future AI workflows without architectural redesign.
- Make the project understandable for both humans and AI coding agents.

---

## 3. Current Scope (MVP)

## Backend

Implemented

- PDF upload
- Text extraction
- Chunking
- Embeddings
- ChromaDB integration
- Semantic retrieval
- Similarity search with metadata filtering
- Maximum Marginal Relevance (MMR)
- Streaming responses
- Source citations
- Document listing
- Document deletion
- Standardized API errors
- Agent orchestration
- Tool registration
- Tool-based retrieval
- Stable streaming tool execution
- RetrievalConfig with strategy dispatch
- **Hybrid Retrieval (Dense + BM25 with RRF)**
- **Retrieval Strategy Pattern (Similarity, MMR, Hybrid)**
- **Centralized Retrieval Configuration**
- **Retrieval Metadata for debugging/evaluation**
- **Query Rewriting**
- **Cross-Encoder Reranking**
- **BM25 Lexical Search**
- **Reciprocal Rank Fusion (RRF)**
- **Offline Retrieval Evaluation Framework**
- **Provider Abstraction Layer (backend/providers/)**

Planned

- Conversation memory with SQLite

---

## Frontend

Implemented

- Upload interface
- Chat interface
- Streaming chat
- Responsive layout
- Source citation cards (expand/collapse, clipboard, deduplication)
- Document management
- Settings (retrieval mode, top-K, reranking, temperature, theme)
- Conversation management (reset with confirm, message count, summary header)
- Conversation context provider
- Settings persistence (localStorage)
- Refined error handling (notifications, connection lost)
- Upload polish (transition animations, cleanup)
- Dead code and import cleanup

Planned

- Conversation history with persistence
- Better accessibility
- Keyboard shortcuts
- Multi-turn conversation sidebar

---

## 4. Out of Scope (MVP)

The following capabilities are intentionally postponed:

- Authentication
- Multi-user support
- Cloud deployment
- OCR
- Image understanding
- Multi-modal RAG
- Background workers
- Distributed vector databases
- Fine-tuning models

These features may be introduced in later milestones.

---

## 5. Target Users

Current Version

- Single user
- Local desktop usage
- Development environment

Future

- Teams
- Shared knowledge bases
- Cloud deployment

---

## 6. Technology Stack

## Backend

- Python
- FastAPI
- LangChain
- ChromaDB
- HuggingFace Embeddings (BAAI/bge-base-en-v1.5)
- Groq (current LLM provider: llama-3.1-8b-instant)
- rank-bm25 (BM25 lexical search)
- sentence-transformers (Cross-encoder reranking)
- LangGraph (future evaluation)
- SQLite (future)

## Frontend

- React
- TypeScript
- Vite
- Tailwind CSS

---

## 7. Project Milestones

---

## Milestone 1 — Backend Foundation ✅

Deliverables

- Modular backend architecture
- PDF upload
- Text extraction
- Chunking
- Embeddings
- ChromaDB integration
- Retrieval
- Chat endpoint
- Streaming endpoint
- Source citations
- Document management
- Standardized error handling
- Backend documentation

Status

Completed

---

## Milestone 2 — Frontend Foundation ✅

Deliverables

- React application
- Upload workflow
- Chat interface
- Streaming responses
- Citation cards
- Responsive layout
- Document list
- Delete workflow
- API integration
- Error handling

Status

Completed

---

## Milestone 3 — Retrieval Intelligence ✅

Goal

Improve retrieval quality before expanding agent capabilities.

Completed

- Retrieval Configuration
- Maximum Marginal Relevance (MMR)
- Metadata filtering
- **Hybrid Retrieval (Dense + BM25 with Reciprocal Rank Fusion)**
- **Retrieval Strategy Pattern (Similarity, MMR, Hybrid)**
- **Centralized Retrieval Configuration in RetrievalConfig**
- **Retrieval Metadata for debugging and evaluation**
- **Query Rewriting**
- **Cross-Encoder Reranking**
- **Prompt Improvements**
- **Offline Retrieval Evaluation Framework**
- **BM25 Lexical Search**
- **Reciprocal Rank Fusion (RRF)**
- **Provider Abstraction Layer (backend/providers/)**

Planned

- Better chunking strategies

---

## Milestone 4 — Agent Foundations ✅

Goal

Transform the application into a true Agentic RAG platform.

Completed

- ToolExecutor with multi-iteration orchestration loop
- ConversationState for per-request state tracking
- Dynamic tool registry (tool_registry.py + tools/ package)
- Native multi-tool calling via LLM bind_tools()
- Streaming tool events
- Configurable safety limits (MAX_TOOL_ITERATIONS, MAX_TOOLS_PER_RESPONSE)
- Graceful tool error handling (unknown tools, exceptions)
- Provider-independent agent layer (via backend/providers/)
- retrieve_context tool
- list_documents tool (delegates to Document Service)
- search_by_filename tool (delegates to Document Service)
- Agent streaming tests
- Tool orchestration tests

Current Tools

- retrieve_context
- list_documents
- search_by_filename

Future Tools

- summarize_document
- search_by_metadata
- web_search
- calculator

---

## Milestone 5 — User Experience ✅

Goal

Polish the user experience with settings, conversation management, improved citations, and code cleanup.

Completed

- Settings infrastructure (SettingsContext, settingsService, localStorage persistence)
- Settings UI panels (General: confirm-before-delete toggle, Retrieval: show-citations toggle, About: version + reset)
- Conversation management (ConversationContext, reset with confirmation dialog)
- Conversation summary header (message count, new chat button)
- Citation experience (expand/collapse, clipboard actions, deduplication)
- CitationViewModel for citation state management
- Citation utility functions (citationUtils: deduplicate, group by document)
- Streaming cleanup (scroll behavior, partial token edge case)
- Polish pass (dead code removal, import cleanup, React.memo, UploadCard animations)
- Frontend E2E tests for upload scenarios

---

## Milestone 6 — Advanced Agentic RAG ⏳

Goal

Improve the intelligence and autonomy of the Agent with advanced retrieval strategies, agent reasoning capabilities, and new tools.

### New Tools

- summarize_document — LLM-based document summarization
- search_by_metadata — Filter documents by metadata fields

### Agent Improvements

- Reflection — Agent reviews its own outputs for quality
- Planning — Agent decomposes complex queries into sub-tasks
- Multi-step reasoning — Chain multiple tool calls coherently
- Reasoning traces — Visible chain-of-thought for debugging
- Agent observability — Tracing, metrics, and monitoring for tool execution

### Retrieval

- Multi-query retrieval — Generate multiple query variations for better recall
- Parent Document Retrieval — Retrieve chunks, return full document context
- Context Compression — Condense retrieved chunks to fit more relevant information
- Adaptive chunking — Dynamic chunk sizes based on content structure

### Infrastructure

- Multiple embedding providers
- Multiple LLM providers
- Conversation memory with persistence
- Background indexing
- Monitoring and tracing (LangFuse / LangSmith)

---

## Milestone 7 — Multimodal Intelligence 📋

Goal

Enable the Agent to understand visual information inside documents.

### Image Processing

- Image extraction from PDFs
- Figure understanding
- Diagram understanding
- Chart understanding
- Table understanding
- OCR for scanned PDFs

### Prompting

- Multimodal prompt construction
- Vision context formatting

### Agent

- Visual reasoning over extracted images
- Visual citations (image sources with page references)

### Infrastructure

- Vision-capable LLM provider abstraction
- Unified multimodal retrieval (text + images share a single RetrievalResult)
- Provider-agnostic vision integration

---

## Milestone 8 — Web Search & External Knowledge 📋

Goal

Allow the Agent to answer questions requiring information beyond uploaded documents.

### Tools

- web_search — External knowledge retrieval via search providers
- Search provider abstraction (pluggable backend: SerpAPI, Bing, Brave, etc.)

### Agent

- Intelligent fallback to web search when local retrieval is insufficient
- Confidence-aware tool selection
- Configurable web search enable/disable

### Responses

- Document + Web answer synthesis
- Source attribution for web results
- Freshness-aware answers (timestamps for web-sourced content)

---

## Milestone 9 — GraphRAG & Internal Knowledge Engine 📋

Goal

Transform isolated document chunks into an interconnected knowledge graph capable of relationship-aware retrieval and reasoning.

### Graph Construction

- Entity extraction
- Relationship extraction
- Automatic graph generation
- Cross-document linking
- Incremental graph updates
- Graph versioning

### Knowledge Graph

Support nodes representing:

- Concepts
- People
- Organizations
- APIs
- Classes
- Files
- Components
- Documents

Support edges representing:

- references
- depends_on
- implements
- calls
- extends
- belongs_to
- mentions

### Retrieval

- Graph traversal
- Entity lookup
- Relationship lookup
- Multi-hop retrieval
- Neighbor expansion
- Hybrid Vector + Graph retrieval
- Graph-aware reranking

### Agent

New planned tools:

- graph_search
- entity_lookup
- relationship_lookup
- graph_explorer
- knowledge_summary

### Internal Wiki

The knowledge graph becomes an automatically generated internal wiki capable of answering relationship-based questions across the document corpus.

---

## 8. Design Principles

The project should always prioritize

- Understanding over abstraction
- Simplicity over cleverness
- Modularity over shortcuts
- Readability over compactness
- Provider independence
- Tool-oriented architecture
- Incremental development
- Production-style engineering

---

## 9. Success Criteria

The MVP is complete when a user can

1. Upload one or more PDF documents.
2. Ask questions about uploaded documents.
3. Receive streamed answers grounded in retrieved context.
4. View source citations (expand/collapse, clipboard).
5. Configure retrieval settings (mode, top-K, reranking, temperature).
6. Manage uploaded documents (list, delete).
7. Reset conversation with confirmation.
8. Use the application entirely through the browser.
9. Run the application locally with minimal setup.

---

## 10. Long-Term Vision

The project should evolve into a reusable **Agentic RAG Platform** rather than a single-purpose chatbot.

Future capabilities should be added by introducing new tools and retrieval strategies rather than redesigning the architecture.

The long-term goal is a modular AI platform where the agent can reason over documents, invoke multiple tools, integrate external knowledge sources, and support increasingly autonomous workflows while preserving a clean, layered architecture.