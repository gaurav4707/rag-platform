"""Retrieve Context Tool for the Agentic RAG system.

This module re-exports the retrieve_context tool from the retriever module
to maintain backward compatibility while organizing tools in the tools package.
"""

from backend.rag.retriever import retrieve_context

__all__ = ["retrieve_context"]