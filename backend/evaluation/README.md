# Offline Retrieval Evaluation

This module provides an **offline evaluation framework** for measuring retrieval quality in the Agentic RAG system.

## Purpose

The evaluation framework is a **development tool only** — it is completely separate from the production runtime. It allows developers to:

- Measure retrieval quality before/after changes
- Compare retrieval configurations (chunking, query rewriting, hybrid retrieval, reranking)
- Track regression in retrieval performance
- Evaluate without running the full API server

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                    PRODUCTION RUNTIME                           │
│  Frontend → API → Services → Agent → Retriever → Vector Store  │
└─────────────────────────────────────────────────────────────────┘
                            ↑
                            │ REUSES (does not import from)
                            │
┌─────────────────────────────────────────────────────────────────┐
│                   OFFLINE EVALUATION                            │
│  Developer → CLI → Evaluator → Retriever → Vector Store        │
│                        ↓                                        │
│                  Metrics Report                                 │
└─────────────────────────────────────────────────────────────────┘
```

**Critical Constraint**: Production code must NEVER import evaluation code. The evaluation framework imports from production (`rag.retriever`, `rag.retrieval_config`, `models.rag_models`), but the reverse is forbidden.

## Components

| File | Responsibility |
|------|----------------|
| `models.py` | Data models: `EvaluationQuery`, `RetrievalEvaluationResult`, `EvaluationReport` |
| `dataset.py` | Load/save JSON evaluation datasets |
| `metrics.py` | Retrieval metrics: Precision@K, Recall@K, Hit Rate, MRR, NDCG, MAP, F1 |
| `evaluator.py` | Orchestration: load dataset → run retriever → calculate metrics → generate report |
| `cli.py` | Command-line interface |
| `reports/` | Output directory for JSON reports |

## Dataset Format

JSON array of query objects:

```json
[
  {
    "id": "q1",
    "question": "What is RAG?",
    "expected_document_ids": ["rag-paper.pdf"],
    "expected_pages": [1, 2],
    "metadata": {
      "category": "definition",
      "difficulty": "easy"
    }
  }
]
```

## Usage

### Run Evaluation

```bash
# Basic usage
python -m backend.evaluation.cli \
    --dataset backend/evaluation/data/test_queries.json

# Custom retrieval config
python -m backend.evaluation.cli \
    --dataset backend/evaluation/data/test_queries.json \
    --top-k 5 \
    --search-type hybrid \
    --reranker cross_encoder

# Verbose output
python -m backend.evaluation.cli \
    --dataset backend/evaluation/data/test_queries.json \
    -v
```

### CLI Options

| Option | Description | Default |
|--------|-------------|---------|
| `--dataset`, `-d` | Path to JSON dataset file | Required |
| `--top-k`, `-k` | Number of top results to evaluate | 5 |
| `--search-type` | Retrieval strategy: `similarity`, `mmr`, `hybrid` | `hybrid` |
| `--score-threshold` | Minimum similarity score | None |
| `--fetch-k` | Documents to fetch for MMR | 20 |
| `--lambda-mult` | MMR diversity parameter (0-1) | 0.5 |
| `--reranker` | Reranker: `none`, `cross_encoder` | `cross_encoder` |
| `--reranker-top-k` | Final top-K after reranking | 6 |
| `--output-dir`, `-o` | Report output directory | `backend/evaluation/reports` |
| `--no-save` | Skip saving report to file | False |
| `--verbose`, `-v` | Enable debug logging | False |

## Metrics

| Metric | Description |
|--------|-------------|
| `precision@k` | Of top K retrieved docs, how many are relevant? |
| `recall@k` | Of all relevant docs, how many found in top K? |
| `hit_rate@k` | 1 if at least one relevant doc in top K, else 0 |
| `f1@k` | Harmonic mean of precision and recall at K |
| `mrr` | Mean Reciprocal Rank — where is first relevant doc? |
| `ndcg@k` | Normalized Discounted Cumulative Gain — ranking quality |
| `map` | Mean Average Precision — average precision across queries |

## Output

### Console Summary

```
============================================================
RETRIEVAL EVALUATION RESULTS
============================================================

Dataset: 5 queries evaluated
Top-K: 5
Search Type: hybrid
Reranker: cross_encoder

------------------------------------------------------------
AGGREGATED METRICS
------------------------------------------------------------
  Precision@5:     0.7200
  Recall@5:        0.8100
  Hit Rate@5:      0.9000
  F1@5:            0.7627
  MRR@5:           0.7600
  NDCG@5:          0.8500
  MAP:             0.6800

------------------------------------------------------------
PER-QUERY RESULTS
------------------------------------------------------------

  Query: q1 - What is Retrieval-Augmented Generation...
    Retrieved: 5 chunks
    P@5: 0.8000 | R@5: 1.0000 | HR@5: 1.0000
```

### JSON Report

Saved to `backend/evaluation/reports/evaluation_<timestamp>.json`:

```json
{
  "timestamp": "2024-01-15T10:30:00",
  "total_queries": 5,
  "top_k": 5,
  "metrics": {
    "precision@5": 0.72,
    "recall@5": 0.81,
    "hit_rate@5": 0.90,
    "f1@5": 0.76,
    "mrr": 0.76,
    "map": 0.68
  },
  "results": [
    {
      "query_id": "q1",
      "question": "What is RAG?",
      "retrieved_documents": [
        {"document_id": "rag-paper.pdf", "filename": "rag-paper.pdf", "page": 1, "chunk_index": 0, "score": 0.92}
      ],
      "retrieved_pages": [1, 2],
      "retrieved_chunks": ["RAG combines retrieval with generation..."],
      "metrics": {
        "precision@5": 0.8,
        "recall@5": 1.0,
        "hit_rate@5": 1.0,
        "mrr": 1.0
      }
    }
  ],
  "retrieval_config": {
    "top_k": 5,
    "search_type": "hybrid",
    "reranker": "cross_encoder"
  }
}
```

## Adding Test Queries

Create a JSON file in `backend/evaluation/data/` following the dataset format, then run evaluation against it.

## Running Tests

```bash
# Run metric unit tests (offline, no dependencies)
pytest backend/tests/test_evaluation_metrics.py -v
```

## Integration with Retrieval Improvements

Use this framework to measure impact of:

1. **Chunking changes** — Compare before/after precision/recall
2. **Query rewriting** — Enable/disable and measure MRR change
3. **Hybrid retrieval** — Compare `similarity` vs `hybrid` search types
4. **Reranking** — Compare with `reranker=none` vs `cross_encoder`
5. **Retrieval config** — Test different `top_k`, `fetch_k`, `lambda_mult` values