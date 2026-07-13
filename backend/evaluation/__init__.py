"""Offline Retrieval Evaluation Framework.

This module provides tools for measuring retrieval quality during development.
It is completely separate from the production runtime and must never be imported
by production code (API, Services, Agent, etc.).

Components:
- models: Data structures for queries, results, and reports
- dataset: JSON dataset loading/saving
- metrics: Retrieval metrics (Precision@K, Recall@K, MRR, NDCG, MAP, etc.)
- evaluator: Orchestration layer that runs evaluation using existing retriever
- cli: Command-line interface for running evaluations
"""

from backend.evaluation.models import (
    EvaluationQuery,
    RetrievalEvaluationResult,
    EvaluationReport,
    RetrievedDocument,
)

from backend.evaluation.dataset import load_dataset, save_dataset

# Lazy imports for evaluator to avoid triggering production dependencies
# Use: from backend.evaluation import run_evaluation
# or:  from backend.evaluation.evaluator import run_evaluation

__all__ = [
    "EvaluationQuery",
    "RetrievalEvaluationResult",
    "EvaluationReport",
    "RetrievedDocument",
    "load_dataset",
    "save_dataset",
]