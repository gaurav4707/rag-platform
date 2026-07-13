"""Command-line interface for offline retrieval evaluation.

Usage:
    python -m backend.evaluation.cli --dataset path/to/queries.json --top-k 5
"""

import argparse
import logging
import sys
from pathlib import Path

from backend.evaluation.evaluator import run_evaluation, save_report
from backend.rag.retrieval_config import RetrievalConfig

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


def parse_args() -> argparse.Namespace:
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(
        description="Offline Retrieval Evaluation for Agentic RAG",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )

    parser.add_argument(
        "--dataset",
        "-d",
        type=str,
        required=True,
        help="Path to evaluation dataset JSON file",
    )

    parser.add_argument(
        "--top-k",
        "-k",
        type=int,
        default=5,
        help="Number of top results to evaluate (K for @K metrics)",
    )

    parser.add_argument(
        "--search-type",
        type=str,
        choices=["similarity", "mmr", "hybrid"],
        default="hybrid",
        help="Retrieval search type",
    )

    parser.add_argument(
        "--score-threshold",
        type=float,
        default=None,
        help="Minimum similarity score threshold",
    )

    parser.add_argument(
        "--fetch-k",
        type=int,
        default=20,
        help="Number of documents to fetch for MMR",
    )

    parser.add_argument(
        "--lambda-mult",
        type=float,
        default=0.5,
        help="Diversity parameter for MMR (0-1)",
    )

    parser.add_argument(
        "--reranker",
        type=str,
        choices=["none", "cross_encoder"],
        default="cross_encoder",
        help="Reranker to use",
    )

    parser.add_argument(
        "--reranker-top-k",
        type=int,
        default=6,
        help="Final top-k after reranking",
    )

    parser.add_argument(
        "--output-dir",
        "-o",
        type=str,
        default="backend/evaluation/reports",
        help="Output directory for evaluation reports",
    )

    parser.add_argument(
        "--no-save",
        action="store_true",
        help="Don't save report to file",
    )

    parser.add_argument(
        "--verbose",
        "-v",
        action="store_true",
        help="Enable verbose logging",
    )

    return parser.parse_args()


def build_retrieval_config(args: argparse.Namespace) -> RetrievalConfig:
    """Build RetrievalConfig from CLI arguments."""
    return RetrievalConfig(
        top_k=args.top_k,
        search_type=args.search_type,
        score_threshold=args.score_threshold,
        fetch_k=args.fetch_k,
        lambda_mult=args.lambda_mult,
        reranker=args.reranker,
        reranker_top_k=args.reranker_top_k,
    )


def print_summary(report) -> None:
    """Print evaluation summary to console."""
    print("\n" + "=" * 60)
    print("RETRIEVAL EVALUATION RESULTS")
    print("=" * 60)

    print(f"\nDataset: {report.retrieval_config.get('top_k', 'N/A')} queries evaluated")
    print(f"Top-K: {report.top_k}")
    print(f"Search Type: {report.retrieval_config.get('search_type', 'N/A')}")
    print(f"Reranker: {report.retrieval_config.get('reranker', 'N/A')}")

    print("\n" + "-" * 60)
    print("AGGREGATED METRICS")
    print("-" * 60)

    k = report.top_k
    metrics = report.metrics

    print(f"  Precision@{k}:     {metrics.get(f'precision@{k}', 0):.4f}")
    print(f"  Recall@{k}:        {metrics.get(f'recall@{k}', 0):.4f}")
    print(f"  Hit Rate@{k}:      {metrics.get(f'hit_rate@{k}', 0):.4f}")
    print(f"  F1@{k}:            {metrics.get(f'f1@{k}', 0):.4f}")
    print(f"  MRR@{k}:           {metrics.get(f'mrr@{k}', 0):.4f}")
    print(f"  NDCG@{k}:          {metrics.get(f'ndcg@{k}', 0):.4f}")
    print(f"  MAP:               {metrics.get('map', 0):.4f}")

    print("\n" + "-" * 60)
    print("PER-QUERY RESULTS")
    print("-" * 60)

    for result in report.results:
        print(f"\n  Query: {result.query_id} - {result.question[:60]}...")
        print(f"    Retrieved: {len(result.retrieved_documents)} chunks")
        print(
            f"    P@{k}: {result.metrics.get(f'precision@{k}', 0):.4f} | "
            f"R@{k}: {result.metrics.get(f'recall@{k}', 0):.4f} | "
            f"HR@{k}: {result.metrics.get(f'hit_rate@{k}', 0):.4f}"
        )


def main() -> int:
    """Main CLI entry point."""
    args = parse_args()

    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    # Validate dataset path
    dataset_path = Path(args.dataset)
    if not dataset_path.exists():
        logger.error("Dataset file not found: %s", args.dataset)
        return 1

    # Build retrieval config
    config = build_retrieval_config(args)

    logger.info("Starting evaluation with config: %s", config)

    try:
        # Run evaluation
        report = run_evaluation(
            dataset_path=str(dataset_path),
            config=config,
            top_k=args.top_k,
        )

        # Print summary
        print_summary(report)

        # Save report
        if not args.no_save:
            filepath = save_report(report, args.output_dir)
            print(f"\nReport saved to: {filepath}")

        return 0

    except Exception as e:
        logger.error("Evaluation failed: %s", e, exc_info=args.verbose)
        return 1


if __name__ == "__main__":
    sys.exit(main())