"""Query rewriting module for the retrieval pipeline.

This module provides functionality to rewrite user queries into more effective
search queries for vector retrieval. It supports multiple strategies and is
designed to be extensible for future strategies.
"""

from backend.rag.llm import get_llm

def rewrite_query(query: str, strategy: str = "none") -> str:
    """Rewrite the user's query based on the specified strategy.

    Args:
        query: The original user query.
        strategy: The rewriting strategy - "none" or "llm".

    Returns:
        The rewritten query (or original if strategy is "none").

    Raises:
        ValueError: If an unknown strategy is provided.
    """
    if strategy == "none" or not query.strip():
        return query

    if strategy == "llm":
        return _rewrite_with_llm(query)

    raise ValueError(f"Unknown query_rewrite strategy: {strategy}")


def _rewrite_with_llm(query: str) -> str:
    """Use an LLM to rewrite the query for better retrieval.

    Args:
        query: The original user query.

    Returns:
        The rewritten query, or the original query if rewriting fails.
    """
    try:
        from langchain_groq import ChatGroq
    except ImportError:
        # If LLM dependencies are not available, fall back to original query
        return query

    llm = get_llm()

    prompt = f"""Rewrite the following user query to be more effective for vector search retrieval.
    The rewritten query should:
    - Be more specific and descriptive
    - Include relevant keywords and synonyms
    - Remove conversational filler
    - Preserve the original intent

    Original query: {query}

    Rewritten query:"""

    try:
        response = llm.invoke(prompt)
        content = response.content

        if isinstance(content, str):
            rewritten = content.strip()
        elif isinstance(content, list):
            rewritten = " ".join(
                str(item.get("text", item)) if isinstance(item, dict) else str(item)
                for item in content
            ).strip()
        else:
            rewritten = str(content).strip()

        if not rewritten:
            return query

        return rewritten
    except Exception:
        # On any error, fall back to original query
        return query