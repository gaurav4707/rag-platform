from langchain_chroma import Chroma
from langchain_chroma.vectorstores import _results_to_docs, maximal_marginal_relevance
import numpy as np

from backend.config import CHROMA_COLLECTION_NAME, CHROMA_DB_DIR
from backend.rag.embeddings import embeddings

__all__ = [
    "similarity_search",
    "add_documents",
    "delete_document",
    "similarity_search_with_scores",
    "list_documents",
    "similarity_search_with_scores_filtered",
    "mmr_search_with_scores",
    "maximal_marginal_relevance",
]

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


def similarity_search_with_scores_filtered(
    query: str,
    top_k: int,
    metadata_filter: dict | None,
    collection: Chroma | None = None,
) -> list[tuple]:
    """Search for similar documents with optional metadata filter."""
    store = _get_collection() if collection is None else collection
    return store.similarity_search_with_score(
        query,
        k=top_k,
        filter=metadata_filter,
    )


def mmr_search_with_scores(
    query: str,
    top_k: int,
    fetch_k: int,
    lambda_mult: float,
    metadata_filter: dict | None,
    collection: Chroma | None = None,
    maximal_marginal_relevance=maximal_marginal_relevance,
) -> list[tuple]:
    """Perform MMR search and return (Document, distance) tuples."""
    store = _get_collection() if collection is None else collection
    embedding_vector = embeddings.embed_query(query)
    result = store._collection.query(
        query_embeddings=[embedding_vector],
        n_results=fetch_k,
        include=["metadatas", "documents", "distances", "embeddings"],
        where=metadata_filter,
    )

    result_embeddings = result.get("embeddings")
    distances = result.get("distances")

    if result_embeddings is None or distances is None:
        raise RuntimeError(
            "Chroma query did not return embeddings/distances despite requesting them."
        )

    mmr_selected = maximal_marginal_relevance(
        np.array(embedding_vector, dtype=np.float32),
        result_embeddings[0],
        k=top_k,
        lambda_mult=lambda_mult,
    )

    candidates = _results_to_docs(result)
    query_distances = distances[0]

    return [
        (candidates[i], float(query_distances[i]))
        for i in mmr_selected
    ]