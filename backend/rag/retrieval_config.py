"""Retrieval Configuration with Query Processing settings.

Clean configuration structure for the Retrieval Pipeline.
No legacy compatibility fields - direct migration to new structure.
"""

from dataclasses import dataclass, field
from typing import Any, Literal


@dataclass(frozen=True)
class QueryProcessingConfig:
    """Query processing configuration (rewrite + expand)."""

    # Query rewriting
    rewrite_enabled: bool = True
    rewrite_strategy: Literal["none", "llm"] = "none"

    # Query expansion (multi-query)
    expand_enabled: bool = False
    expand_strategy: Literal["none", "llm"] = "none"
    expand_count: int = 3


@dataclass(frozen=True)
class RetrievalConfig:
    """Main retrieval configuration."""

    # Core retrieval settings
    top_k: int = 4
    search_type: Literal["similarity", "mmr", "hybrid"] = "hybrid"
    score_threshold: float | None = None
    fetch_k: int = 20
    lambda_mult: float = 0.5
    metadata_filter: dict[str, Any] | None = None

    # Hybrid retrieval specific settings
    dense_top_k: int = 10
    bm25_top_k: int = 10
    final_top_k: int = 6
    rrf_k: int = 60
    hybrid_enabled: bool = True

    # Query processing (rewrite + expand)
    query_processing: QueryProcessingConfig = field(default_factory=QueryProcessingConfig)

    # Parent retrieval settings
    parent_retrieval_enabled: bool = True
    parent_target_size: int = 4000
    parent_overlap: int = 200

    # Reranking settings
    reranker: Literal["none", "cross_encoder"] = "cross_encoder"
    reranker_top_k: int = 6

    # Context compression settings
    compression_strategy: Literal["none", "extractive", "llm"] = "none"
    compression_scoring: Literal["keyword", "embedding"] = "keyword"
    compression_target_ratio: float = 0.5
    compression_max_tokens: int = 512

    # Backward compatibility properties
    @property
    def query_rewrite(self) -> str:
        """Legacy: maps to query_processing.rewrite_strategy."""
        return self.query_processing.rewrite_strategy

    @property
    def query_rewriting_enabled(self) -> bool:
        """Legacy: maps to query_processing.rewrite_enabled."""
        return self.query_processing.rewrite_enabled

    @property
    def multi_query_enabled(self) -> bool:
        """Legacy: maps to query_processing.expand_enabled."""
        return self.query_processing.expand_enabled

    @property
    def multi_query_count(self) -> int:
        """Legacy: maps to query_processing.expand_count."""
        return self.query_processing.expand_count

    @property
    def query_expansion_strategy(self) -> str:
        """Legacy: maps to query_processing.expand_strategy."""
        return self.query_processing.expand_strategy


DEFAULT_RETRIEVAL_CONFIG = RetrievalConfig()
