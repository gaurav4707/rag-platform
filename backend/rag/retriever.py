from langchain.tools import tool
from langchain_chroma import Chroma

from backend.config import CHROMA_COLLECTION_NAME, CHROMA_DB_DIR
from backend.rag.embeddings import embeddings
from backend.models.rag_models import RetrievalResult, RetrievedChunk


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


@tool(response_format="content_and_artifact")
def retrieve_context(query: str):
    """Retrieve information to help answer a query.

    Returns a RetrievalResult containing the query and retrieved chunks with scores.
    """
    k = 4
    collection = _get_collection()
    results = collection.similarity_search_with_score(query, k=k)

    chunks = [
        RetrievedChunk(document=doc, score=score)
        for doc, score in results
    ]

    retrieval_result = RetrievalResult(query=query, chunks=chunks)

    serialized = "\n\n".join(
        f"Source: {chunk.document.metadata}\nContent: {chunk.document.page_content}"
        for chunk in chunks
    )

    return serialized, retrieval_result