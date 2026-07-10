from dataclasses import dataclass, field
from typing import Any, Literal


@dataclass(frozen=True)
class RetrievalConfig:
    top_k: int = 4
    search_type: Literal["similarity", "mmr", "hybrid"] = "hybrid"
    score_threshold: float | None = None
    fetch_k: int = 20
    lambda_mult: float = 0.5
    metadata_filter: dict[str, Any] | None = None
    query_rewrite: Literal["none", "llm"] = "none"

    # Hybrid retrieval specific settings
    dense_top_k: int = 10
    bm25_top_k: int = 10
    final_top_k: int = 6
    rrf_k: int = 60
    hybrid_enabled: bool = True


DEFAULT_RETRIEVAL_CONFIG = RetrievalConfig()