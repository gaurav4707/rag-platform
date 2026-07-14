"""Tests for the query_parser module."""

import pytest
from backend.rag.query_parser import (
    ParsedQuery,
    parse_query,
    build_metadata_filter,
    parse_query_for_retrieval,
    PAGE_PATTERN,
)


class TestParseQuery:
    """Tests for the parse_query function."""

    def test_page_1(self):
        """Test parsing 'page 1'."""
        result = parse_query("Summarize page 1")
        assert result.page == 1
        assert result.cleaned_query == "Summarize"
        assert result.original_query == "Summarize page 1"

    def test_page_15(self):
        """Test parsing 'page 15'."""
        result = parse_query("Explain page 15")
        assert result.page == 15
        assert result.cleaned_query == "Explain"

    def test_uppercase_PAGE(self):
        """Test case-insensitive PAGE detection."""
        result = parse_query("What is on PAGE 7?")
        assert result.page == 7
        assert result.cleaned_query == "What is on"

    def test_punctuation_after_page(self):
        """Test page reference with trailing punctuation."""
        result = parse_query("Summarize page 2.")
        assert result.page == 2
        assert result.cleaned_query == "Summarize"

    def test_pg_abbreviation(self):
        """Test 'pg' abbreviation."""
        result = parse_query("Show pg 5")
        assert result.page == 5
        assert result.cleaned_query == "Show"

    def test_p_abbreviation(self):
        """Test 'p.' abbreviation."""
        result = parse_query("What does p. 3 discuss?")
        assert result.page == 3
        assert result.cleaned_query == "What does discuss"

    def test_no_page(self):
        """Test query without page reference."""
        result = parse_query("What is this document about?")
        assert result.page is None
        assert result.cleaned_query == "What is this document about?"

    def test_page_zero(self):
        """Test page 0 is rejected."""
        result = parse_query("Go to page 0")
        assert result.page is None
        assert result.cleaned_query == "Go to page 0"

    def test_negative_page(self):
        """Test negative page is rejected."""
        result = parse_query("Show page -5")
        assert result.page is None
        assert result.cleaned_query == "Show page -5"

    def test_multiple_pages_uses_first(self):
        """Test multiple page references uses the first."""
        result = parse_query("Compare page 2 and page 5")
        assert result.page == 2
        # The rest should remain in cleaned query
        assert "page 5" in result.cleaned_query

    def test_empty_query(self):
        """Test empty query returns empty result."""
        result = parse_query("")
        assert result.page is None
        assert result.cleaned_query == ""

    def test_whitespace_only(self):
        """Test whitespace-only query."""
        result = parse_query("   ")
        assert result.page is None
        assert result.cleaned_query == ""

    def test_page_at_start(self):
        """Test page reference at the beginning."""
        result = parse_query("page 3 summarize")
        assert result.page == 3
        assert result.cleaned_query == "summarize"

    def test_page_at_end(self):
        """Test page reference at the end."""
        result = parse_query("summarize page 3")
        assert result.page == 3
        assert result.cleaned_query == "summarize"

    def test_page_in_middle(self):
        """Test page reference in the middle."""
        result = parse_query("what is on page 4 of the doc")
        assert result.page == 4
        assert result.cleaned_query == "what is on of the doc"

    def test_capitalization_variants(self):
        """Test various capitalizations."""
        for query in ["Page 2", "PAGE 2", "Page 2", "pAge 2"]:
            result = parse_query(query)
            assert result.page == 2, f"Failed for {query}"

    def test_p_with_dot(self):
        """Test 'p.' with dot."""
        result = parse_query("Check p. 10")
        assert result.page == 10
        assert result.cleaned_query == "Check"

    def test_p_without_dot(self):
        """Test 'p' without dot."""
        result = parse_query("Check p 10")
        assert result.page == 10
        assert result.cleaned_query == "Check"

    def test_give_me_page(self):
        """Test 'Give me page X' pattern."""
        result = parse_query("Give me page 8")
        assert result.page == 8
        assert result.cleaned_query == "Give me"

    def test_show_page(self):
        """Test 'Show page X' pattern."""
        result = parse_query("Show page 10")
        assert result.page == 10
        assert result.cleaned_query == "Show"


class TestBuildMetadataFilter:
    """Tests for the build_metadata_filter function."""

    def test_page_only(self):
        """Test building filter with only page."""
        filter_dict = build_metadata_filter(page=5, existing_filter=None)
        assert filter_dict == {"page": 5}

    def test_existing_filter_only(self):
        """Test building filter with only existing filter."""
        existing = {"document_id": "abc123"}
        filter_dict = build_metadata_filter(page=None, existing_filter=existing)
        assert filter_dict == {"document_id": "abc123"}

    def test_both_page_and_existing(self):
        """Test building filter with both page and existing filter."""
        existing = {"document_id": "abc123"}
        filter_dict = build_metadata_filter(page=3, existing_filter=existing)
        # ChromaDB uses $and for multiple filters
        assert filter_dict == {"$and": [{"document_id": "abc123"}, {"page": 3}]}

    def test_neither(self):
        """Test building filter with neither."""
        filter_dict = build_metadata_filter(page=None, existing_filter=None)
        assert filter_dict is None

    def test_empty_existing_filter(self):
        """Test building filter with empty existing filter."""
        filter_dict = build_metadata_filter(page=2, existing_filter={})
        assert filter_dict == {"page": 2}


class TestParseQueryForRetrieval:
    """Tests for the parse_query_for_retrieval convenience function."""

    def test_with_page(self):
        """Test with page reference."""
        cleaned, filter_dict = parse_query_for_retrieval("Summarize page 4")
        assert cleaned == "Summarize"
        assert filter_dict == {"page": 4}

    def test_without_page(self):
        """Test without page reference."""
        cleaned, filter_dict = parse_query_for_retrieval("What is this?")
        assert cleaned == "What is this?"
        assert filter_dict is None


class TestPatternMatching:
    """Tests for the PAGE_PATTERN regex."""

    def test_pattern_matches_page(self):
        assert PAGE_PATTERN.search("page 2") is not None

    def test_pattern_matches_pg(self):
        assert PAGE_PATTERN.search("pg 3") is not None

    def test_pattern_matches_p_with_dot(self):
        assert PAGE_PATTERN.search("p. 5") is not None

    def test_pattern_matches_p_without_dot(self):
        assert PAGE_PATTERN.search("p 5") is not None

    def test_pattern_case_insensitive(self):
        assert PAGE_PATTERN.search("PAGE 2") is not None
        assert PAGE_PATTERN.search("Page 2") is not None
        assert PAGE_PATTERN.search("PaGe 2") is not None

    def test_pattern_no_match(self):
        assert PAGE_PATTERN.search("what is this") is None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])