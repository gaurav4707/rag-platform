"""Offline retrieval evaluation orchestration.

Coordinates the evaluation workflow:
1. Load evaluation dataset
2. Run retriever for each query
3. Calculate metrics
4. Generate report
"""

import logging
from datetime import datetime
from pathlib import Path
from typing import Optional

from backend.evaluation.dataset import load_dataset
from backend.evaluation.metrics import aggregate_metrics, calculate_all_metrics
from backend.evaluation.models import (
    EvaluationReport,
    RetrievalEvaluationResult,
    RetrievedDocument,
)
from backend.rag.retrieval_config import RetrievalConfig
from backend.rag.retriever import retrieve_context
from backend.models.rag_models import RetrievalResult

logger = logging.getLogger(__name__)


def extract_document_ids(retrieval_result: RetrievalResult) -> list[str]:
    """Extract unique document IDs from retrieval result, preserving order."""
    doc_ids = []
    seen = set()
    for chunk in retrieval_result.chunks:
        doc_id = chunk.document.metadata.get("document_id")
        if doc_id and doc_id not in seen:
            seen.add(doc_id)
            doc_ids.append(doc_id)
    return doc_ids


def extract_pages(retrieval_result: RetrievalResult) -> list[int]:
    """Extract page numbers from retrieval result."""
    pages = []
    seen = set()
    for chunk in retrieval_result.chunks:
        page = chunk.document.metadata.get("page")
        if page is not None and page not in seen:
            seen.add(page)
            pages.append(page)
    return pages


def extract_chunks(retrieval_result: RetrievalResult) -> list[str]:
    """Extract chunk text content from retrieval result."""
    return [chunk.document.page_content for chunk in retrieval_result.chunks]


def create_retrieved_documents(retrieval_result: RetrievalResult) -> list[RetrievedDocument]:
    """Create RetrievedDocument objects from retrieval result."""
    docs = []
    seen = set()
    for chunk in retrieval_result.chunks:
        doc_id = chunk.document.metadata.get("document_id", "unknown")
        if doc_id not in seen:
            seen.add(doc_id)
            docs.append(
                RetrievedDocument(
                    document_id=doc_id,
                    filename=chunk.document.metadata.get("filename", "unknown"),
                    page=chunk.document.metadata.get("page"),
                    chunk_index=chunk.document.metadata.get("chunk_index"),
                    score=chunk.score,
                )
            )
    return docs


def evaluate_single_query(
    query,
    config: RetrievalConfig,
    top_k: int,
) -> RetrievalEvaluationResult:
    """Evaluate a single query against the retriever.

    Args:
        query: EvaluationQuery object with question and expected results.
        config: RetrievalConfig for the retriever.
        top_k: Number of top results to consider for metrics.

    Returns:
        RetrievalEvaluationResult with metrics.
    """
    logger.info("Evaluating query: %s", query.id)

    # Run retrieval using existing retriever
    _, retrieval_result = retrieve_context(
        query=query.question,
        config=config,
    )

    # Extract retrieved document IDs (ranked)
    retrieved_doc_ids = extract_document_ids(retrieval_result)
    retrieved_pages = extract_pages(retrieval_result)
    retrieved_chunks = extract_chunks(retrieval_result)
    retrieved_documents = create_retrieved_documents(retrieval_result)

    # Calculate metrics
    metrics = calculate_all_metrics(
        retrieved_doc_ids=retrieved_doc_ids,
        expected_doc_ids=query.expected_document_ids,
        k_values=[1, 3, 5, 10],
    )

    # Add K-specific metrics for the configured top_k
    k_metrics = {
        f"precision@{top_k}": metrics.get(f"precision@{top_k}", 0.0),
        f"recall@{top_k}": metrics.get(f"recall@{top_k}", 0.0),
        f"hit_rate@{top_k}": metrics.get(f"hit_rate@{top_k}", 0.0),
        f"f1@{top_k}": metrics.get(f"f1@{top_k}", 0.0),
        f"mrr@{top_k}": metrics.get("mrr", 0.0),
        f"ndcg@{top_k}": metrics.get(f"ndcg@{top_k}", 0.0),
    }
    metrics.update(k_metrics)

    return RetrievalEvaluationResult(
        query_id=query.id,
        question=query.question,
        retrieved_documents=retrieved_documents,
        retrieved_pages=retrieved_pages,
        retrieved_chunks=retrieved_chunks,
        metrics=metrics,
    )


def run_evaluation(
    dataset_path: str,
    config: RetrievalConfig,
    top_k: int = 5,
) -> EvaluationReport:
    """Run complete offline retrieval evaluation.

    Args:
        dataset_path: Path to JSON evaluation dataset.
        config: RetrievalConfig for the retriever.
        top_k: Number of top results to evaluate.

    Returns:
        EvaluationReport with aggregated metrics and per-query results.
    """
    logger.info("Loading dataset from: %s", dataset_path)
    queries = load_dataset(dataset_path)
    logger.info("Loaded %d evaluation queries", len(queries))

    results = []
    for query in queries:
        result = evaluate_single_query(query, config, top_k)
        results.append(result)

    # Aggregate metrics
    all_metrics = [r.metrics for r in results]
    aggregated = aggregate_metrics(all_metrics)

    # Build config dict for report
    config_dict = {
        "top_k": config.top_k,
        "search_type": config.search_type,
        "score_threshold": config.score_threshold,
        "fetch_k": config.fetch_k,
        "lambda_mult": config.lambda_mult,
        "reranker": config.reranker,
        "reranker_top_k": config.reranker_top_k,
        "hybrid_enabled": config.hybrid_enabled,
        "query_rewrite": config.query_rewrite,
    }

    report = EvaluationReport(
        timestamp=datetime.now().isoformat(),
        total_queries=len(queries),
        top_k=top_k,
        metrics=aggregated,
        results=results,
        retrieval_config=config_dict,
    )

    logger.info("Evaluation complete. Aggregated metrics: %s", aggregated)
    return report


def save_report(report: EvaluationReport, output_dir: str) -> str:
    """Save evaluation report to JSON file.

    Args:
        report: EvaluationReport to save.
        output_dir: Directory to save report in.

    Returns:
        Path to saved report file.
    """
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"evaluation_{timestamp}.json"
    filepath = output_path / filename

    report.save_json(str(filepath))
    logger.info("Report saved to: %s", filepath)

    return str(filepath)