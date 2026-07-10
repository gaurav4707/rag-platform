from langchain.tools import tool

from backend.rag.retrieval_config import DEFAULT_RETRIEVAL_CONFIG, RetrievalConfig
from backend.rag.vector_store import (
    maximal_marginal_relevance,
    mmr_search_with_scores,
    similarity_search_with_scores_filtered,
)
from backend.rag.query_rewriter import rewrite_query
from backend.models.rag_models import RetrievalResult, RetrievedChunk


def _run_similarity_search(
    query: str,
    config: RetrievalConfig,
) -> list[tuple]:
    return similarity_search_with_scores_filtered(
        query=query,
        top_k=config.top_k,
        metadata_filter=config.metadata_filter,
    )


def _run_mmr_search(
    query: str,
    config: RetrievalConfig,
) -> list[tuple]:
    return mmr_search_with_scores(
        query=query,
        top_k=config.top_k,
        fetch_k=config.fetch_k,
        lambda_mult=config.lambda_mult,
        metadata_filter=config.metadata_filter,
        maximal_marginal_relevance=maximal_marginal_relevance,
    )


def _run_retrieval(
    query: str,
    config: RetrievalConfig,
) -> list[tuple]:
    if config.search_type == "similarity":
        return _run_similarity_search(query, config)

    if config.search_type == "mmr":
        return _run_mmr_search(query, config)

    raise ValueError(f"Unsupported search_type: {config.search_type}")


def _deduplicate_chunks(chunks: list[tuple]) -> list[tuple]:
    """Remove duplicate chunks based on stable identifier (document_id, chunk_index).

    Preserves the first occurrence (highest score) of each unique chunk.
    Only deduplicates when both identifiers are present and valid.
    """
    seen: set[tuple] = set()
    unique_chunks: list[tuple] = []

    for doc, score in chunks:
        doc_id = doc.metadata.get("document_id")
        chunk_index = doc.metadata.get("chunk_index")

        # Only deduplicate if both identifiers are present
        if doc_id is not None and chunk_index is not None:
            key = (doc_id, chunk_index)
            if key not in seen:
                seen.add(key)
                unique_chunks.append((doc, score))
        else:
            # Fallback: use content hash for chunks without metadata
            content_key = doc.page_content[:200]  # First 200 chars as fallback
            if content_key not in seen:
                seen.add(content_key)
                unique_chunks.append((doc, score))

    return unique_chunks


def _log_retrieval_details(
    original_query: str,
    retrieval_query: str,
    chunks: list[RetrievedChunk],
) -> None:
    """Log detailed retrieval information for debugging."""
    print("\n=== Retrieval ===")
    print(f"Original Query : {original_query}")
    print(f"Retrieval Query: {retrieval_query}")
    print(f"Chunks Retrieved: {len(chunks)}")

    for i, chunk in enumerate(chunks):
        meta = chunk.document.metadata
        doc_id = meta.get("document_id", "unknown")
        filename = meta.get("filename", "unknown")
        page = meta.get("page", "unknown")
        chunk_idx = meta.get("chunk_index", "unknown")
        score = chunk.score

        preview = chunk.document.page_content[:300].replace("\n", " ")

        print(f"\n  Chunk {i + 1}:")
        print(f"    Document ID : {doc_id}")
        print(f"    Filename    : {filename}")
        print(f"    Page        : {page}")
        print(f"    Chunk Index : {chunk_idx}")
        print(f"    Score       : {score:.4f}")
        print(f"    Preview     : {preview}")


@tool(response_format="content_and_artifact")
def retrieve_context(
    query: str,
    config: RetrievalConfig = DEFAULT_RETRIEVAL_CONFIG,
):
    """Retrieve information to help answer a query.

    Returns a RetrievalResult containing the query and retrieved chunks with scores.
    """
    try:
        retrieval_query = rewrite_query(query, config.query_rewrite)
    except Exception:
        # Fall back to original query if rewriting fails
        retrieval_query = query

    results = _run_retrieval(retrieval_query, config)

    # Deduplicate chunks by stable identifier (document_id, chunk_index)
    results = _deduplicate_chunks(results)

    chunks = [
        RetrievedChunk(document=doc, score=score)
        for doc, score in results
    ]

    retrieval_result = RetrievalResult(
        original_query=query,
        retrieval_query=retrieval_query,
        chunks=chunks,
    )

    serialized = "\n\n".join(
        f"Source: {chunk.document.metadata}\nContent: {chunk.document.page_content}"
        for chunk in chunks
    )

    _log_retrieval_details(query, retrieval_query, chunks)

    return serialized, retrieval_result