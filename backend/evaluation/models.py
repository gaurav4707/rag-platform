"""Evaluation data models.

Defines data structures for offline retrieval evaluation.
"""

from dataclasses import dataclass, field
from typing import Optional


@dataclass
class EvaluationQuery:
    """Represents a single test query with expected relevant documents.

    Example:
        EvaluationQuery(
            id="q1",
            question="What is attention mechanism?",
            expected_document_ids=["paper.pdf"],
            expected_pages=[5, 6]
        )
    """

    id: str
    question: str
    expected_document_ids: list[str] = field(default_factory=list)
    expected_pages: list[int] = field(default_factory=list)
    metadata: dict = field(default_factory=dict)


@dataclass
class RetrievedDocument:
    """Represents a document retrieved during evaluation."""

    document_id: str
    filename: str
    page: Optional[int] = None
    chunk_index: Optional[int] = None
    score: Optional[float] = None


@dataclass
class RetrievalEvaluationResult:
    """Represents one evaluated retrieval attempt."""

    query_id: str
    question: str
    retrieved_documents: list[RetrievedDocument] = field(default_factory=list)
    retrieved_pages: list[int] = field(default_factory=list)
    retrieved_chunks: list[str] = field(default_factory=list)
    metrics: dict = field(default_factory=dict)


@dataclass
class EvaluationReport:
    """Complete evaluation report."""

    total_queries: int
    metrics: dict
    results: list[RetrievalEvaluationResult] = field(default_factory=list)
    timestamp: str = ""
    retrieval_config: dict = field(default_factory=dict)

    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization."""
        return {
            "total_queries": self.total_queries,
            "metrics": self.metrics,
            "results": [
                {
                    "query_id": r.query_id,
                    "question": r.question,
                    "retrieved_documents": [
                        {
                            "document_id": d.document_id,
                            "filename": d.filename,
                            "page": d.page,
                            "chunk_index": d.chunk_index,
                            "score": d.score,
                        }
                        for d in r.retrieved_documents
                    ],
                    "retrieved_pages": r.retrieved_pages,
                    "retrieved_chunks": r.retrieved_chunks,
                    "metrics": r.metrics,
                }
                for r in self.results
            ],
            "timestamp": self.timestamp,
            "retrieval_config": self.retrieval_config,
        }

    def save_json(self, path: str) -> None:
        """Save report as JSON file."""
        import json
        from pathlib import Path

        Path(path).parent.mkdir(parents=True, exist_ok=True)
        Path(path).write_text(json.dumps(self.to_dict(), indent=2))