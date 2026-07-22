import hashlib
import uuid

from backend.config import PARENT_STORAGE_DIR, UPLOAD_DIR
from backend.rag.loader import load_pdf
from backend.rag.splitter import HierarchicalSplitter
from backend.storage.parent_store import FileParentStore, ParentBlock
from backend.rag.vector_store import (
    add_documents,
    delete_document as delete_vector_document,
    find_document_by_hash,
    list_documents as list_vector_documents,
    get_all_documents,
)
from backend.rag.bm25 import rebuild as rebuild_bm25_index, refresh as refresh_bm25_index, invalidate as invalidate_bm25_index
from backend.api.errors import AppError, ERROR_CODES, status

_parent_store = FileParentStore(PARENT_STORAGE_DIR)


def _compute_file_hash(file_content: bytes) -> str:
    """Compute SHA-256 hash of file content."""
    return hashlib.sha256(file_content).hexdigest()


def process_upload(file_content: bytes, original_filename: str) -> dict:
    """Save a PDF file, load, split, embed, and index it.

    Returns upload metadata on success.
    Cleans up the saved file and any partial vector entries on failure.
    """
    file_hash = _compute_file_hash(file_content)

    # Check if document with same hash already exists
    existing_doc = find_document_by_hash(file_hash)
    if existing_doc:
        print(f"Uploading: {original_filename}")
        print(f"SHA256: {file_hash}")
        print("Duplicate: Yes")
        print("Skipping indexing.")

        return {
            "document_id": existing_doc["document_id"],
            "filename": existing_doc["filename"],
            "status": "already_indexed",
            "already_indexed": True,
        }

    document_id = str(uuid.uuid4())
    saved_path = UPLOAD_DIR / f"{document_id}.pdf"

    try:
        saved_path.write_bytes(file_content)

        try:
            docs = load_pdf(str(saved_path))
        except Exception as e:
            # PyPDFLoader raises various exceptions for corrupted/unreadable PDFs
            raise AppError(
                ERROR_CODES["CORRUPTED_PDF"],
                "The file appears to be corrupted or unreadable.",
                http_status=status.HTTP_422_UNPROCESSABLE_ENTITY,
            ) from e

        if not docs:
            raise AppError(
                ERROR_CODES["EMPTY_PDF"],
                "The uploaded PDF contains no readable text.",
                http_status=status.HTTP_422_UNPROCESSABLE_ENTITY,
            )

        for doc in docs:
            doc.metadata["document_id"] = document_id
            doc.metadata["filename"] = original_filename
            doc.metadata["file_hash"] = file_hash

        splitter = HierarchicalSplitter(
            document_id=document_id,
            filename=original_filename,
            file_hash=file_hash,
        )
        split_result = splitter.split(docs)

        parent_blocks = [
            ParentBlock(
                parent_id=p.metadata["parent_id"],
                content=p.page_content,
                start_page=p.metadata.get("page"),
                end_page=p.metadata.get("page"),
                metadata=dict(p.metadata),
            )
            for p in split_result.parent_blocks
        ]
        _parent_store.store_parents(document_id, parent_blocks)

        add_documents(split_result.child_chunks)

        # Rebuild BM25 index with all documents
        try:
            all_docs = get_all_documents()
            rebuild_bm25_index(all_docs)
        except Exception as e:
            # Log but don't fail the upload if BM25 rebuild fails
            print(f"Warning: BM25 index rebuild failed: {e}")

    except AppError:
        if saved_path.exists():
            saved_path.unlink()
        try:
            delete_vector_document(document_id)
        except Exception:
            pass
        _parent_store.delete_parents(document_id)
        raise
    except Exception:
        if saved_path.exists():
            saved_path.unlink()
        try:
            delete_vector_document(document_id)
        except Exception:
            pass
        _parent_store.delete_parents(document_id)
        raise AppError(
            ERROR_CODES["INDEXING_FAILED"],
            "Document indexing failed.",
            http_status=status.HTTP_422_UNPROCESSABLE_ENTITY,
        )

    print(f"Uploading: {original_filename}")
    print(f"SHA256: {file_hash}")
    print("Duplicate: No")

    return {
        "document_id": document_id,
        "filename": original_filename,
        "status": "indexed",
        "already_indexed": False,
    }


def list_indexed_documents() -> list[dict]:
    """Return all indexed documents from the vector store."""
    docs = list_vector_documents()
    for doc in docs:
        doc["status"] = "indexed"
    return docs


def delete_document(document_id: str) -> None:
    """Delete a document: remove vectors, then remove stored PDF.

    Raises AppError DOCUMENT_NOT_FOUND if the document is not indexed.
    """
    docs = list_vector_documents()
    matching = [d for d in docs if d["document_id"] == document_id]
    if not matching:
        raise AppError(
            ERROR_CODES["DOCUMENT_NOT_FOUND"],
            "Document not found.",
            http_status=status.HTTP_404_NOT_FOUND,
        )

    try:
        delete_vector_document(document_id)
    except Exception:
        raise AppError(
            ERROR_CODES["VECTOR_STORE_ERROR"],
            "Failed to delete document vectors.",
        )

    # Rebuild BM25 index after deletion
    try:
        all_docs = get_all_documents()
        rebuild_bm25_index(all_docs)
    except Exception as e:
        print(f"Warning: BM25 index rebuild failed after deletion: {e}")

    _parent_store.delete_parents(document_id)

    saved_path = UPLOAD_DIR / f"{document_id}.pdf"
    if saved_path.exists():
        saved_path.unlink()


def search_documents_by_filename(filename: str) -> list[dict]:
    """Search indexed documents by filename (case-insensitive, partial match).

    Args:
        filename: Filename or partial filename to search for.

    Returns:
        List of matching document metadata dicts with keys:
        document_id, filename, file_hash, status.
    """
    docs = list_vector_documents()
    filename_lower = filename.lower()
    matches = [
        {**doc, "status": "indexed"}
        for doc in docs
        if filename_lower in doc["filename"].lower()
    ]
    return matches
