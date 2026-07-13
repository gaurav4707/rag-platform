"""Evaluation dataset loading.

Loads evaluation queries with expected relevant documents from JSON files.
"""

import json
from pathlib import Path
from typing import Any

from backend.evaluation.models import EvaluationQuery


def load_dataset(path: str) -> list[EvaluationQuery]:
    """Load evaluation dataset from JSON file.

    Expected format:
    [
        {
            "id": "q1",
            "question": "What is RAG?",
            "expected_document_ids": ["rag-paper.pdf"],
            "expected_pages": [2],
            "metadata": {"category": "definition"}
        }
    ]

    Args:
        path: Path to JSON dataset file.

    Returns:
        List of EvaluationQuery objects.

    Raises:
        FileNotFoundError: If file doesn't exist.
        ValueError: If JSON format is invalid.
    """
    file_path = Path(path)
    if not file_path.exists():
        raise FileNotFoundError(f"Dataset file not found: {path}")

    with open(file_path) as f:
        data = json.load(f)

    if not isinstance(data, list):
        raise ValueError("Dataset must be a JSON array")

    queries = []
    for item in data:
        if not isinstance(item, dict):
            raise ValueError("Each dataset item must be an object")

        query_id = item.get("id")
        question = item.get("question")

        if not query_id or not question:
            raise ValueError("Each query must have 'id' and 'question' fields")

        expected_doc_ids = item.get("expected_document_ids", [])
        expected_pages = item.get("expected_pages", [])
        metadata = item.get("metadata", {})

        queries.append(
            EvaluationQuery(
                id=query_id,
                question=question,
                expected_document_ids=expected_doc_ids,
                expected_pages=expected_pages,
                metadata=metadata,
            )
        )

    return queries


def save_dataset(queries: list[EvaluationQuery], path: str) -> None:
    """Save evaluation dataset to JSON file.

    Args:
        queries: List of EvaluationQuery objects.
        path: Output file path.
    """
    data = []
    for q in queries:
        item = {
            "id": q.id,
            "question": q.question,
            "expected_document_ids": q.expected_document_ids,
            "expected_pages": q.expected_pages,
            "metadata": q.metadata,
        }
        data.append(item)

    Path(path).write_text(json.dumps(data, indent=2))