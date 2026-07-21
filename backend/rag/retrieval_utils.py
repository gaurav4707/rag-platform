"""Utilities for retrieval result processing.

Contains helpers for merging, deduplicating, and combining retrieval results.
"""

from backend.models.rag_models import RetrievalResult, RetrievedChunk


def merge_retrieval_results(results: list[RetrievalResult]) -> RetrievalResult | None:
    """Merge multiple RetrievalResults into one, deduplicating by (document_id, chunk_index).

    Returns None if no results provided.
    """
    if not results:
        return None

    if len(results) == 1:
        return results[0]

    seen_chunks: set[tuple[str, int]] = set()
    merged_chunks = []
    merged_metadata: dict = {}

    for result in results:
        # Preserve first retrieval's metadata as base
        if not merged_metadata:
            merged_metadata = result.retrieval_metadata.copy()

        for chunk in result.chunks:
            doc_id = chunk.document.metadata.get("document_id", "unknown")
            chunk_idx = chunk.document.metadata.get("chunk_index", -1)
            key = (doc_id, chunk_idx)

            if key not in seen_chunks:
                seen_chunks.add(key)
                merged_chunks.append(chunk)

    # Use the first result's queries as base
    base = results[0]
    return RetrievalResult(
        original_query=base.original_query,
        retrieval_query=base.retrieval_query,
        chunks=merged_chunks,
        retrieval_metadata=merged_metadata,
    )


def deduplicate_chunks(chunks: list[RetrievedChunk]) -> list[RetrievedChunk]:
    """Remove duplicate chunks based on (document_id, chunk_index) pair.

    Preserves first occurrence (highest ranked).
    """
    seen: set[tuple[str, int]] = set()
    unique: list[RetrievedChunk] = []

    for chunk in chunks:
        doc_id = chunk.document.metadata.get("document_id", "unknown")
        chunk_idx = chunk.document.metadata.get("chunk_index", -1)
        key = (doc_id, chunk_idx)

        if key not in seen:
            seen.add(key)
            unique.append(chunk)

    return unique