"""Search by Filename tool for the Agentic RAG system.

This module provides the `search_by_filename` tool that allows the Agent
to discover indexed documents matching a filename pattern.

Matching Strategy:
- Case-insensitive substring matching
- No fuzzy matching, regular expressions, or semantic matching
- Returns all documents where the query string appears in the filename
"""

import logging
from typing import Any

from langchain.tools import tool

from backend.services.document_service import search_documents_by_filename

logger = logging.getLogger(__name__)


@tool(response_format="content_and_artifact")
def search_by_filename(filename: str) -> tuple[str, list[dict[str, Any]]]:
    """Search for indexed documents matching a filename.

    Performs case-insensitive partial matching on document filenames.
    Use this to find document IDs before retrieving context from specific documents.

    Args:
        filename: Filename or partial filename to search for
            (e.g., "architecture", "API_SPEC.pdf", "readme")

    Returns:
        Tuple of (serialized_message, artifact_list)
    """
    logger.debug("Searching documents by filename: %s", filename)

    documents = search_documents_by_filename(filename)

    if not documents:
        serialized = f"No documents found matching '{filename}'."
    else:
        serialized = f"Found {len(documents)} matching document(s).\n"
        for doc in documents:
            serialized += f"- {doc['filename']}\n"

    logger.debug("Found %d documents matching '%s'", len(documents), filename)
    return serialized, documents