"""Tests for the search_by_filename tool."""

from __future__ import annotations

from unittest.mock import patch

import pytest
from langchain_core.tools import BaseTool

from backend.rag.tools.search_by_filename import search_by_filename
from backend.rag.tools import get_tools


class TestSearchByFilenameTool:
    """Tests for the search_by_filename tool."""

    def test_search_by_filename_exact_match(self):
        """Test exact filename match."""
        mock_documents = [
            {"document_id": "doc1", "filename": "architecture.pdf", "file_hash": "hash1", "status": "indexed"},
            {"document_id": "doc2", "filename": "API_SPEC.pdf", "file_hash": "hash2", "status": "indexed"},
        ]

        with patch("backend.rag.tools.search_by_filename.search_documents_by_filename", return_value=mock_documents):
            serialized, artifact = search_by_filename.func("architecture.pdf")

        assert isinstance(serialized, str)
        assert "Found 2 matching document(s)" in serialized
        assert "architecture.pdf" in serialized
        assert "API_SPEC.pdf" in serialized
        assert artifact == mock_documents

    def test_search_by_filename_partial_match(self):
        """Test partial filename match."""
        mock_documents = [
            {"document_id": "doc1", "filename": "system_architecture.pdf", "file_hash": "hash1", "status": "indexed"},
            {"document_id": "doc2", "filename": "ARCHITECTURE_decisions.md", "file_hash": "hash2", "status": "indexed"},
        ]

        with patch("backend.rag.tools.search_by_filename.search_documents_by_filename", return_value=mock_documents):
            serialized, artifact = search_by_filename.func("architecture")

        assert "Found 2 matching document(s)" in serialized
        assert "system_architecture.pdf" in serialized
        assert "ARCHITECTURE_decisions.md" in serialized
        assert artifact == mock_documents

    def test_search_by_filename_case_insensitive(self):
        """Test case-insensitive matching."""
        mock_documents = [
            {"document_id": "doc1", "filename": "README.md", "file_hash": "hash1", "status": "indexed"},
        ]

        with patch("backend.rag.tools.search_by_filename.search_documents_by_filename", return_value=mock_documents):
            serialized, artifact = search_by_filename.func("readme")

        assert "README.md" in serialized
        assert artifact == mock_documents

    def test_search_by_filename_no_matches(self):
        """Test empty result when no documents match."""
        with patch("backend.rag.tools.search_by_filename.search_documents_by_filename", return_value=[]):
            serialized, artifact = search_by_filename.func("nonexistent.pdf")

        assert serialized == "No documents found matching 'nonexistent.pdf'."
        assert artifact == []

    def test_search_by_filename_is_tool(self):
        """Test that search_by_filename is a LangChain tool."""
        assert isinstance(search_by_filename, BaseTool)
        assert search_by_filename.name == "search_by_filename"

    def test_search_by_filename_registered_in_tools(self):
        """Test that search_by_filename is registered in the tools registry."""
        tools = get_tools()
        tool_names = [tool.name for tool in tools]
        assert "search_by_filename" in tool_names
        assert "retrieve_context" in tool_names
        assert "list_documents" in tool_names

    def test_search_by_filename_delegates_to_service(self):
        """Test that search_by_filename delegates to DocumentService."""
        mock_documents = [{"document_id": "doc1", "filename": "test.pdf", "file_hash": "hash", "status": "indexed"}]

        with patch("backend.rag.tools.search_by_filename.search_documents_by_filename") as mock_service:
            mock_service.return_value = mock_documents
            serialized, artifact = search_by_filename.func("test")

        mock_service.assert_called_once_with("test")
        assert artifact == mock_documents

    def test_search_by_filename_serialization_format(self):
        """Test the serialization format includes document details."""
        mock_documents = [
            {"document_id": "abc123", "filename": "report.pdf", "file_hash": "hash1", "status": "indexed"},
            {"document_id": "def456", "filename": "summary.pdf", "file_hash": "hash2", "status": "indexed"},
        ]

        with patch("backend.rag.tools.search_by_filename.search_documents_by_filename", return_value=mock_documents):
            serialized, artifact = search_by_filename.func("report")

        # Serialized content should be user-friendly (no internal IDs or status)
        assert "report.pdf" in serialized
        assert "summary.pdf" in serialized
        assert "Found 2 matching document(s)" in serialized

        # Internal IDs should remain in the structured artifact only
        assert artifact[0]["document_id"] == "abc123"
        assert artifact[1]["document_id"] == "def456"
        assert artifact[0]["status"] == "indexed"

    def test_search_by_filename_empty_string(self):
        """Test search with empty string returns all documents."""
        mock_documents = [
            {"document_id": "doc1", "filename": "test.pdf", "file_hash": "hash1", "status": "indexed"},
            {"document_id": "doc2", "filename": "another.pdf", "file_hash": "hash2", "status": "indexed"},
        ]

        with patch("backend.rag.tools.search_by_filename.search_documents_by_filename", return_value=mock_documents):
            serialized, artifact = search_by_filename.func("")

        # Empty string matches all filenames
        assert "Found 2 matching document(s)" in serialized
        assert artifact == mock_documents

    def test_search_by_filename_special_characters(self):
        """Test search handles special characters in filename."""
        mock_documents = [
            {"document_id": "doc1", "filename": "API-v2.0_spec.pdf", "file_hash": "hash1", "status": "indexed"},
        ]

        with patch("backend.rag.tools.search_by_filename.search_documents_by_filename", return_value=mock_documents):
            serialized, artifact = search_by_filename.func("v2.0")

        assert "API-v2.0_spec.pdf" in serialized
        assert artifact == mock_documents


class TestToolsRegistry:
    """Tests for the tools registry."""

    def test_get_tools_returns_all_three_tools(self):
        """Test that get_tools returns all three tools."""
        tools = get_tools()
        assert len(tools) == 3
        tool_names = {tool.name for tool in tools}
        assert tool_names == {"retrieve_context", "list_documents", "search_by_filename"}

    def test_tools_are_langchain_tools(self):
        """Test that all registered tools are LangChain tools."""
        from langchain_core.tools import BaseTool

        tools = get_tools()
        for tool in tools:
            assert isinstance(tool, BaseTool)