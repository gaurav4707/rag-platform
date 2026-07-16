# RAG Agent - Agentic Retrieval-Augmented Generation Platform

A production-style Agentic RAG platform with PDF upload, semantic retrieval, and streaming responses.

## Architecture

- **Frontend**: React 18 + TypeScript + Vite + Tailwind CSS
- **Backend**: FastAPI + LangChain + ChromaDB
- **Embeddings**: BAAI/bge-base-en-v1.5 (HuggingFace)
- **LLM**: Groq (llama-3.1-8b-instant)

## Running the Application

```bash
# Backend
cd backend
python -m uvicorn app:app --reload --port 8000

# Frontend
cd frontend
npm install
npm run dev
```

## Running E2E Tests

The end-to-end test suite validates the PDF upload pipeline against a real backend.

```bash
cd frontend

# Run all tests headless
npm run test:e2e

# Run with Playwright UI
npm run test:e2e:ui

# Run headed (visible browser)
npm run test:e2e:headed

# View HTML report after test run
npx playwright show-report
```

### Test Scenarios

| Test | Description | Expected |
|------|-------------|----------|
| Test 1 | Valid PDF upload | Success toast, document appears, uploader resets |
| Test 2 | Blank PDF rejected | Error toast "Document Processing Failed", no document added |
| Test 3 | Corrupted PDF rejected | Error toast "Invalid PDF", no document added |
| Test 4 | Duplicate PDF rejected | Info toast "Document Already Exists", no duplicate added |
| Test 5 | Network interruption | Error toast "Connection Lost", uploader resets |
| Test 6 | 5 sequential uploads | No stuck state, correct toast counts, correct document list |

### Test Fixtures

Static PDF fixtures in `frontend/tests/fixtures/`:
- `valid.pdf` - Valid PDF with text content
- `valid2.pdf` - Second valid PDF with different content
- `blank.pdf` - Valid PDF structure, no extractable text
- `corrupted.pdf` - Invalid PDF binary
- `duplicate.pdf` - Copy of `valid.pdf` (same SHA256)

### Requirements

- Backend must be running on `http://localhost:8000` (auto-started by Playwright)
- Frontend dev server on `http://localhost:5173` (auto-started by Playwright)
- Chromium browser (installed via `npx playwright install chromium`)