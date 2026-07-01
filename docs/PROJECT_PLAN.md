# PROJECT_PLAN.md

# AI Document Assistant (RAG Platform)

## 1. Project Overview

### Goal

Build a production-style Retrieval-Augmented Generation (RAG) application that allows users to upload PDF documents and interact with them through a conversational interface.

The project is designed primarily for learning modern AI engineering practices while maintaining a clean, modular architecture suitable for future expansion.

---

## 2. Objectives

### Primary Objectives

* Learn RAG architecture from end to end.
* Build a clean backend using LangChain and FastAPI.
* Build a modern frontend using React.
* Understand every architectural decision instead of relying on framework abstractions.
* Keep the project modular and easy to extend.

### Secondary Objectives

* Produce a portfolio-quality project.
* Support future advanced RAG features without major refactoring.
* Make the project understandable for both humans and AI coding agents.

---

## 3. Current Scope (MVP)

### Backend — Implemented

* Upload PDF documents
* Extract text
* Chunk documents
* Generate embeddings
* Store vectors in ChromaDB
* Retrieve relevant chunks
* Generate answers using an LLM
* Stream responses
* Return source citations
* List indexed documents
* Delete documents
* Standardized error codes

### Frontend

* Not yet implemented

---

## 4. Out of Scope (Initial Version)

The following features are intentionally postponed:

* Authentication
* Multi-user support
* Cloud deployment
* OCR
* Image understanding
* Multi-modal RAG
* Web search
* Graph RAG
* Hybrid search
* Metadata filtering
* Reranking
* Conversation persistence
* Mobile support

These may be added after the MVP.

---

## 5. Target Users

Current version:

* Single user
* Local desktop usage
* Development environment

No production deployment is planned during the initial development.

---

## 6. Technology Stack

### Backend

* Python
* FastAPI
* LangChain
* ChromaDB
* HuggingFace Embeddings (BAAI/bge-base-en-v1.5)
* Groq LLM (llama-3.1-8b-instant)
* LangGraph (future)
* SQLite (future)

### Frontend

* React
* TypeScript
* Vite
* Tailwind CSS

---

## 7. Project Milestones

### Milestone 1 — In Progress

Backend Foundation

Deliverables:

* Modular architecture — Done
* Upload endpoint — Done
* Chat endpoint — Done
* List documents endpoint — Done
* Delete document endpoint — Done
* Source citations — Done
* Standardized error handling — Done
* Documentation updated — Done

Manual verification required before marking as complete.

---

### Milestone 2

Frontend

Deliverables:

* React application
* Upload page
* Chat page
* Document list

---

### Milestone 3

Improved Retrieval

Deliverables:

* Better retrieval strategy
* Cleaner prompts
* Source improvements

---

### Milestone 4

Conversation Memory

Deliverables:

* Chat history
* Persistent conversations
* SQLite integration

---

### Milestone 5

User Experience

Deliverables:

* Better UI
* Loading states
* Error handling
* Dark mode
* Settings

---

### Milestone 6

Advanced RAG

Possible additions:

* Hybrid Search
* Query Rewriting
* Reranking
* Metadata Filtering
* Multiple Embedding Providers
* Multiple LLM Providers
* Parent Document Retrieval

---

## 8. Design Principles

The project should always prioritize:

* Simplicity over cleverness
* Modularity over shortcuts
* Readability over compactness
* Understanding over abstraction
* Incremental improvements
* Maintainability

---

## 9. Success Criteria

The MVP is considered complete when a user can:

1. Upload one or more PDF documents.
2. Ask questions about uploaded documents.
3. Receive accurate answers grounded only in retrieved context.
4. View source citations.
5. Continue chatting within the same session.
6. Run the application locally with minimal setup.

---

## 10. Future Vision

This project should evolve into a reusable RAG platform rather than remaining a single-purpose chatbot.

Future enhancements should fit naturally into the existing architecture without requiring major redesign.
