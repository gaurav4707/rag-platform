"""Tests for chunking strategy abstraction."""
from backend.rag.indexing_config import IndexingConfig
from backend.rag.chunking import ChunkingMetrics, ChunkingResult


class TestIndexingConfig:
    def test_defaults(self):
        config = IndexingConfig()
        assert config.chunking_strategy == "fixed"
        assert config.chunking_scope == "page"
        assert config.adaptive_min_chunk_size == 200
        assert config.adaptive_max_chunk_size == 1500
        assert config.parent_chunk_size == 4000
        assert config.parent_chunk_overlap == 200
        assert config.child_chunk_size == 1000
        assert config.child_chunk_overlap == 200

    def test_custom_config(self):
        config = IndexingConfig(
            chunking_strategy="adaptive",
            chunking_scope="document",
            adaptive_min_chunk_size=300,
            adaptive_max_chunk_size=2000,
        )
        assert config.chunking_strategy == "adaptive"
        assert config.chunking_scope == "document"
        assert config.adaptive_min_chunk_size == 300
        assert config.adaptive_max_chunk_size == 2000

    def test_frozen(self):
        config = IndexingConfig()
        try:
            config.chunking_strategy = "adaptive"
            assert False, "Should be frozen"
        except AttributeError:
            pass


class TestChunkingMetrics:
    def test_defaults(self):
        metrics = ChunkingMetrics()
        assert metrics.chunk_count == 0
        assert metrics.average_chunk_size == 0.0
        assert metrics.boundary_hits == 0
        assert metrics.strategy == "fixed"
        assert metrics.duration_ms == 0.0
        assert metrics.fallback_used is False

    def test_custom_metrics(self):
        metrics = ChunkingMetrics(
            chunk_count=5,
            average_chunk_size=800.0,
            boundary_hits=3,
            strategy="adaptive",
            duration_ms=12.5,
            fallback_used=True,
        )
        assert metrics.chunk_count == 5
        assert metrics.fallback_used is True


class TestChunkingResult:
    def test_defaults(self):
        result = ChunkingResult(chunks=[])
        assert result.chunks == []
        assert result.success is True
        assert result.metrics.strategy == "fixed"

    def test_with_metrics(self):
        metrics = ChunkingMetrics(strategy="adaptive", chunk_count=3)
        result = ChunkingResult(chunks=[], success=True, metrics=metrics)
        assert result.metrics.strategy == "adaptive"
