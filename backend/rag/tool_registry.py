"""Tool Registry for the Agentic RAG system.

Registers and exposes available tools to the Agent.
"""

from backend.rag.tools import get_tools as _get_tools


def get_tools() -> list:
    """Return all registered tools."""
    return _get_tools()