from dataclasses import dataclass
from typing import Any, Literal


@dataclass(frozen=True)
class RetrievalConfig:
    top_k: int = 4
    search_type: Literal["similarity", "mmr"] = "similarity"
    score_threshold: float | None = None
    fetch_k: int = 20
    lambda_mult: float = 0.5
    metadata_filter: dict[str, Any] | None = None
    query_rewrite: Literal["none", "llm"] = "none"


DEFAULT_RETRIEVAL_CONFIG = RetrievalConfig()