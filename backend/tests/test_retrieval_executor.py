"""Tests for the retrieval executor module."""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from backend.models.rag_models import RetrievedChunk
from backend.rag.retrieval_executor import RetrievalExecutor


def _make_chunk(text: str, score: float = 0.5) -> RetrievedChunk:
    from langchain_core.documents import Document
    return RetrievedChunk(
        document=Document(page_content=text, metadata={"document_id": "1", "chunk_index": 0}),
        score=score,
    )


class TestRetrievalExecutor:
    def test_default_max_workers(self):
        executor = RetrievalExecutor()
        assert executor.max_workers == 3

    def test_custom_max_workers(self):
        executor = RetrievalExecutor(max_workers=5)
        assert executor.max_workers == 5

    def test_execute_parallel_empty_queries(self):
        executor = RetrievalExecutor()
        result = executor.execute_parallel([], lambda q: [_make_chunk(q)])
        assert result == []

    def test_execute_parallel_single_query(self):
        executor = RetrievalExecutor()
        fn = MagicMock(return_value=[_make_chunk("result")])
        result = executor.execute_parallel(["query1"], fn)
        assert len(result) == 1
        assert len(result[0]) == 1
        assert result[0][0].document.page_content == "result"

    def test_execute_parallel_multiple_queries(self):
        executor = RetrievalExecutor()

        def fn(q: str) -> list:
            return [_make_chunk(f"result_{q}")]

        queries = ["q1", "q2", "q3"]
        result = executor.execute_parallel(queries, fn)
        assert len(result) == 3
        assert result[0][0].document.page_content == "result_q1"
        assert result[1][0].document.page_content == "result_q2"
        assert result[2][0].document.page_content == "result_q3"

    def test_execute_parallel_handles_exception(self):
        executor = RetrievalExecutor()

        def fn(q: str) -> list:
            if q == "fail":
                raise ValueError("boom")
            return [_make_chunk(f"ok_{q}")]

        result = executor.execute_parallel(["ok1", "fail", "ok2"], fn)
        assert len(result) == 3
        assert len(result[0]) == 1
        assert result[1] == []
        assert len(result[2]) == 1

    def test_execute_sequential_empty_queries(self):
        executor = RetrievalExecutor()
        result = executor.execute_sequential([], lambda q: [_make_chunk(q)])
        assert result == []

    def test_execute_sequential_single_query(self):
        executor = RetrievalExecutor()
        fn = MagicMock(return_value=[_make_chunk("result")])
        result = executor.execute_sequential(["query1"], fn)
        assert len(result) == 1
        assert len(result[0]) == 1

    def test_execute_sequential_multiple_queries(self):
        executor = RetrievalExecutor()
        fn = lambda q: [_make_chunk(f"result_{q}")]
        result = executor.execute_sequential(["a", "b"], fn)
        assert len(result) == 2

    def test_execute_sequential_handles_exception(self):
        executor = RetrievalExecutor()

        def fn(q: str) -> list:
            if q == "fail":
                raise ValueError("boom")
            return [_make_chunk(q)]

        result = executor.execute_sequential(["ok", "fail", "good"], fn)
        assert len(result) == 3
        assert len(result[0]) == 1
        assert result[1] == []
        assert len(result[2]) == 1

    def test_execute_default_parallel(self):
        executor = RetrievalExecutor()
        result = executor.execute(["q1"], lambda q: [_make_chunk(q)])
        assert len(result) == 1

    def test_execute_sequential_mode(self):
        executor = RetrievalExecutor()
        fn = MagicMock(return_value=[_make_chunk("x")])
        result = executor.execute(["q1", "q2"], fn, parallel=False)
        assert len(result) == 2
        assert fn.call_count == 2
