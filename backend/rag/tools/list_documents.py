"""List Documents tool for the Agentic RAG system.

This module provides the `list_documents` tool that allows the Agent
to retrieve a list of all indexed documents.
"""

import logging
from typing import Any

from langchain.tools import tool

from backend.services.document_service import list_indexed_documents

logger = logging.getLogger(__name__)


@tool(response_format="content_and_artifact")
def list_documents() -> tuple[str, list[dict[str, Any]]]:
    """List all indexed documents.

    Returns a list of documents with their IDs, filenames, and status.
    """
    logger.debug("Listing indexed documents")

    documents = list_indexed_documents()

    if not documents:
        serialized = "No documents have been uploaded yet."
    else:
        serialized = f"Found {len(documents)} document(s):\n"
        for doc in documents:
            serialized += f"- {doc['filename']} (ID: {doc['document_id']}, Status: {doc['status']})\n"

    logger.debug("Listed %d documents", len(documents))

    return serialized, documents