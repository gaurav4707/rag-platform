from backend.models.rag_models import RetrievalResult, SourceItem


def build_sources(retrieval_result: RetrievalResult) -> list[SourceItem]:
    """Convert RetrievalResult chunks into SourceItem citations.

    Does not query the vector store. Only converts metadata from
    already-retrieved chunks.
    """
    sources = []
    for chunk in retrieval_result.chunks:
        meta = chunk.document.metadata
        sources.append(
            SourceItem(
                document=meta.get("filename", "unknown"),
                page=meta.get("page"),
                document_id=meta.get("document_id", ""),
                score=round(chunk.score, 4) if chunk.score is not None else None,
            )
        )
    return sources