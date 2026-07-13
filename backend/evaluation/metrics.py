"""Retrieval evaluation metrics.

Calculates standard retrieval metrics without external dependencies.
No vector database calls, no embeddings, no LLM calls.
"""

from typing import Optional


def precision_at_k(
    retrieved_doc_ids: list[str],
    expected_doc_ids: list[str],
    k: int,
) -> float:
    """Calculate Precision@K.

    Of the top K retrieved documents, how many are relevant?

    Formula: relevant_retrieved / total_retrieved (up to K)

    Args:
        retrieved_doc_ids: List of retrieved document IDs (ranked).
        expected_doc_ids: List of expected/relevant document IDs.
        k: Number of top results to consider.

    Returns:
        Precision@K score (0.0 to 1.0).
    """
    if not retrieved_doc_ids or not expected_doc_ids:
        return 0.0

    top_k = retrieved_doc_ids[:k]
    if not top_k:
        return 0.0

    expected_set = set(expected_doc_ids)
    relevant_count = sum(1 for doc_id in top_k if doc_id in expected_set)

    return relevant_count / len(top_k)


def recall_at_k(
    retrieved_doc_ids: list[str],
    expected_doc_ids: list[str],
    k: int,
) -> float:
    """Calculate Recall@K.

    Of the expected relevant documents, how many were found in top K?

    Formula: relevant_retrieved / total_expected_relevant

    Args:
        retrieved_doc_ids: List of retrieved document IDs (ranked).
        expected_doc_ids: List of expected/relevant document IDs.
        k: Number of top results to consider.

    Returns:
        Recall@K score (0.0 to 1.0).
    """
    if not expected_doc_ids:
        return 1.0

    if not retrieved_doc_ids:
        return 0.0

    top_k = retrieved_doc_ids[:k]
    expected_set = set(expected_doc_ids)
    relevant_count = sum(1 for doc_id in top_k if doc_id in expected_set)

    return relevant_count / len(expected_set)


def hit_rate(
    retrieved_doc_ids: list[str],
    expected_doc_ids: list[str],
    k: int,
) -> float:
    """Calculate Hit Rate@K.

    Returns 1 if at least one expected document appears in top K, else 0.

    Args:
        retrieved_doc_ids: List of retrieved document IDs (ranked).
        expected_doc_ids: List of expected/relevant document IDs.
        k: Number of top results to consider.

    Returns:
        1.0 if hit, 0.0 otherwise.
    """
    if not retrieved_doc_ids or not expected_doc_ids:
        return 0.0

    top_k = retrieved_doc_ids[:k]
    expected_set = set(expected_doc_ids)

    for doc_id in top_k:
        if doc_id in expected_set:
            return 1.0

    return 0.0


def mean_reciprocal_rank(
    retrieved_doc_ids: list[str],
    expected_doc_ids: list[str],
    k: Optional[int] = None,
) -> float:
    """Calculate Mean Reciprocal Rank (MRR).

    Measures ranking quality - where does the first relevant document appear?

    Formula: 1 / rank_of_first_relevant_document

    Args:
        retrieved_doc_ids: List of retrieved document IDs (ranked).
        expected_doc_ids: List of expected/relevant document IDs.
        k: Optional cutoff rank. If None, searches entire list.

    Returns:
        MRR score (0.0 to 1.0).
    """
    if not retrieved_doc_ids or not expected_doc_ids:
        return 0.0

    expected_set = set(expected_doc_ids)
    search_list = retrieved_doc_ids[:k] if k else retrieved_doc_ids

    for rank, doc_id in enumerate(search_list, start=1):
        if doc_id in expected_set:
            return 1.0 / rank

    return 0.0


def average_precision(
    retrieved_doc_ids: list[str],
    expected_doc_ids: list[str],
    k: Optional[int] = None,
) -> float:
    """Calculate Average Precision (AP).

    Precision averaged over all relevant documents in the ranked list.

    Args:
        retrieved_doc_ids: List of retrieved document IDs (ranked).
        expected_doc_ids: List of expected/relevant document IDs.
        k: Optional cutoff rank.

    Returns:
        Average Precision score (0.0 to 1.0).
    """
    if not retrieved_doc_ids or not expected_doc_ids:
        return 0.0

    expected_set = set(expected_doc_ids)
    search_list = retrieved_doc_ids[:k] if k else retrieved_doc_ids

    relevant_count = 0
    precision_sum = 0.0

    for i, doc_id in enumerate(search_list, start=1):
        if doc_id in expected_set:
            relevant_count += 1
            precision_sum += relevant_count / i

    if relevant_count == 0:
        return 0.0

    return precision_sum / len(expected_set)


def ndcg_at_k(
    retrieved_doc_ids: list[str],
    expected_doc_ids: list[str],
    k: int,
    relevance_scores: Optional[dict[str, float]] = None,
) -> float:
    """Calculate Normalized Discounted Cumulative Gain (NDCG@K).

    Accounts for ranking quality with graded relevance.

    Args:
        retrieved_doc_ids: List of retrieved document IDs (ranked).
        expected_doc_ids: List of expected/relevant document IDs.
        k: Number of top results to consider.
        relevance_scores: Optional dict mapping doc_id to relevance score (default: 1.0 for relevant, 0.0 for non-relevant).

    Returns:
        NDCG@K score (0.0 to 1.0).
    """
    if not retrieved_doc_ids or not expected_doc_ids:
        return 0.0

    if relevance_scores is None:
        relevance_scores = {doc_id: 1.0 for doc_id in expected_doc_ids}

    top_k = retrieved_doc_ids[:k]

    # DCG
    dcg = 0.0
    for i, doc_id in enumerate(top_k, start=1):
        rel = relevance_scores.get(doc_id, 0.0)
        if rel > 0:
            dcg += rel / (i.bit_length())  # log2(i+1) approximation using bit_length

    # IDCG (ideal DCG)
    ideal_rels = sorted(relevance_scores.values(), reverse=True)[:k]
    idcg = 0.0
    for i, rel in enumerate(ideal_rels, start=1):
        if rel > 0:
            idcg += rel / (i.bit_length())

    if idcg == 0:
        return 0.0

    return dcg / idcg


def f1_at_k(
    retrieved_doc_ids: list[str],
    expected_doc_ids: list[str],
    k: int,
) -> float:
    """Calculate F1@K (harmonic mean of Precision@K and Recall@K).

    Args:
        retrieved_doc_ids: List of retrieved document IDs (ranked).
        expected_doc_ids: List of expected/relevant document IDs.
        k: Number of top results to consider.

    Returns:
        F1@K score (0.0 to 1.0).
    """
    precision = precision_at_k(retrieved_doc_ids, expected_doc_ids, k)
    recall = recall_at_k(retrieved_doc_ids, expected_doc_ids, k)

    if precision + recall == 0:
        return 0.0

    return 2 * (precision * recall) / (precision + recall)


def calculate_all_metrics(
    retrieved_doc_ids: list[str],
    expected_doc_ids: list[str],
    k_values: Optional[list[int]] = None,
) -> dict:
    """Calculate all metrics for a single query.

    Args:
        retrieved_doc_ids: List of retrieved document IDs (ranked).
        expected_doc_ids: List of expected/relevant document IDs.
        k_values: List of K values to evaluate. Defaults to [1, 3, 5, 10].

    Returns:
        Dictionary with all metric scores.
    """
    if k_values is None:
        k_values = [1, 3, 5, 10]

    metrics = {}
    for k in k_values:
        metrics[f"precision@{k}"] = precision_at_k(retrieved_doc_ids, expected_doc_ids, k)
        metrics[f"recall@{k}"] = recall_at_k(retrieved_doc_ids, expected_doc_ids, k)
        metrics[f"hit_rate@{k}"] = hit_rate(retrieved_doc_ids, expected_doc_ids, k)
        metrics[f"f1@{k}"] = f1_at_k(retrieved_doc_ids, expected_doc_ids, k)

    metrics["mrr"] = mean_reciprocal_rank(retrieved_doc_ids, expected_doc_ids)
    metrics["map"] = average_precision(retrieved_doc_ids, expected_doc_ids)

    return metrics


def aggregate_metrics(results: list[dict], k_values: Optional[list[int]] = None) -> dict:
    """Aggregate metrics across multiple queries.

    Args:
        results: List of metric dictionaries from calculate_all_metrics.
        k_values: List of K values used.

    Returns:
        Dictionary with mean metrics across all queries.
    """
    if not results:
        return {}

    if k_values is None:
        k_values = [1, 3, 5, 10]

    aggregated = {}

    # Mean for each metric
    for k in k_values:
        for metric_name in [f"precision@{k}", f"recall@{k}", f"hit_rate@{k}", f"f1@{k}"]:
            values = [r.get(metric_name, 0.0) for r in results if metric_name in r]
            aggregated[metric_name] = sum(values) / len(values) if values else 0.0

    # MRR and MAP
    mrr_values = [r.get("mrr", 0.0) for r in results if "mrr" in r]
    aggregated["mrr"] = sum(mrr_values) / len(mrr_values) if mrr_values else 0.0

    map_values = [r.get("map", 0.0) for r in results if "map" in r]
    aggregated["map"] = sum(map_values) / len(map_values) if map_values else 0.0

    return aggregated