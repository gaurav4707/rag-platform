"""Retrieval Executor for parallel and sequential retrieval execution.

This module handles the execution concerns of retrieval operations:
- Parallel retrieval using thread pool
- Sequential retrieval
- Future: batching, provider-specific optimizations, timeouts
"""

from __future__ import annotations

import logging
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Callable, TypeVar

from backend.models.rag_models import RetrievedChunk

logger = logging.getLogger(__name__)

T = TypeVar("T")


class RetrievalExecutor:
    """Handles execution of retrieval operations with configurable parallelism.

    Responsibilities:
    - Parallel retrieval across multiple queries
    - Sequential retrieval (fallback/simple cases)
    - Thread pool management
    - Future: batching, timeouts, provider-specific optimizations

    The executor is stateless and can be reused across pipeline invocations.
    """

    def __init__(self, max_workers: int = 3):
        """Initialize the retrieval executor.

        Args:
            max_workers: Maximum number of parallel retrieval workers.
                         Defaults to 3 for typical multi-query scenarios.
        """
        self.max_workers = max_workers

    def execute_parallel(
        self,
        queries: list[str],
        retrieve_fn: Callable[[str], list[RetrievedChunk]],
    ) -> list[list[RetrievedChunk]]:
        """Execute retrieval for multiple queries in parallel.

        Args:
            queries: List of queries to retrieve for.
            retrieve_fn: Function that takes a query string and returns
                         a list of RetrievedChunk objects.

        Returns:
            List of chunk lists, one per query, in the same order as input queries.
        """
        if not queries:
            return []

        if len(queries) == 1:
            return [retrieve_fn(queries[0])]

        results: list[list[RetrievedChunk] | None] = [None] * len(queries)

        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            future_to_index = {
                executor.submit(retrieve_fn, query): index
                for index, query in enumerate(queries)
            }

            for future in as_completed(future_to_index):
                index = future_to_index[future]
                try:
                    results[index] = future.result()
                    chunk_count = results[index]
                    assert chunk_count is not None
                    logger.debug(
                        "Parallel retrieval completed for query %d/%d: %d chunks",
                        index + 1,
                        len(queries),
                        len(chunk_count),
                    )
                except Exception as e:
                    logger.warning("Parallel retrieval failed for query %d: %s", index, e)
                    results[index] = []

        return [r if r is not None else [] for r in results]

    def execute_sequential(
        self,
        queries: list[str],
        retrieve_fn: Callable[[str], list[RetrievedChunk]],
    ) -> list[list[RetrievedChunk]]:
        """Execute retrieval for multiple queries sequentially.

        Args:
            queries: List of queries to retrieve for.
            retrieve_fn: Function that takes a query string and returns
                         a list of RetrievedChunk objects.

        Returns:
            List of chunk lists, one per query, in the same order as input queries.
        """
        results = []
        for i, query in enumerate(queries):
            try:
                chunks = retrieve_fn(query)
                results.append(chunks)
                logger.debug(
                    "Sequential retrieval completed for query %d/%d: %d chunks",
                    i + 1,
                    len(queries),
                    len(chunks),
                )
            except Exception as e:
                logger.warning("Sequential retrieval failed for query %d: %s", i, e)
                results.append([])
        return results

    def execute(
        self,
        queries: list[str],
        retrieve_fn: Callable[[str], list[RetrievedChunk]],
        parallel: bool = True,
    ) -> list[list[RetrievedChunk]]:
        """Execute retrieval with configurable parallelism.

        Args:
            queries: List of queries to retrieve for.
            retrieve_fn: Function that takes a query string and returns
                         a list of RetrievedChunk objects.
            parallel: Whether to execute in parallel (default: True).

        Returns:
            List of chunk lists, one per query, in the same order as input queries.
        """
        if parallel:
            return self.execute_parallel(queries, retrieve_fn)
        return self.execute_sequential(queries, retrieve_fn)