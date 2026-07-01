import uuid

from config import UPLOAD_DIR
from rag.loader import load_pdf
from rag.splitter import text_splitter
from rag.vector_store import add_documents, delete_document as delete_vector_document
from rag.vector_store import list_documents as list_vector_documents
from api.errors import AppError, ERROR_CODES, status


def process_upload(file_content: bytes, original_filename: str) -> dict:
    """Save a PDF file, load, split, embed, and index it.

    Returns upload metadata on success.
    Cleans up the saved file and any partial vector entries on failure.
    """
    document_id = str(uuid.uuid4())
    saved_path = UPLOAD_DIR / f"{document_id}.pdf"

    try:
        saved_path.write_bytes(file_content)

        docs = load_pdf(str(saved_path))

        if not docs:
            raise ValueError("PDF contains no extractable text")

        for doc in docs:
            doc.metadata["document_id"] = document_id
            doc.metadata["filename"] = original_filename

        splits = text_splitter.split_documents(docs)

        for i, split in enumerate(splits):
            split.metadata["chunk_index"] = i

        add_documents(splits)

    except AppError:
        raise
    except ValueError:
        if saved_path.exists():
            saved_path.unlink()
        try:
            delete_vector_document(document_id)
        except Exception:
            pass
        raise
    except Exception:
        if saved_path.exists():
            saved_path.unlink()
        try:
            delete_vector_document(document_id)
        except Exception:
            pass
        raise AppError(
            ERROR_CODES["INDEXING_FAILED"],
            "Document indexing failed.",
            http_status=status.HTTP_422_UNPROCESSABLE_ENTITY,
        )

    return {
        "document_id": document_id,
        "filename": original_filename,
        "status": "indexed",
    }


def list_indexed_documents() -> list[dict]:
    """Return all indexed documents from the vector store."""
    return list_vector_documents()


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

    saved_path = UPLOAD_DIR / f"{document_id}.pdf"
    if saved_path.exists():
        saved_path.unlink()
