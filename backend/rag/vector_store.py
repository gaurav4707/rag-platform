from langchain_chroma import Chroma

from backend.config import CHROMA_COLLECTION_NAME, CHROMA_DB_DIR, EMBEDDING_MODEL
from backend.rag.embeddings import embeddings

_collection: Chroma | None = None


def _get_collection() -> Chroma:
    """Return the cached Chroma vector store collection."""
    global _collection
    if _collection is None:
        _collection = Chroma(
            collection_name=CHROMA_COLLECTION_NAME,
            embedding_function=embeddings,
            persist_directory=str(CHROMA_DB_DIR),
        )
    return _collection


def similarity_search(query: str, k: int = 4) -> list:
    """Search for similar documents in the vector store."""
    return _get_collection().similarity_search(query, k=k)


def add_documents(docs: list) -> None:
    """Add documents to the vector store."""
    _get_collection().add_documents(docs)


def delete_document(document_id: str) -> None:
    """Delete all chunks associated with a given document_id."""
    _get_collection().delete(where={"document_id": document_id})


def similarity_search_with_scores(query: str, k: int = 4) -> list[tuple]:
    """Search for similar documents and return (Document, distance) tuples."""
    return _get_collection().similarity_search_with_score(query, k=k)


def list_documents() -> list[dict]:
    """List unique documents in the vector store."""
    collection = _get_collection()
    all_data = collection.get()
    seen = set()
    documents = []
    for metadata in all_data.get("metadatas", []):
        doc_id = metadata.get("document_id")
        if doc_id and doc_id not in seen:
            seen.add(doc_id)
            documents.append({
                "document_id": doc_id,
                "filename": metadata.get("filename", "unknown"),
            })
    return documents
