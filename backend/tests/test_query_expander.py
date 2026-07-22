"""Tests for the query expansion module."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from backend.rag.query_expander import (
    LLMQueryExpander,
    NoOpQueryExpander,
    QueryExpansionResult,
    get_query_expander,
)


class TestQueryExpansionResult:
    def test_holds_data(self):
        result = QueryExpansionResult(
            original_query="test",
            expanded_queries=["q1", "q2"],
            metadata={"strategy": "llm", "count": 2},
        )
        assert result.original_query == "test"
        assert result.expanded_queries == ["q1", "q2"]
        assert result.metadata == {"strategy": "llm", "count": 2}

    def test_default_metadata(self):
        result = QueryExpansionResult(
            original_query="test",
            expanded_queries=["test"],
            metadata={},
        )
        assert result.metadata == {}


class TestNoOpQueryExpander:
    def test_returns_original_query(self):
        expander = NoOpQueryExpander()
        result = expander.expand("test query")
        assert result.original_query == "test query"
        assert result.expanded_queries == ["test query"]
        assert result.metadata["strategy"] == "none"

    def test_preserves_empty(self):
        expander = NoOpQueryExpander()
        result = expander.expand("")
        assert result.expanded_queries == [""]

    def test_preserves_whitespace(self):
        expander = NoOpQueryExpander()
        result = expander.expand("   ")
        assert result.expanded_queries == ["   "]


class TestLLMQueryExpander:
    def test_default_num_queries(self):
        expander = LLMQueryExpander()
        assert expander.num_queries == 3

    def test_custom_num_queries(self):
        expander = LLMQueryExpander(num_queries=5)
        assert expander.num_queries == 5

    def test_empty_query_returns_as_is(self):
        expander = LLMQueryExpander()
        result = expander.expand("")
        assert result.expanded_queries == [""]
        assert result.metadata.get("fallback") is True

    def test_expand_success(self):
        expander = LLMQueryExpander(num_queries=3)
        mock_llm = MagicMock()
        mock_llm.invoke.return_value = MagicMock(
            content="query about climate\nclimate change effects\nimpact of global warming"
        )
        with patch.object(expander, "_get_llm", return_value=mock_llm):
            result = expander.expand("tell me about climate")
        assert result.original_query == "tell me about climate"
        assert len(result.expanded_queries) == 3
        assert result.expanded_queries[0] == "tell me about climate"
        assert result.metadata["strategy"] == "llm"

    def test_llm_not_available_falls_back(self):
        expander = LLMQueryExpander()
        with patch.object(expander, "_get_llm", return_value=None):
            result = expander.expand("test query")
        assert result.expanded_queries == ["test query"]
        assert result.metadata.get("fallback") is True

    def test_llm_failure_falls_back(self):
        expander = LLMQueryExpander()
        mock_llm = MagicMock()
        mock_llm.invoke.side_effect = Exception("API error")
        with patch.object(expander, "_get_llm", return_value=mock_llm):
            result = expander.expand("test query")
        assert result.expanded_queries == ["test query"]
        assert result.metadata.get("fallback") is True
        assert "error" in result.metadata

    def test_empty_response_uses_original(self):
        expander = LLMQueryExpander()
        mock_llm = MagicMock()
        mock_llm.invoke.return_value = MagicMock(content="")
        with patch.object(expander, "_get_llm", return_value=mock_llm):
            result = expander.expand("test query")
        assert result.expanded_queries == ["test query"]

    def test_parses_list_content(self):
        expander = LLMQueryExpander()
        mock_llm = MagicMock()
        mock_llm.invoke.return_value = MagicMock(
            content=[{"text": "query one"}, {"text": "query two"}]
        )
        with patch.object(expander, "_get_llm", return_value=mock_llm):
            result = expander.expand("test")
        assert len(result.expanded_queries) >= 2

    def test_parse_response_strips_numbering(self):
        expander = LLMQueryExpander()
        response = "1. first query\n2. second query\n3. third query"
        queries = expander._parse_response(response)
        assert len(queries) == 3
        assert all(q == q.strip() for q in queries)

    def test_parse_response_strips_bullets(self):
        expander = LLMQueryExpander()
        response = "- query a\n* query b\n• query c"
        queries = expander._parse_response(response)
        assert len(queries) == 3

    def test_build_prompt_includes_num_queries(self):
        expander = LLMQueryExpander(num_queries=4)
        prompt = expander._build_prompt("test")
        assert "4" in prompt
        assert "test" in prompt


class TestGetQueryExpander:
    def test_noop_strategy(self):
        expander = get_query_expander("none")
        assert isinstance(expander, NoOpQueryExpander)

    def test_llm_strategy(self):
        expander = get_query_expander("llm")
        assert isinstance(expander, LLMQueryExpander)
        assert expander.num_queries == 3

    def test_llm_strategy_with_custom_count(self):
        expander = get_query_expander("llm", num_queries=5)
        assert isinstance(expander, LLMQueryExpander)
        assert expander.num_queries == 5

    def test_invalid_strategy_raises(self):
        with pytest.raises(ValueError, match="Unknown query expansion strategy"):
            get_query_expander("invalid")
