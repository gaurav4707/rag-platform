"""Query rewriting module for the retrieval pipeline.

This module provides functionality to rewrite user queries into more effective
search queries for vector retrieval. It supports multiple strategies and is
designed to be extensible for future strategies.

The module follows a provider-agnostic design using the BaseQueryRewriter protocol,
allowing different implementations (LLM-based, rule-based, cached, etc.) to be
swapped without changing the retriever.
"""

from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Protocol

logger = logging.getLogger(__name__)


@dataclass
class QueryRewriteResult:
    """Result of a query rewrite operation.

    Attributes:
        original_query: The original user query.
        retrieval_query: The rewritten query to use for retrieval.
        rewritten: Whether the query was actually rewritten.
    """
    original_query: str
    retrieval_query: str
    rewritten: bool


class BaseQueryRewriter(Protocol):
    """Protocol for query rewriters.

    Implementations should be provider-agnostic and focus only on
    transforming the query for better retrieval.
    """
    def rewrite(self, query: str) -> QueryRewriteResult:
        ...


class QueryRewriter(ABC):
    """Abstract base class for query rewriters."""

    @abstractmethod
    def rewrite(self, query: str) -> QueryRewriteResult:
        """Rewrite a query for better retrieval.

        Args:
            query: The original user query.

        Returns:
            QueryRewriteResult with original and rewritten queries.
        """
        pass


class NoOpQueryRewriter(QueryRewriter):
    """Query rewriter that returns the original query unchanged."""

    def rewrite(self, query: str) -> QueryRewriteResult:
        return QueryRewriteResult(
            original_query=query,
            retrieval_query=query,
            rewritten=False,
        )


class LLMQueryRewriter(QueryRewriter):
    """LLM-based query rewriter.

    Uses the project's configured LLM to rewrite queries into more
    effective search queries for vector retrieval.
    """

    def __init__(self):
        self._llm = None

    def _get_llm(self):
        """Lazy-load the LLM to avoid circular imports."""
        if self._llm is None:
            try:
                from backend.rag.llm import get_llm
                self._llm = get_llm()
            except ImportError:
                logger.warning("LLM not available, falling back to no-op rewriter")
                self._llm = None
        return self._llm

    def _should_rewrite(self, query: str) -> bool:
        """Determine if a query would benefit from rewriting.

        Avoids rewriting queries that are already specific and standalone.
        """
        if not query or not query.strip():
            return False

        query_lower = query.lower().strip()

        # Already specific queries that don't need rewriting
        specific_patterns = [
            "what is",
            "explain",
            "how does",
            "what are",
            "define",
            "describe",
            "compare",
            "difference between",
        ]

        # Conversational/follow-up patterns that DO need rewriting
        conversational_patterns = [
            "how does it work",
            "explain this",
            "what about",
            "tell me more",
            "and then",
            "what does it mean",
            "can you explain",
            "this section",
            "that part",
            "it says",
            "the paper",
            "the document",
            "above",
            "below",
            "previous",
            "next",
        ]

        # Check if it's already specific
        for pattern in specific_patterns:
            if query_lower.startswith(pattern):
                # But still check if it's vague
                words = query.split()
                if len(words) > 5:  # Specific enough
                    return False

        # Check if it's conversational/follow-up
        for pattern in conversational_patterns:
            if pattern in query_lower:
                return True

        # Very short queries likely need expansion
        if len(query.split()) <= 3:
            return True

        return False

    def rewrite(self, query: str) -> QueryRewriteResult:
        """Rewrite the query using the LLM.

        Args:
            query: The original user query.

        Returns:
            QueryRewriteResult with original and rewritten queries.
        """
        if not query or not query.strip():
            return QueryRewriteResult(
                original_query=query,
                retrieval_query=query,
                rewritten=False,
            )

        # Check if rewriting would be beneficial
        if not self._should_rewrite(query):
            logger.debug("Query rewriting skipped - query is already specific: %s", query)
            return QueryRewriteResult(
                original_query=query,
                retrieval_query=query,
                rewritten=False,
            )

        llm = self._get_llm()
        if llm is None:
            logger.warning("LLM not available for query rewriting, using original query")
            return QueryRewriteResult(
                original_query=query,
                retrieval_query=query,
                rewritten=False,
            )

        prompt = f"""Rewrite the user's question into a concise standalone search query suitable for retrieving relevant document chunks.

Do not answer the question.
Do not add information.
Return only the rewritten query.

Original question: {query}

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

            # Clean up common LLM artifacts
            rewritten = rewritten.strip('"\'').strip()

            if not rewritten:
                logger.debug("LLM returned empty rewrite, using original query")
                return QueryRewriteResult(
                    original_query=query,
                    retrieval_query=query,
                    rewritten=False,
                )

            logger.debug(
                "Query rewritten:\n  Original: %s\n  Rewritten: %s",
                query,
                rewritten,
            )

            return QueryRewriteResult(
                original_query=query,
                retrieval_query=rewritten,
                rewritten=True,
            )

        except Exception as e:
            logger.warning("Query rewrite failed: %s, using original query", e)
            return QueryRewriteResult(
                original_query=query,
                retrieval_query=query,
                rewritten=False,
            )


def get_query_rewriter(strategy: str = "llm") -> QueryRewriter:
    """Factory function to get the appropriate query rewriter.

    Args:
        strategy: The rewriting strategy - "none" or "llm".

    Returns:
        QueryRewriter instance.
    """
    if strategy == "none":
        return NoOpQueryRewriter()
    if strategy == "llm":
        return LLMQueryRewriter()
    raise ValueError(f"Unknown query_rewrite strategy: {strategy}")


# Backward compatibility function
def rewrite_query(query: str, strategy: str = "none") -> str:
    """Rewrite the user's query based on the specified strategy.

    This function is maintained for backward compatibility.
    New code should use the QueryRewriter classes directly.

    Args:
        query: The original user query.
        strategy: The rewriting strategy - "none" or "llm".

    Returns:
        The rewritten query (or original if strategy is "none").

    Raises:
        ValueError: If an unknown strategy is provided.
    """
    rewriter = get_query_rewriter(strategy)
    result = rewriter.rewrite(query)
    return result.retrieval_query