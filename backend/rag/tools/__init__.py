"""Tools package for the Agentic RAG system.

Exports all available tools for the Tool Registry.
"""

from backend.rag.tools.list_documents import list_documents
from backend.rag.tools.retrieve_context import retrieve_context
from backend.rag.tools.search_by_filename import search_by_filename


def get_tools() -> list:
    """Return all registered tools."""
    return [retrieve_context, list_documents, search_by_filename]


__all__ = [
    "retrieve_context",
    "list_documents",
    "search_by_filename",
    "get_tools",
]