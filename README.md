<p align="center">
  <br/>
  <img src="https://img.shields.io/badge/Python-3.12-3776AB?style=for-the-badge&logo=python&logoColor=white"/>
  <img src="https://img.shields.io/badge/FastAPI-0.138-009688?style=for-the-badge&logo=fastapi&logoColor=white"/>
  <img src="https://img.shields.io/badge/LangChain-1.3-1C3C3C?style=for-the-badge&logo=langchain&logoColor=white"/>
  <img src="https://img.shields.io/badge/ChromaDB-1.5-FF6B6B?style=for-the-badge&logo=chromadb&logoColor=white"/>
  <img src="https://img.shields.io/badge/Gemini-2.5-4285F4?style=for-the-badge&logo=google&logoColor=white"/>
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

- **PDF Loading & Chunking** — Load documents from web URLs, split into chunks using `RecursiveCharacterTextSplitter`.
- **Vector Embeddings** — Generate embeddings via Google Gemini models and store them in ChromaDB.
- **Semantic Retrieval** — Retrieve the most relevant document chunks for a user query.
- **LLM-Powered Answers** — Generate answers using Google Gemini (2.5 Flash), constrained exclusively to retrieved context.
- **Health Check API** — `GET /health` endpoint for service monitoring.
- **Chat API** — `POST /chat` endpoint that accepts a user message and returns a grounded answer with tool call metadata.
- **Modular RAG Pipeline** — Loader → Splitter → Embeddings → Vector Store → Retriever → Prompt Builder → Agent.
- **Clean FastAPI Structure** — Layered architecture with thin API routes, service layer coordination, and isolated RAG modules.

### Planned

- PDF upload via `multipart/form-data`
- Document management (list, delete)
- Streaming chat responses (SSE)
- React + TypeScript frontend
- Conversation memory with SQLite
- Retrieval improvements (MMR, query rewriting)
- Advanced RAG (hybrid search, reranking, metadata filtering)

---

## Architecture

```
                        +----------------------+
                        |    React Frontend     |  (planned)
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
      Loader      Splitter    Embeddings   Retriever   Prompt Builder
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
  Embeddings                Retriever
   ↓                             ↓
  ChromaDB                  Prompt Builder
                                 ↓
                               LLM (Gemini)
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
| [Google Gemini](https://ai.google.dev/) | Embeddings (`gemini-embedding-2-preview`) and LLM (`gemini-2.5-flash`) |
| [Pydantic](https://docs.pydantic.dev/) | Request/response validation and serialization |
| [Uvicorn](https://www.uvicorn.org/) | ASGI server |

</details>

<details>
<summary><strong>Frontend (planned)</strong></summary>

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
│   │   ├── chat.py                     # POST /chat endpoint
│   │   ├── health.py                   # GET /health endpoint
│   │   ├── documents.py                # (planned) Document management
│   │   └── upload.py                   # (planned) PDF upload
│   │
│   ├── services/
│   │   └── rag_service.py              # RAG orchestration layer
│   │
│   ├── rag/
│   │   ├── agent.py                    # LLM agent setup and execution
│   │   ├── embeddings.py               # Embedding model initialization
│   │   ├── loader.py                   # Document loading (web, PDF)
│   │   ├── prompts.py                  # System prompt construction
│   │   ├── retriever.py                # Semantic retrieval logic
│   │   ├── splitter.py                 # Text chunking configuration
│   │   └── vector_store.py             # ChromaDB operations
│   │
│   ├── models/
│   │   └── schemas.py                  # Pydantic models (ChatRequest, ChatResponse, HealthResponse)
│   │
│   └── storage/
│       └── chroma_langchain_db/        # Persistent vector store
│
├── docs/
│   ├── ARCHITECTURE.md                 # System architecture
│   ├── API_SPEC.md                     # API contract
│   ├── DECISIONS.md                    # Architectural Decision Records
│   ├── PROJECT_PLAN.md                 # Project planning
│   ├── RAG_PIPELINE.md                 # RAG pipeline details
│   └── TODO.md                         # Active task tracking
│
├── venv/                               # Virtual environment (local)
├── AGENTS.md                           # AI coding agent instructions
├── .gitignore
├── .env                                # Environment variables (local, not tracked)
└── README.md                           # This file
```

---

## Getting Started

### Prerequisites

- Python 3.12+
- A [Google Gemini API key](https://aistudio.google.com/apikey)

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
            langchain-google-genai langchain-text-splitters \
            chromadb beautifulsoup4 pypdf python-dotenv pydantic

# 4. Configure environment
echo "GOOGLE_API_KEY=your-api-key-here" > .env

# 5. Run the backend
uvicorn backend.app:app --reload
```

The API will be available at `http://localhost:8000`.

- Interactive API docs: [`http://localhost:8000/docs`](http://localhost:8000/docs)
- Alternative ReDoc: [`http://localhost:8000/redoc`](http://localhost:8000/redoc)
- Health check: [`http://localhost:8000/health`](http://localhost:8000/health)

---

## Development Roadmap

| Milestone | Status | Description |
|-----------|--------|-------------|
| **1 — Backend Foundation** | 🏗️ In Progress | FastAPI structure, upload/chat endpoints, document management, vector store |
| **2 — React Frontend** | ⏳ Not Started | React app with upload, chat, and document management pages |
| **3 — Retrieval Improvements** | ⏳ Not Started | MMR, query rewriting, better chunk selection |
| **4 — Conversation Memory** | ⏳ Not Started | SQLite, chat history, persistent conversations |
| **5 — UI & UX** | ⏳ Not Started | Dark mode, loading states, settings, error handling |
| **6 — Advanced RAG** | ⏳ Not Started | Hybrid search, reranking, metadata filtering, multi-provider |

> **Current focus:** Milestone 1 — the backend is being refactored into a clean, modular architecture. PDF upload and document management endpoints are coming next.

---

## API Overview

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/health` | Health check — returns `{"status": "healthy"}` |
| `POST` | `/chat` | Send a message and receive a grounded answer |

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
      "input": "What is ReAct?",
      "output": "Source: {...}\nContent: ReAct is..."
    }
  ]
}
```

### Planned Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/documents/upload` | Upload a PDF for indexing |
| `GET` | `/documents` | List all indexed documents |
| `DELETE` | `/documents/{id}` | Remove a document and its vectors |
| `POST` | `/chat/stream` | Stream LLM response tokens via SSE |

---

## Future Enhancements

<details>
<summary><strong>Backend</strong></summary>

- [ ] PDF upload via `multipart/form-data`
- [ ] Document management (list, delete)
- [ ] Streaming chat responses (Server-Sent Events)
- [ ] Conversation memory with SQLite
- [ ] Hybrid search (dense + sparse)
- [ ] Cross-encoder reranking
- [ ] Metadata filtering
- [ ] Multiple embedding providers
- [ ] Multiple LLM providers
- [ ] Parent Document Retrieval
- [ ] Query rewriting
- [ ] Docker support
- [ ] CI/CD pipeline

</details>

<details>
<summary><strong>Frontend</strong></summary>

- [ ] React + TypeScript + Vite setup
- [ ] Drag-and-drop PDF upload
- [ ] Chat interface with streaming responses
- [ ] Document list and management
- [ ] Dark mode
- [ ] Markdown rendering with syntax highlighting
- [ ] Mobile-responsive layout

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
