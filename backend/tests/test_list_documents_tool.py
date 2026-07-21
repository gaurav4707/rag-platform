"""Tests for the list_documents tool."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest
from langchain_core.tools import BaseTool

from backend.rag.tools.list_documents import list_documents
from backend.rag.tools import get_tools


class TestListDocumentsTool:
    """Tests for the list_documents tool."""

    def test_list_documents_returns_documents(self):
        """Test that list_documents returns documents when available."""
        mock_documents = [
            {"document_id": "doc1", "filename": "test1.pdf", "status": "indexed"},
            {"document_id": "doc2", "filename": "test2.pdf", "status": "indexed"},
        ]

        with patch("backend.rag.tools.list_documents.list_indexed_documents", return_value=mock_documents):
            serialized, artifact = list_documents.func()

        assert isinstance(serialized, str)
        assert "Found 2 document(s)" in serialized
        assert "test1.pdf" in serialized
        assert "test2.pdf" in serialized
        assert artifact == mock_documents

    def test_list_documents_returns_empty_list(self):
        """Test that list_documents returns empty list when no documents."""
        with patch("backend.rag.tools.list_documents.list_indexed_documents", return_value=[]):
            serialized, artifact = list_documents.func()

        assert isinstance(serialized, str)
        assert serialized == "No documents have been uploaded yet."
        assert artifact == []

    def test_list_documents_is_tool(self):
        """Test that list_documents is a LangChain tool."""
        assert isinstance(list_documents, BaseTool)
        assert list_documents.name == "list_documents"

    def test_list_documents_registered_in_tools(self):
        """Test that list_documents is registered in the tools registry."""
        tools = get_tools()
        tool_names = [tool.name for tool in tools]
        assert "list_documents" in tool_names
        assert "retrieve_context" in tool_names

    def test_list_documents_delegates_to_service(self):
        """Test that list_documents delegates to DocumentService."""
        mock_documents = [{"document_id": "doc1", "filename": "test.pdf", "status": "indexed"}]

        with patch("backend.rag.tools.list_documents.list_indexed_documents") as mock_service:
            mock_service.return_value = mock_documents
            serialized, artifact = list_documents.func()

        mock_service.assert_called_once()
        assert artifact == mock_documents

    def test_list_documents_serialization_format(self):
        """Test the serialization format includes document details."""
        mock_documents = [
            {"document_id": "abc123", "filename": "report.pdf", "status": "indexed"},
            {"document_id": "def456", "filename": "summary.pdf", "status": "indexed"},
        ]

        with patch("backend.rag.tools.list_documents.list_indexed_documents", return_value=mock_documents):
            serialized, artifact = list_documents.func()

        # Check serialized output contains key information
        assert "report.pdf" in serialized
        assert "summary.pdf" in serialized
        assert "abc123" in serialized
        assert "def456" in serialized
        assert "indexed" in serialized


class TestToolsRegistry:
    """Tests for the tools registry."""

    def test_get_tools_returns_all_tools(self):
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