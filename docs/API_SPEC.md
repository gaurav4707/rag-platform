# API_SPEC.md

# API Specification

## Purpose

This document defines the public HTTP API exposed by the backend.

The API acts as the contract between the frontend and the backend.

The frontend should remain completely unaware of the internal implementation, whether the backend uses:

- Traditional RAG
- Agentic RAG
- Different LLM providers
- Different vector databases

Only the API contract defined in this document is considered stable.

Internal implementation details may change without affecting the frontend.

---

# 2. API Principles

The API should be:

* RESTful
* Consistent
* Versionable
* Stateless
* Easy to extend

Business logic must remain in the Service layer.

---

# 3. Base URL

Development

```text
http://localhost:8000
```

Future

```text
https://your-domain.com/api
```

---

# 4. Authentication

Current Version

No authentication.

The application is intended for local, single-user use.

Future versions may introduce authentication without changing existing endpoint behavior.

---

# 5. Endpoints

## Health Check

### GET `/health`

Purpose

Verify that the backend is running.

### Response

```json
{
  "status": "healthy"
}
```

---

## Upload Document

### POST `/documents/upload`

Purpose

Upload and index a PDF.

### Request

Content-Type

```text
multipart/form-data
```

Fields

| Field | Type | Required |
| ----- | ---- | -------- |
| file  | PDF  | Yes      |

### Success Response (201)

New document:

```json
{
  "document_id": "uuid-string",
  "filename": "research.pdf",
  "status": "indexed",
  "already_indexed": false
}
```

Duplicate document (200):

```json
{
  "document_id": "uuid-string",
  "filename": "research.pdf",
  "status": "already_indexed",
  "already_indexed": true
}
```

### Errors

```json
{
  "error": {
    "code": "INVALID_FILE",
    "message": "Only PDF files are accepted."
  }
}
```

```json
{
  "error": {
    "code": "INDEXING_FAILED",
    "message": "PDF contains no extractable text"
  }
}
```

---

## List Documents

### GET `/documents`

Purpose

Return all indexed documents.

### Success Response (200)

```json
[
    {
        "document_id": "uuid-string",
        "filename": "research.pdf",
        "status": "indexed"
    },
    {
        "document_id": "uuid-string",
        "filename": "notes.pdf",
        "status": "indexed"
    }
]
```

### Notes

* Source of truth is the ChromaDB metadata. The uploads directory is not scanned.
* Deduplicated by `document_id`.

---

## Delete Document

### DELETE `/documents/{document_id}`

Purpose

Remove a document and its associated vectors.

### Success Response (200)

```json
{
    "status": "deleted"
}
```

### Errors

```json
{
    "error": {
        "code": "DOCUMENT_NOT_FOUND",
        "message": "Document not found."
    }
}
```

### Behavior

1. Removes all vector entries for the `document_id` from ChromaDB.
2. Removes the stored PDF from `storage/uploads/`.
3. Returns 404 if the document does not exist.
Document management endpoints are intentionally separate from the Agent.

Although future versions of the Agent may invoke document management tools internally, the frontend should continue using these dedicated REST endpoints for CRUD operations.

---

## Chat

### POST `/chat`

Purpose

Ask a question about uploaded documents.

### Request

```json
{
    "message": "What is ReAct?"
}
```

### Response (200)
### tool_calls

Optional metadata describing the tools invoked by the Agent while answering the request.

This field is primarily intended for debugging, development, and future observability.

The frontend should not depend on its contents for normal application behavior.

Example

```json
[
  {
    "tool_name": "retrieve_context",
    "input": {
      "query": "What is RAG?"
    },
    "output": "Retrieved 4 relevant chunks"
  }
]
```

### Fields

| Field       | Type   | Description                                    |
|-------------|--------|------------------------------------------------|
| answer      | string | LLM-generated response                         |
| sources     | array  | Retrieved documents with metadata               |
| sources[].document   | string | Original filename                     |
| sources[].page       | int    | Page number (from PyPDFLoader)        |
| sources[].document_id| string | UUID of the source document           |
| sources[].score      | float  | Distance score from ChromaDB (lower = closer) |

### Validation

* Message cannot be empty.
* Leading/trailing whitespace is preserved (no trimming).

---

## Streaming Chat

### POST `/chat/stream`

Purpose

Receive the LLM response as a stream.

This endpoint is implemented and returns tokens via Server-Sent Events.

### Stream Events

The backend streams Server-Sent Events in the following format:

### Token Event (zero or more)

```text
data: {"token": "Re"}

data: {"token": "Act"}

data: {"token": " is"}
```

### Done Event (exactly one, sent last)

```text
data: {"done": true, "sources": [...], "tool_calls": [...]}
```

The `sources` array follows the same format as the non-streaming `POST /chat` response.

The `tool_calls` array contains metadata about each tool invocation:

```json
[
  {
    "tool_name": "retrieve_context",
    "input": {"query": "What is RAG?"},
    "output": "Retrieved 4 relevant chunks"
  }
]
```

The frontend should progressively render tokens to the UI, then finalize citations when the `done` event arrives.

### Error Handling

If the stream encounters an error, the connection is closed without a `done` event. The frontend should detect this via stream completion without a `done` event and show a fallback message.

---

# 6. Standard Response Format

Successful responses return the resource directly:

```json
// Single object
{ "document_id": "...", "filename": "...", "status": "indexed" }

// List
[{ "document_id": "..." }, { "document_id": "..." }]

// Status
{ "status": "deleted" }
```

---

# 7. Standard Error Format

All errors follow a consistent structure:

```json
{
    "error": {
        "code": "DOCUMENT_NOT_FOUND",
        "message": "Document not found."
    }
}
```

### Error Codes

| Code                 | Description                         | HTTP Status |
| -------------------- | ----------------------------------- | ----------- |
| INVALID_FILE         | File type or content not accepted   | 400         |
| DOCUMENT_NOT_FOUND   | Document does not exist             | 404         |
| INDEXING_FAILED      | PDF extraction or indexing failed   | 422         |
| VECTOR_STORE_ERROR   | ChromaDB operation failed           | 500         |
| INTERNAL_SERVER_ERROR| Unexpected error                    | 500         |

---

# 8. HTTP Status Codes

| Code | Meaning               |
| ---- | --------------------- |
| 200  | Success               |
| 201  | Created               |
| 400  | Invalid request       |
| 404  | Resource not found    |
| 422  | Validation error      |
| 500  | Internal server error |

---

# 9. Validation Rules

Upload

* Only PDF files
* Reject empty files
* Reject corrupted PDFs

Chat

* Message cannot be empty
* Leading/trailing whitespace preserved

Delete

* Document must exist (returns 404 if not)

---

# 10. Streaming Requirements

Streaming should begin as soon as the first token is available.

The backend should not wait for the complete answer before sending data.

Streaming should terminate cleanly when generation finishes or an unrecoverable error occurs.

---

# 11. Versioning

Current version

```text
v1
```

Future versions may introduce

```text
/api/v2/
```

without breaking existing clients.

---

# 12. Future Endpoints

Potential additions

## Conversation History

```text
GET /conversations

POST /conversations

DELETE /conversations/{id}
```

---

## Conversation Messages

```text
GET /conversations/{id}/messages
```

---

## Search

```text
POST /search
```

Returns retrieved chunks without invoking the LLM.

Useful for debugging.

---

*Note: Settings are intentionally frontend-only and managed via localStorage. No settings API is planned.*

## Debug

```text
POST /debug/retrieve

POST /debug/prompt
```

Expose retrieval results and constructed prompts for development purposes.

These endpoints should be disabled or protected in production.

---

# 13. API Design Rules

The API should:

* Hide internal implementation details.
* Return consistent response formats.
* Validate inputs before invoking business logic.
* Stream responses when appropriate.
* Remain backward compatible whenever possible.

The frontend should never need to know whether the backend uses Chroma, FAISS, Gemini, OpenAI, or any other provider.

# Agent Compatibility

The backend currently exposes a stable HTTP API while using an internal Agentic RAG architecture.

Future versions of the backend may introduce additional tools, planning strategies, or reasoning capabilities.

These internal changes should not require changes to the frontend as long as the API contract remains unchanged.

This separation allows the backend to evolve independently from the user interface.