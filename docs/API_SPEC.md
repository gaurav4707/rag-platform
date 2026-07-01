# API_SPEC.md

# Backend API Specification

## 1. Purpose

This document defines the public API contract between the frontend and the backend.

It specifies:

* Available endpoints
* Request formats
* Response formats
* Streaming behavior
* Error responses

The frontend should interact only with these APIs and should not depend on backend implementation details.

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

```json
{
  "document_id": "uuid-string",
  "filename": "research.pdf",
  "status": "indexed"
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

```json
{
    "answer": "ReAct is a framework that combines reasoning and acting...",
    "sources": [
        {
            "document": "research.pdf",
            "page": 7,
            "document_id": "uuid-string",
            "score": 0.4521
        }
    ]
}
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

This endpoint is planned but not yet implemented.

### Stream Events

The backend streams tokens as they are generated.

Example

```text
data: "Re"

data: "Act"

data: " is"

data: "..."
```

The frontend should progressively render tokens.

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

## Settings

```text
GET /settings

PUT /settings
```

Manage application configuration.

---

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
