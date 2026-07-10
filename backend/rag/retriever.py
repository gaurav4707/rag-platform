from langchain.tools import tool

from backend.rag.retrieval_config import DEFAULT_RETRIEVAL_CONFIG, RetrievalConfig
from backend.rag.vector_store import (
    embeddings,
    maximal_marginal_relevance,
    mmr_search_with_scores,
    similarity_search_with_scores_filtered,
)
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


@tool(response_format="content_and_artifact")
def retrieve_context(
    query: str,
    config: RetrievalConfig = DEFAULT_RETRIEVAL_CONFIG,
):
    """Retrieve information to help answer a query.

    Returns a RetrievalResult containing the query and retrieved chunks with scores.
    """
    results = _run_retrieval(query, config)

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