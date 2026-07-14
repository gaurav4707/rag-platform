"""Query parser for extracting structured retrieval constraints from user queries.

This module provides functionality to parse user queries for explicit metadata
constraints (e.g., page numbers) and return a cleaned query for semantic search.
"""

from __future__ import annotations

import logging
import re
from dataclasses import dataclass
from typing import Any

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class ParsedQuery:
    """Result of parsing a user query for retrieval constraints.

    Attributes:
        original_query: The unmodified user query.
        cleaned_query: The query with page references removed, for semantic search.
        page: The detected page number, or None if no page reference found.
    """
    original_query: str
    cleaned_query: str
    page: int | None


# Regex pattern to match page references
# Matches: "page 2", "page 15", "Page 7", "PAGE 3", "p. 5", "p.5", "pg 4", etc.
# Also captures trailing whitespace and punctuation like . , ! but NOT ?
PAGE_PATTERN = re.compile(
    r"""(?ix)
    \b
    (?:page|pg|p)\.?\s*  # "page", "pg", or "p" followed by optional dot and whitespace
    (\d+)                # Capture the page number
    \b
    [\s\.\!\,]*          # Optional trailing whitespace and punctuation (not ?)
    """
)


def parse_query(query: str) -> ParsedQuery:
    """Parse a user query for page references and other metadata constraints.

    Detects patterns like "page 2", "Page 15", "p. 7", "pg 3" and extracts
    the page number while returning a cleaned query suitable for semantic search.

    Args:
        query: The original user query.

    Returns:
        ParsedQuery with original_query, cleaned_query, and page (or None).
    """
    if not query or not query.strip():
        return ParsedQuery(
            original_query=query,
            cleaned_query="",
            page=None,
        )

    original = query.strip()

    # Find all page references
    matches = list(PAGE_PATTERN.finditer(original))

    if not matches:
        logger.debug("No page reference detected in query: %s", original)
        return ParsedQuery(
            original_query=original,
            cleaned_query=original,
            page=None,
        )

    # Use the first match (if multiple, log a warning)
    if len(matches) > 1:
        logger.warning(
            "Multiple page references found in query, using first: %s",
            original,
        )

    match = matches[0]
    page_str = match.group(1)

    try:
        page = int(page_str)
    except ValueError:
        logger.warning("Failed to parse page number from: %s", page_str)
        return ParsedQuery(
            original_query=original,
            cleaned_query=original,
            page=None,
        )

    # Validate page number (pages are 1-indexed in most documents)
    if page < 1:
        logger.warning("Invalid page number (must be >= 1): %d", page)
        return ParsedQuery(
            original_query=original,
            cleaned_query=original,
            page=None,
        )

    # Remove the page reference from the query for semantic search
    # Replace the matched portion with empty string
    cleaned = (
        original[: match.start()] + original[match.end() :]
    ).strip()

    # Clean up any double spaces or leading/trailing whitespace
    cleaned = re.sub(r"\s+", " ", cleaned).strip()
    # Remove space before punctuation
    cleaned = re.sub(r"\s+([\.\,\!\?\;\:])", r"\1", cleaned)
    # Strip leading/trailing punctuation
    cleaned = cleaned.strip(".,;:!?")

    logger.debug(
        "Detected page query: page=%d, cleaned_query=%r",
        page,
        cleaned,
    )

    return ParsedQuery(
        original_query=original,
        cleaned_query=cleaned,
        page=page,
    )


def build_metadata_filter(
    page: int | None,
    existing_filter: dict[str, Any] | None,
) -> dict[str, Any] | None:
    """Build a combined metadata filter for vector store queries.

    Merges a page filter with any existing metadata filter.
    ChromaDB requires multiple conditions to be combined with $and operator.

    Args:
        page: Page number to filter by, or None.
        existing_filter: Existing metadata filter dict, or None.

    Returns:
        Combined filter dict compatible with ChromaDB, or None if no filters apply.
    """
    filters = []

    # Add existing filter conditions
    if existing_filter:
        for key, value in existing_filter.items():
            filters.append({key: value})

    # Add page filter if specified
    if page is not None:
        # Note: In the vector store, page numbers are stored as integers
        filters.append({"page": page})

    if not filters:
        return None

    if len(filters) == 1:
        return filters[0]

    # Multiple conditions: use $and operator
    return {"$and": filters}


def parse_query_for_retrieval(query: str) -> tuple[str, dict[str, Any] | None]:
    """Convenience function to parse query and return cleaned query + filter.

    This is a simpler interface for direct use in retrieval pipelines.

    Args:
        query: The user query.

    Returns:
        Tuple of (cleaned_query, metadata_filter_dict_or_None).
    """
    parsed = parse_query(query)
    filter_dict = build_metadata_filter(parsed.page, None)
    return parsed.cleaned_query, filter_dict