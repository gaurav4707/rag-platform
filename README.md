<p align="center">
  <br/>
  <img src="https://img.shields.io/badge/Python-3.12-3776AB?style=for-the-badge&logo=python&logoColor=white"/>
  <img src="https://img.shields.io/badge/FastAPI-0.138-009688?style=for-the-badge&logo=fastapi&logoColor=white"/>
  <img src="https://img.shields.io/badge/LangChain-1.3-1C3C3C?style=for-the-badge&logo=langchain&logoColor=white"/>
  <img src="https://img.shields.io/badge/ChromaDB-1.5-FF6B6B?style=for-the-badge&logo=chromadb&logoColor=white"/>
  <img src="https://img.shields.io/badge/HuggingFace-Embeddings-FF6B6B?style=for-the-badge&logo=huggingface&logoColor=white"/>
  <img src="https://img.shields.io/badge/Groq-LLM-FF6B6B?style=for-the-badge&logo=groq&logoColor=white"/>
  <br/>
  <img src="https://img.shields.io/badge/React-18-61DAFB?style=for-the-badge&logo=react&logoColor=white&labelColor=222"/>
  <img src="https://img.shields.io/badge/TypeScript-5-3178C6?style=for-the-badge&logo=typescript&logoColor=white"/>
  <img src="https://img.shields.io/badge/Vite-6-646CFF?style=for-the-badge&logo=vite&logoColor=white"/>
  <img src="https://img.shields.io/badge/Tailwind_CSS-4-06B6D4?style=for-the-badge&logo=tailwindcss&logoColor=white"/>
  <br/>
  <img src="https://img.shields.io/badge/License-MIT-yellow?style=for-the-badge"/>
</p>

<h1 align="center">RAG Platform</h1>

<p align="center">
  <strong>A production-style Retrieval-Augmented Generation platform</strong>
  <br/>
  Upload documents, index them into a vector database, and ask questions with grounded AI answers.
</p>

---

## Table of Contents

- [Overview](#overview)
- [Key Features](#key-features)
- [Architecture](#architecture)
- [Tech Stack](#tech-stack)
- [Project Structure](#project-structure)
- [Getting Started](#getting-started)
- [Development Roadmap](#development-roadmap)
- [API Overview](#api-overview)
- [Future Enhancements](#future-enhancements)
- [Design Principles](#design-principles)
- [Screenshots](#screenshots)
- [Contributing](#contributing)
- [License](#license)
- [Author](#author)

---

## Overview

**RAG Platform** is a local, single-user AI document assistant built for learning modern AI engineering. It lets you upload PDFs, index them into a local ChromaDB vector store, and ask questions — receiving answers grounded exclusively in your documents with citations.

The project prioritizes **understanding over abstraction**, **modularity over shortcuts**, and **clean architecture over rapid development**. Every component is deliberately chosen and intentionally composed, making it an ideal reference for anyone learning RAG systems.

---

## Key Features

### Implemented

- **PDF Loading & Chunking** — Extract text from PDFs and split into chunks using `RecursiveCharacterTextSplitter` with custom separators.
- **Vector Embeddings** — Generate embeddings via HuggingFace models (BAAI/bge-base-en-v1.5) and store them in ChromaDB.
- **Semantic Retrieval** — Retrieve the most relevant document chunks using similarity or MMR search.
- **Metadata Filtering** — Filter retrieval results by document_id, filename, or page.
- **Strategy-Based Retrieval** — Choose between Similarity, MMR, and Hybrid via `RetrievalConfig`.
- **Hybrid Retrieval** — Dense + BM25 lexical search combined with Reciprocal Rank Fusion (RRF).
- **BM25 Lexical Search** — In-memory `rank-bm25` index rebuilt from ChromaDB on document changes.
- **Reciprocal Rank Fusion** — Parameter-free fusion of dense and sparse results (default k=60).
- **Query Rewriting** — LLM-based query rewriting for conversational/follow-up queries with heuristic skip.
- **Cross-Encoder Reranking** — Local `cross-encoder/ms-marco-MiniLM-L-6-v2` reranker with lazy singleton and batch inference.
- **Agentic RAG** — LLM-powered agent with tool registry, tool orchestration, and streaming execution.
- **Document Management** — Upload, list, and delete PDFs through dedicated API endpoints.
- **LLM-Powered Answers** — Generate answers using Groq (llama-3.1-8b-instant), grounded in retrieved context with citations.
- **Health Check API** — `GET /health` endpoint for service monitoring.
- **Chat API** — `POST /chat` endpoint returning grounded answers with source citations and tool call metadata.
- **Streaming Chat** — `POST /chat/stream` for token-by-token streaming via Server-Sent Events.
- **Provider Abstraction Layer** — Centralized factory for embedding and LLM providers via `backend/providers/`.
- **Modular RAG Pipeline** — Loader → Splitter → Embeddings → Vector Store → Retriever → Agent.
- **Clean FastAPI Structure** — Layered architecture with thin API routes, service layer coordination, and isolated RAG modules.
- **Comprehensive Tests** — 127 automated tests covering retrieval strategies, configuration, metadata filtering, hybrid retrieval, query rewriting, reranking, and integration.
- **Offline Evaluation Framework** — CLI-based retrieval evaluation with Precision@K, Recall@K, Hit Rate, MRR, MAP, NDCG, F1 metrics.

### Planned

- Conversation memory with SQLite
- Multiple embedding providers
- Multiple LLM providers
- Parent Document Retrieval
- Context Compression
- Web Search tool

---

## Architecture

```
                          +----------------------+
                          |    React Frontend     |
                          +----------+-----------+
                                     |
                              HTTP / Streaming
                                     |
                          +----------v-----------+
                          |    FastAPI API Layer   |  Thin routes, no business logic
                          +----------+-----------+
                                     |
                           Application Services
                                     |
                 +--------------------+--------------------+
                 |                    |                    |
          Document Service      Chat Service        RAG Service
                 |                    |                    |
                 +--------------------+--------------------+
                                     |
                               RAG Engine
                                     |
            +------------+-----------+-----------+------------+
            |            |           |           |            |
        Loader      Splitter    Embeddings   Retriever   Agent / LLM
            |            |           |           |            |
            +------------+-----------+-----------+------------+
                                     |
                               Vector Store
                                     |
                                ChromaDB
```

### Data Flow

```
  Upload                          Chat
  ───────────                     ───────────
  PDF                      User Question
   ↓                             ↓
  Loader                    Chat API
   ↓                             ↓
  Splitter                  RAG Service
   ↓                             ↓
  Embeddings                Agent
   ↓                             ↓
  ChromaDB                  Tool Registry
                                   ↓
                             retrieve_context
                                   ↓
                             Retriever (Strategy)
                               ├── Similarity
                               ├── MMR
                               └── Hybrid (Dense + BM25 + RRF)
                                   ↓
                             Vector Store / ChromaDB
                                   ↓
                             RetrievalResult
                               ├──► Prompt Builder
                               ├──► Citation Builder
                               └──► Agent
                                   ↓
                             LLM
                                   ↓
                             Stream Response
```

### Layer Responsibilities

| Layer | Role |
|-------|------|
| **API Layer** | Receive requests, validate input, return responses. No business logic. |
| **Service Layer** | Orchestrate workflows, coordinate RAG components, manage documents and conversations. |
| **RAG Layer** | Load, chunk, embed, retrieve, build prompts, and interact with the LLM. |
| **Storage Layer** | Persist vectors (ChromaDB) and uploaded files. |

Dependencies always flow **downward**: API → Services → RAG → Storage.

---

## Tech Stack

<details>
<summary><strong>Backend</strong></summary>

| Technology | Purpose |
|------------|---------|
| [Python 3.12](https://www.python.org/) | Runtime |
| [FastAPI](https://fastapi.tiangolo.com/) | API framework with automatic OpenAPI docs |
| [LangChain](https://www.langchain.com/) | RAG orchestration, agent framework |
| [ChromaDB](https://www.trychroma.com/) | Local vector database |
| [HuggingFace](https://huggingface.co/) | Embeddings (`BAAI/bge-base-en-v1.5`) |
| [Groq](https://groq.com/) | LLM (`llama-3.1-8b-instant`) |
| [rank-bm25](https://github.com/dorianbrown/rank_bm25) | BM25 lexical search |
| [sentence-transformers](https://www.sbert.net/) | Cross-encoder reranking |
| [Pydantic](https://docs.pydantic.dev/) | Request/response validation and serialization |
| [Uvicorn](https://www.uvicorn.org/) | ASGI server |

</details>

<details>
<summary><strong>Frontend</strong></summary>

| Technology | Purpose |
|------------|---------|
| [React 18](https://react.dev/) | UI framework |
| [TypeScript](https://www.typescriptlang.org/) | Type safety |
| [Vite](https://vite.dev/) | Build tool and dev server |
| [Tailwind CSS](https://tailwindcss.com/) | Utility-first styling |

</details>

---

## Project Structure

```
rag-platform/
│
├── backend/
│   ├── app.py                          # FastAPI entry point
│   ├── config.py                       # All project-wide constants
│   │
│   ├── api/
│   │   ├── chat.py                     # POST /chat, /chat/stream endpoints
│   │   ├── health.py                   # GET /health endpoint
│   │   ├── documents.py                # Document management endpoints
│   │   ├── upload.py                   # PDF upload endpoint
│   │   └── errors.py                   # Standardized error handlers
│   │
│   ├── services/
│   │   ├── rag_service.py              # Chat orchestration layer
│   │   └── document_service.py         # Document lifecycle management
│   │
│   ├── rag/
│   │   ├── agent.py                    # LLM agent setup and execution
│   │   ├── tool_registry.py            # Tool registration for the agent
│   │   ├── retriever.py                # Retrieval strategy orchestration
│   │   ├── retrieval_config.py         # RetrievalConfig dataclass
│   │   ├── retrieval_strategies.py     # Strategy Pattern (Similarity, MMR, Hybrid)
│   │   ├── bm25.py                     # BM25 lexical retrieval
│   │   ├── hybrid_retriever.py         # BM25 index management utilities
│   │   ├── reranker.py                 # Cross-encoder reranking
│   │   ├── query_rewriter.py           # LLM-based query rewriting
│   │   ├── vector_store.py             # ChromaDB operations and retrieval
│   │   ├── loader.py                   # PDF text extraction
│   │   ├── splitter.py                 # Text chunking
│   │   ├── prompts.py                  # System prompt construction
│   │   └── citations.py                # Source citation builder
│   │
│   ├── providers/
│   │   ├── __init__.py                 # Exports get_embedding_provider, get_llm
│   │   ├── embeddings.py               # Embedding provider factory
│   │   ├── llm.py                      # LLM provider factory
│   │   └── exceptions.py               # ProviderConfigurationError
│   │
│   ├── evaluation/
│   │   ├── __init__.py
│   │   ├── README.md
│   │   ├── cli.py                      # CLI for offline evaluation
│   │   ├── evaluator.py                # Evaluation orchestration
│   │   ├── dataset.py                  # Load/save JSON datasets
│   │   ├── metrics.py                  # Precision@K, Recall@K, MRR, MAP, NDCG, F1
│   │   ├── models.py                   # Evaluation data structures
│   │   └── reports/
│   │
│   ├── models/
│   │   ├── schemas.py                  # Public API Pydantic models
│   │   └── rag_models.py               # Internal RAG domain models
│   │
│   ├── tests/
│   │   ├── __init__.py
│   │   ├── conftest.py                 # Shared test fixtures
│   │   ├── test_retriever.py           # 110+ retriever tests
│   │   ├── test_prompts.py             # 22 prompt builder tests
│   │   └── test_evaluation_metrics.py  # 23 evaluation metrics tests
│   │
│   └── storage/
│       └── chroma_langchain_db/        # Persistent vector store
│
├── frontend/                           # React + TypeScript + Vite app
│
├── docs/
│   ├── ARCHITECTURE.md                 # System architecture
│   ├── API_SPEC.md                     # API contract
│   ├── DECISIONS.md                    # Architectural Decision Records
│   ├── PROJECT_PLAN.md                 # Project planning
│   ├── RAG_PIPELINE.md                 # RAG pipeline details
│   └── TODO.md                         # Active task tracking
│
├── .venv/                              # Virtual environment (local)
├── AGENTS.md                           # AI coding agent instructions
├── .gitignore
├── .env                                # Environment variables (local, not tracked)
└── README.md                           # This file
```

---

## Getting Started

### Prerequisites

- Python 3.12+
- A [Groq API key](https://console.groq.com/keys)

### Setup

```bash
# 1. Clone the repository
git clone https://github.com/your-username/rag-platform.git
cd rag-platform

# 2. Create a virtual environment
python3 -m venv venv
source venv/bin/activate    # On Windows: venv\Scripts\activate

# 3. Install dependencies
pip install fastapi uvicorn[standard] langchain langchain-chroma \
            langchain-huggingface langchain-text-splitters \
            chromadb rank-bm25 sentence-transformers \
            beautifulsoup4 pypdf python-dotenv pydantic

# 4. Configure environment
echo "GROQ_API_KEY=your-api-key-here" > .env

# 5. Run the backend
uvicorn backend.app:app --reload
```

The API will be available at `http://localhost:8000`.

- Interactive API docs: [`http://localhost:8000/docs`](http://localhost:8000/docs)
- Alternative ReDoc: [`http://localhost:8000/redoc`](http://localhost:8000/redoc)
- Health check: [`http://localhost:8000/health`](http://localhost:8000/health)

---

## Running Tests

Run the test suite with pytest:

```bash
# Run all tests with verbose output
pytest

# Run tests for a specific module
pytest backend/tests/test_prompts.py

# Run with extra verbosity
pytest -v
```

### Generating Coverage Reports

The project uses **pytest-cov** and **coverage.py** for coverage reporting.

**Terminal Summary (with missing lines):**

```bash
pytest --cov=backend --cov-report=term-missing
```

**HTML Report (open `htmlcov/index.html` in browser):**

```bash
pytest --cov=backend --cov-report=html
```

**XML Report (for CI integration):**

```bash
pytest --cov=backend --cov-report=xml
```

**All reports at once:**

```bash
pytest --cov=backend --cov-report=term-missing --cov-report=html --cov-report=xml
```

Coverage reports are generated in:

- `htmlcov/` — HTML report (open `htmlcov/index.html`)
- `coverage.xml` — XML report for CI/CD
- Terminal output — Summary and missing lines

### Coverage Configuration

Coverage is configured in `pyproject.toml` under `[tool.coverage.run]`:

- **Source**: `backend` package
- **Branch coverage**: Enabled
- **Excluded**: `tests/`, `__pycache__/`, `.venv/`, `venv/`, `build/`, `dist/`, `htmlcov/`, `*.egg-info/`
- **Relative paths**: Enabled for readability

---

## Development Roadmap

| Milestone | Status | Description |
|-----------|--------|-------------|
| **1 — Backend Foundation** | ✅ Completed | FastAPI structure, upload/chat endpoints, document management, vector store |
| **2 — React Frontend** | ✅ Completed | React app with upload, chat, and document management pages |
| **3 — Retrieval Intelligence** | ✅ Completed | Hybrid retrieval, MMR, metadata filtering, query rewriting, reranking, evaluation |
| **4 — Agent Foundations** | ✅ Completed | Tool registry, agent orchestration, streaming tool execution |
| **5 — User Experience** | ⏳ Planned | Dark mode, loading states, settings, error handling |
| **6 — Advanced Agentic RAG** | ⏳ Planned | Hybrid search, reranking, query rewriting, multi-provider |

> **Current focus:** Milestone 5 — User Experience. Settings page, conversation history, better accessibility.

---

## API Overview

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/health` | Health check — returns `{"status": "healthy"}` |
| `POST` | `/chat` | Send a message and receive a grounded answer |
| `POST` | `/chat/stream` | Stream LLM response tokens via SSE |
| `POST` | `/documents/upload` | Upload a PDF for indexing |
| `GET` | `/documents` | List all indexed documents |
| `DELETE` | `/documents/{id}` | Remove a document and its vectors |

### Example Request

```bash
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "What is ReAct?"}'
```

### Example Response

```json
{
  "answer": "ReAct is a framework that combines reasoning and acting...",
  "tool_calls": [
    {
      "tool_name": "retrieve_context",
      "input": "What is RAG?",
      "output": "Source: {...}\nContent: ReAct is..."
    }
  ]
}
```

---

## Future Enhancements

<details>
<summary><strong>Backend</strong></summary>

- [ ] Conversation memory with SQLite
- [ ] Multiple embedding providers
- [ ] Multiple LLM providers
- [ ] Parent Document Retrieval
- [ ] Docker support
- [ ] CI/CD pipeline

</details>

<details>
<summary><strong>Frontend</strong></summary>

- [ ] Dark mode
- [ ] Settings page
- [ ] Conversation history
- [ ] Accessibility audit

</details>

---

## Design Principles

This project is guided by a clear set of architectural rules:

- **Single Responsibility** — Every file and function has one clear purpose.
- **Clean Architecture** — API → Services → RAG → Storage. Dependencies flow downward.
- **Thin Endpoints** — API routes validate input and delegate to services. No business logic in routes.
- **Explicit over Clever** — Prefer readable, descriptive code over clever one-liners.
- **Modular RAG Pipeline** — Each stage (loader, splitter, embeddings, retriever, prompts) is isolated.
- **Incremental Building** — Small, focused changes over large rewrites.
- **No Premature Optimization** — Build it clean first, measure, then optimize.
- **Understanding > Abstraction** — Choose solutions that improve comprehension, even if they require slightly more code.

See [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md) and [`docs/DECISIONS.md`](docs/DECISIONS.md) for the full architectural rationale.

---

## Screenshots

<p align="center">
  <em>Screenshots coming soon. The project is currently in the backend development phase.</em>
</p>

<!--

Once the frontend is built, add screenshots here:

<p align="center">
  <img src="docs/screenshots/chat.png" alt="Chat Interface" width="700"/>
  <br/>
  <em>Chat interface with streamed responses and source citations.</em>
</p>

<p align="center">
  <img src="docs/screenshots/upload.png" alt="Upload Interface" width="700"/>
  <br/>
  <em>Drag-and-drop PDF upload.</em>
</p>

<p align="center">
  <img src="docs/screenshots/documents.png" alt="Document List" width="700"/>
  <br/>
  <em>Document management view.</em>
</p>

-->

---

## Contributing

This is primarily a learning project, but contributions, ideas, and discussions are welcome.

If you'd like to contribute:

1. Fork the repository.
2. Create a feature branch (`git checkout -b feature/your-feature`).
3. Commit your changes (`git commit -m 'Add some feature'`).
4. Push to the branch (`git push origin feature/your-feature`).
5. Open a Pull Request.

Please ensure your changes follow the existing architecture. If you're considering a significant change, open an issue first to discuss it.

---

## License

Distributed under the **MIT License**. See `LICENSE` for more information.

---

## Author

Built as a learning project in modern AI engineering.

**Key areas explored:**

- Retrieval-Augmented Generation (RAG) systems
- Modular software architecture for AI applications
- FastAPI and backend API design
- LangChain agent and retrieval pipelines
- Vector databases and semantic search
- Prompt engineering and LLM integration

---

<p align="center">
  <sub>Built for learning, designed for understanding.</sub>
</p>