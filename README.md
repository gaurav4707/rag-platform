# RAG Agent — Agentic Retrieval-Augmented Generation Platform

A production-style **Agentic RAG** platform that enables users to upload PDF documents, ask questions via an intelligent conversational agent, and receive grounded answers with source citations.

Unlike traditional RAG, an **LLM-powered Agent** selects and invokes tools to answer requests, supporting multi-step reasoning across document search and retrieval.

---

## Architecture

```
Frontend → API → Services → Agent → Tool Registry → Tools → Retriever → Vector Store
```

| Layer | Technology |
|-------|------------|
| **Frontend** | React 18 + TypeScript + Vite + Tailwind CSS |
| **API** | FastAPI (thin REST endpoints) |
| **Services** | Document Service, RAG Service |
| **Agent** | ToolExecutor with multi-iteration orchestration loop |
| **Tools** | retrieve_context, list_documents, search_by_filename |
| **Retrieval** | Similarity, MMR, Hybrid (Dense + BM25 + RRF), Cross-Encoder Reranking |
| **Vector Store** | ChromaDB (persistent, local) |
| **Embeddings** | BAAI/bge-base-en-v1.5 (HuggingFace) |
| **LLM** | Groq (llama-3.1-8b-instant) |

---

## Current Capabilities

- **PDF Upload** — Drag-and-drop upload with validation, SHA-256 deduplication
- **Document Indexing** — Text extraction, chunking, embedding, vector storage
- **Semantic Retrieval** — Similarity search, MMR, Hybrid (Dense + BM25 + RRF)
- **Query Rewriting** — LLM-based conversational query rewriting with heuristic skip
- **Cross-Encoder Reranking** — Local HF model for relevance scoring
- **Agentic Tool Orchestration** — LLM decides which tools to invoke:
  - `retrieve_context` — Semantic document retrieval
  - `list_documents` — List all indexed documents
  - `search_by_filename` — Find documents by filename
- **Streaming Responses** — Real-time token streaming with tool event metadata
- **Source Citations** — Expand/collapse citations with clipboard actions, deduplication
- **Document Management** — List, delete, duplicate detection
- **Settings** — Confirm-before-delete, show citations toggle, localStorage persistence, about panel
- **Conversation Management** — Context-based reset with confirmation, message count, summary header
- **Retrieval Evaluation** — CLI-based offline benchmarking (Precision@K, Recall@K, MRR, NDCG, MAP, F1)

---

## Milestone Status

| Milestone | Status |
|-----------|--------|
| 1. Backend Foundation | ✅ Complete |
| 2. Frontend Foundation | ✅ Complete |
| 3. Retrieval Intelligence | ✅ Complete |
| 4. Agent Foundations | ✅ Complete |
| 5. User Experience | ✅ Complete |
| 6. Advanced Agentic RAG | ⏳ In Progress |
| 7. Multimodal Intelligence | 📋 Planned |
| 8. Web Search & External Knowledge | 📋 Planned |
| 9. GraphRAG & Internal Knowledge Engine | 📋 Planned |

---

## Setup

### Backend

```bash
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -r ../requirements.txt

# Set your Groq API key
Set-Content -Path .env -Value "GROQ_API_KEY=your_key"

# Run command to install Embeddings Model
python -c "from sentence_transformers import SentenceTransformer; SentenceTransformer('BAAI/bge-base-en-v1.5')"             

# Run the server
python -m uvicorn app:app --reload --port 8000
```

### Frontend

```bash
cd frontend
npm install
npm run dev
```

Open `http://localhost:5173` in your browser.

---

## Testing

### Backend Tests

```bash
# Run all backend tests
cd backend
python -m pytest tests/ -v

# Run with coverage
python -m pytest tests/ --cov=backend --cov-report=term
```

### Frontend E2E Tests

```bash
cd frontend

# Run all tests headless
npm run test:e2e

# Run with Playwright UI
npm run test:e2e:ui

# Run headed (visible browser)
npm run test:e2e:headed
```

### E2E Test Scenarios

| Test | Description |
|------|-------------|
| Valid PDF upload | Success toast, document appears, uploader resets |
| Blank PDF rejected | Error toast, no document added |
| Corrupted PDF rejected | Error toast "Invalid PDF" |
| Duplicate PDF rejected | Info toast "Document Already Exists" |
| Network interruption | Error toast "Connection Lost" |
| 5 sequential uploads | No stuck state, correct counts |

---

## Benchmarking

Run retrieval quality evaluations:

```bash
python -m backend.evaluation.cli \
    --dataset backend/evaluation/data/test_queries.json \
    --top-k 5 \
    --search-type hybrid
```

---

## Project Structure

```
├── backend/
│   ├── api/             # REST endpoints (thin)
│   ├── services/        # Business logic
│   ├── rag/             # RAG engine
│   │   ├── agent.py     # Entry points
│   │   ├── tool_executor.py  # Orchestration loop
│   │   ├── tools/       # Tool implementations
│   │   ├── retriever.py # Retrieval orchestration
│   │   ├── prompts.py   # Prompt construction
│   │   ├── citations.py # Citation building
│   │   └── vector_store.py
│   ├── providers/       # LLM + Embedding factories
│   ├── models/          # Data models
│   ├── evaluation/      # Offline benchmarking
│   └── tests/           # Test suite (209+ tests)
├── frontend/            # React + TypeScript
│   ├── src/context/     # React context providers (Settings, Conversation)
│   ├── src/services/    # API clients, settings persistence, notifications
│   ├── src/utils/       # Shared utilities (citationUtils)
│   └── src/components/  # UI components (Chat, Settings, ui, Shell)
├── docs/                # Architecture documentation
└── storage/             # PDF + ChromaDB persistence
```

---

## Documentation

| Document | Description |
|----------|-------------|
| `docs/ARCHITECTURE.md` | System architecture and data flow |
| `docs/RAG_PIPELINE.md` | Complete RAG pipeline specification |
| `docs/PROJECT_PLAN.md` | Milestone roadmap and status |
| `docs/API_SPEC.md` | Public API contract |
| `docs/DECISIONS.md` | Architecture Decision Records |
| `docs/CHANGELOG.md` | Version history and milestones |
| `AGENTS.md` | AI coding agent profiles and rules |

---

## License

MIT
