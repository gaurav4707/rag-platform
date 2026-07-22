"""Query Expansion Module for Retrieval Pipeline.

This module provides query expansion capabilities as part of the retrieval pipeline.
It follows a provider-agnostic design using the BaseQueryExpander protocol,
allowing different implementations (LLM-based, rule-based, cached, etc.) to be
swapped without changing the pipeline.

The module is designed to support future query transformation techniques including:
- Query Expansion (current)
- Query Decomposition
- HyDE (Hypothetical Document Embeddings)
- Step-Back Prompting
- Self-Query Generation
- Metadata Query Generation
"""

from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Protocol

logger = logging.getLogger(__name__)


@dataclass
class QueryExpansionResult:
    """Result of a query expansion operation.

    Attributes:
        original_query: The original user query.
        expanded_queries: List of expanded query variations.
        metadata: Additional information about the expansion (e.g., count, strategy).
    """
    original_query: str
    expanded_queries: list[str]
    metadata: dict


class BaseQueryExpander(Protocol):
    """Protocol for query expanders.

    Implementations should focus only on generating query variations for
    improved retrieval recall. They must not perform retrieval themselves.
    """

    def expand(self, query: str) -> QueryExpansionResult:
        """Expand a query into multiple retrieval queries.

        Args:
            query: The original (or rewritten) query to expand.

        Returns:
            QueryExpansionResult with expanded queries and metadata.
        """
        ...


class QueryExpander(ABC):
    """Abstract base class for query expanders."""

    @abstractmethod
    def expand(self, query: str) -> QueryExpansionResult:
        """Expand a query into multiple retrieval queries.

        Args:
            query: The original (or rewritten) query to expand.

        Returns:
            QueryExpansionResult with expanded queries and metadata.
        """
        pass


class NoOpQueryExpander(QueryExpander):
    """Query expander that returns the original query unchanged.

    Used when query expansion is disabled.
    """

    def expand(self, query: str) -> QueryExpansionResult:
        return QueryExpansionResult(
            original_query=query,
            expanded_queries=[query],
            metadata={"strategy": "none", "expansion_count": 1},
        )


class LLMQueryExpander(QueryExpander):
    """LLM-based query expander.

    Uses the project's configured LLM to generate multiple semantically diverse
    search queries from a single user question. This improves recall by capturing
    different aspects and phrasings of the same information need.
    """

    def __init__(self, num_queries: int = 3):
        """Initialize the LLM query expander.

        Args:
            num_queries: Number of query variations to generate (including original).
        """
        self._llm = None
        self.num_queries = num_queries

    def _get_llm(self):
        """Lazy-load the LLM to avoid circular imports."""
        if self._llm is None:
            try:
                from backend.providers import get_llm
                self._llm = get_llm()
            except ImportError:
                logger.warning("LLM not available, falling back to no-op expander")
                self._llm = None
        return self._llm

    def _build_prompt(self, query: str) -> str:
        """Build the prompt for query expansion."""
        return f"""Generate {self.num_queries} semantically diverse search queries that could help retrieve relevant information for the given question.

The queries should:
- Use different vocabulary and phrasing
- Cover different aspects of the question
- Be suitable for semantic vector search
- NOT answer the question

Return only the queries, one per line, without numbering or explanations.

Original question: {query}

Search queries:"""

    def _parse_response(self, response: str) -> list[str]:
        """Parse the LLM response into a list of queries."""
        lines = [line.strip() for line in response.strip().split("\n") if line.strip()]
        queries = []
        for line in lines:
            cleaned = line.strip("- •*1234567890. ")
            if cleaned and cleaned not in queries:
                queries.append(cleaned)
        return queries

    def expand(self, query: str) -> QueryExpansionResult:
        """Expand the query using the LLM.

        Args:
            query: The original (or rewritten) query to expand.

        Returns:
            QueryExpansionResult with expanded queries and metadata.
        """
        if not query or not query.strip():
            logger.debug("Empty query, returning as-is")
            return QueryExpansionResult(
                original_query=query,
                expanded_queries=[query],
                metadata={"strategy": "llm", "expansion_count": 1, "fallback": True},
            )

        llm = self._get_llm()
        if llm is None:
            logger.warning("LLM not available for query expansion, using original query")
            return QueryExpansionResult(
                original_query=query,
                expanded_queries=[query],
                metadata={"strategy": "llm", "expansion_count": 1, "fallback": True},
            )

        prompt = self._build_prompt(query)

        try:
            response = llm.invoke(prompt)
            content = response.content

            if isinstance(content, str):
                generated = content
            elif isinstance(content, list):
                generated = " ".join(
                    str(item.get("text", item)) if isinstance(item, dict) else str(item)
                    for item in content
                )
            else:
                generated = str(content)

            expanded = self._parse_response(generated)

            if not expanded:
                logger.debug("LLM returned no valid queries, using original")
                expanded = [query]

            if query not in expanded:
                expanded.insert(0, query)

            expanded = expanded[: self.num_queries]

            logger.debug(
                "Query expanded:\n  Original: %s\n  Expanded: %s",
                query,
                expanded,
            )

            return QueryExpansionResult(
                original_query=query,
                expanded_queries=expanded,
                metadata={"strategy": "llm", "expansion_count": len(expanded)},
            )

        except Exception as e:
            logger.warning("Query expansion failed: %s, using original query", e)
            return QueryExpansionResult(
                original_query=query,
                expanded_queries=[query],
                metadata={"strategy": "llm", "expansion_count": 1, "fallback": True, "error": str(e)},
            )


def get_query_expander(strategy: str = "none", **kwargs) -> QueryExpander:
    """Factory function to get the appropriate query expander.

    Args:
        strategy: The expansion strategy - "none" or "llm".
        **kwargs: Additional arguments for the expander (e.g., num_queries).

    Returns:
        QueryExpander instance.

    Raises:
        ValueError: If an unknown strategy is provided.
    """
    if strategy == "none":
        return NoOpQueryExpander()
    if strategy == "llm":
        num_queries = kwargs.get("num_queries", 3)
        return LLMQueryExpander(num_queries=num_queries)
    raise ValueError(f"Unknown query expansion strategy: {strategy}")