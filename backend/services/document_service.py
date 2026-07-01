import uuid

from config import UPLOAD_DIR
from rag.loader import load_pdf
from rag.splitter import text_splitter
from rag.vector_store import add_documents, delete_document


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

    except Exception:
        if saved_path.exists():
            saved_path.unlink()
        try:
            delete_document(document_id)
        except Exception:
            pass
        raise

    return {
        "document_id": document_id,
        "filename": original_filename,
        "status": "indexed",
    }
