"""Tests for evaluation metrics.

These tests run offline - no vector database, no embeddings, no LLM calls.
"""

import pytest

from backend.evaluation.metrics import (
    aggregate_metrics,
    average_precision,
    calculate_all_metrics,
    f1_at_k,
    hit_rate,
    mean_reciprocal_rank,
    ndcg_at_k,
    precision_at_k,
    recall_at_k,
)


class TestPrecisionAtK:
    """Tests for Precision@K metric."""

    def test_perfect_precision(self):
        """All retrieved docs are relevant."""
        retrieved = ["doc1", "doc2", "doc3"]
        expected = ["doc1", "doc2", "doc3"]
        assert precision_at_k(retrieved, expected, 3) == 1.0

    def test_zero_precision(self):
        """No retrieved docs are relevant."""
        retrieved = ["doc4", "doc5", "doc6"]
        expected = ["doc1", "doc2", "doc3"]
        assert precision_at_k(retrieved, expected, 3) == 0.0

    def test_partial_precision(self):
        """Some retrieved docs are relevant."""
        retrieved = ["doc1", "doc4", "doc2"]
        expected = ["doc1", "doc2", "doc3"]
        assert precision_at_k(retrieved, expected, 3) == 2.0 / 3.0

    def test_precision_at_k_less_than_results(self):
        """K is smaller than number of retrieved docs."""
        retrieved = ["doc1", "doc2", "doc3", "doc4"]
        expected = ["doc1", "doc2"]
        assert precision_at_k(retrieved, expected, 2) == 1.0

    def test_empty_retrieved(self):
        """No documents retrieved."""
        assert precision_at_k([], ["doc1"], 5) == 0.0

    def test_empty_expected(self):
        """No expected relevant documents."""
        assert precision_at_k(["doc1", "doc2"], [], 5) == 0.0


class TestRecallAtK:
    """Tests for Recall@K metric."""

    def test_perfect_recall(self):
        """All expected docs found."""
        retrieved = ["doc1", "doc2", "doc3"]
        expected = ["doc1", "doc2"]
        assert recall_at_k(retrieved, expected, 3) == 1.0

    def test_zero_recall(self):
        """No expected docs found."""
        retrieved = ["doc4", "doc5"]
        expected = ["doc1", "doc2"]
        assert recall_at_k(retrieved, expected, 5) == 0.0

    def test_partial_recall(self):
        """Some expected docs found."""
        retrieved = ["doc1", "doc4", "doc5"]
        expected = ["doc1", "doc2", "doc3"]
        assert recall_at_k(retrieved, expected, 3) == 1.0 / 3.0

    def test_recall_k_larger_than_retrieved(self):
        """K is larger than retrieved results."""
        retrieved = ["doc1"]
        expected = ["doc1", "doc2"]
        assert recall_at_k(retrieved, expected, 10) == 0.5

    def test_empty_expected(self):
        """No expected documents - recall is 1.0 by convention."""
        assert recall_at_k(["doc1"], [], 5) == 1.0


class TestHitRate:
    """Tests for Hit Rate@K metric."""

    def test_hit_when_relevant_in_top_k(self):
        """Returns 1.0 when relevant doc in top K."""
        retrieved = ["doc4", "doc1", "doc5"]
        expected = ["doc1", "doc2"]
        assert hit_rate(retrieved, expected, 2) == 1.0

    def test_miss_when_no_relevant_in_top_k(self):
        """Returns 0.0 when no relevant doc in top K."""
        retrieved = ["doc4", "doc5", "doc1"]
        expected = ["doc1", "doc2"]
        assert hit_rate(retrieved, expected, 2) == 0.0

    def test_hit_with_k_larger_than_list(self):
        """Hit when K exceeds list length."""
        retrieved = ["doc1"]
        expected = ["doc1"]
        assert hit_rate(retrieved, expected, 10) == 1.0


class TestMeanReciprocalRank:
    """Tests for MRR metric."""

    def test_first_result_relevant(self):
        """MRR = 1.0 when first result is relevant."""
        retrieved = ["doc1", "doc2", "doc3"]
        expected = ["doc1"]
        assert mean_reciprocal_rank(retrieved, expected) == 1.0

    def test_second_result_relevant(self):
        """MRR = 1/2 when second result is relevant."""
        retrieved = ["doc4", "doc1", "doc3"]
        expected = ["doc1"]
        assert mean_reciprocal_rank(retrieved, expected) == 0.5

    def test_third_result_relevant(self):
        """MRR = 1/3 when third result is relevant."""
        retrieved = ["doc4", "doc5", "doc1"]
        expected = ["doc1"]
        assert mean_reciprocal_rank(retrieved, expected) == 1.0 / 3.0

    def test_no_relevant_results(self):
        """MRR = 0.0 when no relevant results."""
        retrieved = ["doc4", "doc5"]
        expected = ["doc1"]
        assert mean_reciprocal_rank(retrieved, expected) == 0.0

    def test_mrr_with_cutoff_k(self):
        """MRR respects K cutoff."""
        retrieved = ["doc4", "doc1"]
        expected = ["doc1"]
        assert mean_reciprocal_rank(retrieved, expected, k=1) == 0.0


class TestAveragePrecision:
    """Tests for Average Precision (AP) metric."""

    def test_perfect_ap(self):
        """AP = 1.0 when all relevant at top."""
        retrieved = ["doc1", "doc2", "doc3"]
        expected = ["doc1", "doc2", "doc3"]
        assert average_precision(retrieved, expected) == 1.0

    def test_zero_ap(self):
        """AP = 0.0 when no relevant retrieved."""
        retrieved = ["doc4", "doc5"]
        expected = ["doc1", "doc2"]
        assert average_precision(retrieved, expected) == 0.0

    def test_partial_ap(self):
        """AP calculation with partial relevance."""
        retrieved = ["doc1", "doc4", "doc2", "doc5", "doc3"]
        expected = ["doc1", "doc2", "doc3"]
        # Precision at ranks 1, 3, 5: 1/1, 2/3, 3/5 = 1.0, 0.667, 0.6
        # AP = (1.0 + 0.667 + 0.6) / 3 = 0.756
        ap = average_precision(retrieved, expected)
        assert abs(ap - 0.7555) < 0.01


class TestF1AtK:
    """Tests for F1@K metric."""

    def test_perfect_f1(self):
        """F1 = 1.0 when precision and recall are perfect."""
        retrieved = ["doc1", "doc2"]
        expected = ["doc1", "doc2"]
        assert f1_at_k(retrieved, expected, 2) == 1.0

    def test_zero_f1(self):
        """F1 = 0.0 when either precision or recall is 0."""
        retrieved = ["doc4", "doc5"]
        expected = ["doc1", "doc2"]
        assert f1_at_k(retrieved, expected, 2) == 0.0


class TestNDCGAtK:
    """Tests for NDCG@K metric."""

    def test_perfect_ndcg(self):
        """NDCG = 1.0 for perfect ranking."""
        retrieved = ["doc1", "doc2", "doc3"]
        expected = ["doc1", "doc2", "doc3"]
        assert ndcg_at_k(retrieved, expected, 3) == 1.0

    def test_ndcg_with_scores(self):
        """NDCG with graded relevance scores."""
        retrieved = ["doc1", "doc2", "doc3"]
        expected = ["doc1", "doc2", "doc3"]
        scores = {"doc1": 3.0, "doc2": 2.0, "doc3": 1.0}
        ndcg = ndcg_at_k(retrieved, expected, 3, scores)
        assert ndcg > 0.8


class TestCalculateAllMetrics:
    """Tests for calculate_all_metrics function."""

    def test_returns_all_metrics(self):
        """Returns dictionary with all expected metrics."""
        retrieved = ["doc1", "doc4", "doc2", "doc5"]
        expected = ["doc1", "doc2", "doc3"]
        metrics = calculate_all_metrics(retrieved, expected, k_values=[1, 3, 5])

        assert "precision@1" in metrics
        assert "precision@3" in metrics
        assert "precision@5" in metrics
        assert "recall@1" in metrics
        assert "recall@3" in metrics
        assert "recall@5" in metrics
        assert "hit_rate@1" in metrics
        assert "hit_rate@3" in metrics
        assert "hit_rate@5" in metrics
        assert "f1@1" in metrics
        assert "f1@3" in metrics
        assert "f1@5" in metrics
        assert "mrr" in metrics
        assert "map" in metrics


class TestAggregateMetrics:
    """Tests for aggregate_metrics function."""

    def test_aggregates_multiple_results(self):
        """Aggregates metrics across multiple queries."""
        results = [
            {"precision@5": 1.0, "recall@5": 1.0, "hit_rate@5": 1.0, "f1@5": 1.0, "mrr": 1.0, "map": 1.0},
            {"precision@5": 0.0, "recall@5": 0.0, "hit_rate@5": 0.0, "f1@5": 0.0, "mrr": 0.0, "map": 0.0},
        ]
        aggregated = aggregate_metrics(results, k_values=[5])

        assert aggregated["precision@5"] == 0.5
        assert aggregated["recall@5"] == 0.5
        assert aggregated["hit_rate@5"] == 0.5
        assert aggregated["f1@5"] == 0.5
        assert aggregated["mrr"] == 0.5
        assert aggregated["map"] == 0.5

    def test_empty_results(self):
        """Returns empty dict for empty results."""
        assert aggregate_metrics([]) == {}


if __name__ == "__main__":
    pytest.main([__file__, "-v"])