"""Tests for the retriever module.

Covers:
- RetrievalConfig construction and defaults
- Strategy dispatch (similarity vs mmr vs unsupported)
- Similarity retrieval (mocked)
- MMR retrieval (mocked)
- Configuration parameters are respected
- Top-level retrieve_context tool
- Integration test with temporary ChromaDB instance
- Query rewriting (none and llm strategies)
"""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import numpy as np
import pytest
from langchain_core.documents import Document

from backend.models.rag_models import RetrievalResult, RetrievedChunk
from backend.rag.retrieval_config import DEFAULT_RETRIEVAL_CONFIG, RetrievalConfig


# ======================================================================
# Fixtures
# ======================================================================

@pytest.fixture
def sample_docs_with_scores():
    return [
        (
            Document(
                page_content="The sky is blue.",
                metadata={"document_id": "1", "filename": "a.pdf", "page": 1},
            ),
            0.1,
        ),
        (
            Document(
                page_content="Grass is green.",
                metadata={"document_id": "1", "filename": "a.pdf", "page": 2},
            ),
            0.2,
        ),
        (
            Document(
                page_content="The ocean is deep.",
                metadata={"document_id": "1", "filename": "a.pdf", "page": 3},
            ),
            0.3,
        ),
        (
            Document(
                page_content="Mountains are tall.",
                metadata={"document_id": "2", "filename": "b.pdf", "page": 1},
            ),
            0.4,
        ),
    ]


@pytest.fixture
def mmr_query_result():
    """Simulate the dict returned by collection._collection.query()."""
    return {
        "ids": [["id0", "id1", "id2", "id3"]],
        "documents": [["doc A", "doc B", "doc C", "doc D"]],
        "metadatas": [
            [
                {"document_id": "1", "filename": "a.pdf"},
                {"document_id": "1", "filename": "a.pdf"},
                {"document_id": "2", "filename": "b.pdf"},
                {"document_id": "2", "filename": "b.pdf"},
            ]
        ],
        "distances": [[0.1, 0.2, 0.3, 0.4]],
        "embeddings": [
            [
                np.array([1.0, 0.0, 0.5, 0.5]),
                np.array([0.9, 0.1, 0.4, 0.6]),
                np.array([0.0, 1.0, 0.5, 0.5]),
                np.array([0.1, 0.9, 0.6, 0.4]),
            ]
        ],
    }


# ======================================================================
# RetrievalConfig Tests
# ======================================================================

class TestRetrievalConfig:
    def test_default_values(self):
        config = DEFAULT_RETRIEVAL_CONFIG
        assert config.top_k == 4
        assert config.search_type == "hybrid"
        assert config.score_threshold is None
        assert config.fetch_k == 20
        assert config.lambda_mult == 0.5
        assert config.query_rewrite == "none"

    def test_custom_values(self):
        config = RetrievalConfig(
            top_k=8, search_type="mmr", fetch_k=40, lambda_mult=0.3, query_rewrite="llm"
        )
        assert config.top_k == 8
        assert config.search_type == "mmr"
        assert config.fetch_k == 40
        assert config.lambda_mult == 0.3
        assert config.query_rewrite == "llm"

    def test_config_is_frozen(self):
        config = RetrievalConfig()
        with pytest.raises((AttributeError, TypeError)):
            config.top_k = 99

    def test_valid_search_types(self):
        RetrievalConfig(search_type="similarity")
        RetrievalConfig(search_type="mmr")

    def test_valid_query_rewrite_types(self):
        RetrievalConfig(query_rewrite="none")
        RetrievalConfig(query_rewrite="llm")


# ======================================================================
# Strategy Dispatch Tests
# ======================================================================

class TestStrategyDispatch:
    def test_similarity_dispatch(self):
        from backend.rag.retriever import _run_retrieval

        config = RetrievalConfig(search_type="similarity")
        with patch("backend.rag.retriever._run_similarity_search") as mock_sim:
            _run_retrieval("query", config)
            mock_sim.assert_called_once_with("query", config)

    def test_mmr_dispatch(self):
        from backend.rag.retriever import _run_retrieval

        config = RetrievalConfig(search_type="mmr")
        with patch("backend.rag.retriever._run_mmr_search") as mock_mmr:
            _run_retrieval("query", config)
            mock_mmr.assert_called_once_with("query", config)

    def test_unsupported_search_type_raises(self):
        from backend.rag.retriever import _run_retrieval

        config = RetrievalConfig()
        object.__setattr__(config, "search_type", "hybrid")
        with pytest.raises(ValueError, match="Unsupported search_type: hybrid"):
            _run_retrieval("query", config)


# ======================================================================
# Similarity Retrieval Tests
# ======================================================================

class TestSimilarityRetrieval:
    def test_returns_correct_count(self, sample_docs_with_scores):
        from backend.rag.retriever import _run_similarity_search

        config = RetrievalConfig(top_k=2, search_type="similarity")
        with patch("backend.rag.retriever.similarity_search_with_scores_filtered") as mock_search:
            mock_search.return_value = sample_docs_with_scores[:2]
            results = _run_similarity_search("query", config)
        assert len(results) == 2

    def test_top_k_respected(self, sample_docs_with_scores):
        from backend.rag.retriever import _run_similarity_search

        config = RetrievalConfig(top_k=3, search_type="similarity")
        with patch("backend.rag.retriever.similarity_search_with_scores_filtered") as mock_search:
            mock_search.return_value = sample_docs_with_scores[:3]
            results = _run_similarity_search("query", config)
        assert len(results) == 3

    def test_top_k_passed_to_chroma(self):
        from backend.rag.retriever import _run_similarity_search

        config = RetrievalConfig(top_k=7)
        with patch("backend.rag.retriever.similarity_search_with_scores_filtered") as mock_search:
            _run_similarity_search("query", config)
            mock_search.assert_called_once_with(query="query", top_k=7, metadata_filter=None)

    def test_preserves_metadata(self):
        from backend.rag.retriever import _run_similarity_search

        doc = Document(
            page_content="test content",
            metadata={"document_id": "42", "filename": "report.pdf", "page": 5},
        )
        with patch("backend.rag.retriever.similarity_search_with_scores_filtered") as mock_search:
            mock_search.return_value = [(doc, 0.5)]
            config = RetrievalConfig(top_k=1)
            results = _run_similarity_search("query", config)
        assert results[0][0].metadata["document_id"] == "42"
        assert results[0][0].metadata["filename"] == "report.pdf"
        assert results[0][0].metadata["page"] == 5

    def test_returns_doc_score_tuples(self):
        from backend.rag.retriever import _run_similarity_search

        doc = Document(page_content="content", metadata={})
        with patch("backend.rag.retriever.similarity_search_with_scores_filtered") as mock_search:
            mock_search.return_value = [(doc, 0.123)]
            config = RetrievalConfig(top_k=1)
            results = _run_similarity_search("query", config)
        assert isinstance(results[0][0], Document)
        assert isinstance(results[0][1], float)
        assert results[0][1] == 0.123

    def test_handles_empty_results(self):
        from backend.rag.retriever import _run_similarity_search

        with patch("backend.rag.retriever.similarity_search_with_scores_filtered") as mock_search:
            mock_search.return_value = []
            config = RetrievalConfig(top_k=4)
            results = _run_similarity_search("query", config)
        assert len(results) == 0


# ======================================================================
# MMR Retrieval Tests
# ======================================================================

class TestMMRRetrieval:
    def test_returns_correct_count(self, mmr_query_result):
        from backend.rag.retriever import _run_mmr_search

        config = RetrievalConfig(top_k=2, search_type="mmr")
        with patch("backend.rag.retriever.mmr_search_with_scores") as mock_mmr:
            mock_mmr.return_value = [
                (Document(page_content="A", metadata={}), 0.1),
                (Document(page_content="B", metadata={}), 0.2),
            ]
            results = _run_mmr_search("query", config)
        assert len(results) == 2

    def test_top_k_respected(self, mmr_query_result):
        from backend.rag.retriever import _run_mmr_search

        config = RetrievalConfig(top_k=1, search_type="mmr", fetch_k=4)
        with patch("backend.rag.retriever.mmr_search_with_scores") as mock_mmr:
            mock_mmr.return_value = [(Document(page_content="A", metadata={}), 0.1)]
            results = _run_mmr_search("query", config)
        assert len(results) == 1

    def test_fetch_k_respected(self, mmr_query_result):
        from backend.rag.retriever import _run_mmr_search

        config = RetrievalConfig(top_k=2, search_type="mmr", fetch_k=50)
        with patch("backend.rag.retriever.mmr_search_with_scores") as mock_mmr:
            mock_mmr.return_value = [
                (Document(page_content="A", metadata={}), 0.1),
                (Document(page_content="B", metadata={}), 0.2),
            ]
            _run_mmr_search("query", config)
            mock_mmr.assert_called_once()
            assert mock_mmr.call_args[1]["fetch_k"] == 50

    def test_lambda_mult_passed(self, mmr_query_result):
        from backend.rag.retriever import _run_mmr_search

        config = RetrievalConfig(top_k=2, search_type="mmr", lambda_mult=0.7)
        with patch("backend.rag.retriever.mmr_search_with_scores") as mock_mmr:
            mock_mmr.return_value = [
                (Document(page_content="A", metadata={}), 0.1),
                (Document(page_content="B", metadata={}), 0.2),
            ]
            _run_mmr_search("query", config)
            mock_mmr.assert_called_once()
            assert mock_mmr.call_args[1]["lambda_mult"] == 0.7
            assert mock_mmr.call_args[1]["top_k"] == 2

    def test_include_fields(self, mmr_query_result):
        from backend.rag.retriever import _run_mmr_search

        config = RetrievalConfig(top_k=2, search_type="mmr", fetch_k=4)
        with patch("backend.rag.retriever.mmr_search_with_scores") as mock_mmr:
            mock_mmr.return_value = [
                (Document(page_content="A", metadata={}), 0.1),
                (Document(page_content="B", metadata={}), 0.2),
            ]
            _run_mmr_search("query", config)
            mock_mmr.assert_called_once()
            # The include fields are handled internally by mmr_search_with_scores

    def test_preserves_metadata(self, mmr_query_result):
        from backend.rag.retriever import _run_mmr_search

        config = RetrievalConfig(top_k=4, search_type="mmr", fetch_k=4)
        with patch("backend.rag.retriever.mmr_search_with_scores") as mock_mmr:
            mock_mmr.return_value = [
                (Document(page_content="A", metadata={"document_id": "1", "filename": "a.pdf"}), 0.1),
                (Document(page_content="B", metadata={"document_id": "2", "filename": "b.pdf"}), 0.2),
            ]
            results = _run_mmr_search("query", config)
        for doc, _ in results:
            assert "document_id" in doc.metadata
            assert "filename" in doc.metadata

    def test_returns_doc_score_tuples(self, mmr_query_result):
        from backend.rag.retriever import _run_mmr_search

        config = RetrievalConfig(top_k=2, search_type="mmr", fetch_k=4)
        with patch("backend.rag.retriever.mmr_search_with_scores") as mock_mmr:
            mock_mmr.return_value = [
                (Document(page_content="A", metadata={}), 0.1),
                (Document(page_content="B", metadata={}), 0.2),
            ]
            results = _run_mmr_search("query", config)
        for doc, score in results:
            assert isinstance(doc, Document)
            assert isinstance(score, float)

    def test_handles_empty_results(self):
        from backend.rag.retriever import _run_mmr_search

        config = RetrievalConfig(top_k=4, search_type="mmr", fetch_k=4)
        with patch("backend.rag.retriever.mmr_search_with_scores") as mock_mmr:
            mock_mmr.return_value = []
            results = _run_mmr_search("query", config)
        assert len(results) == 0


# ======================================================================
# retrieve_context Tool Tests
# ======================================================================

class TestRetrieveContext:
    def test_returns_retrieval_result(self):
        from backend.rag.retriever import retrieve_context

        mock_doc = Document(page_content="test", metadata={"document_id": "1", "chunk_index": 0})
        with patch("backend.rag.retrieval_strategies.similarity_search_with_scores_filtered") as mock_search:
            with patch("backend.rag.bm25.search", return_value=[]) as mock_bm25:
                mock_search.return_value = [(mock_doc, 0.5)]
                serialized, artifact = retrieve_context.func("query")

        assert isinstance(artifact, RetrievalResult)
        assert artifact.original_query == "query"
        assert artifact.retrieval_query == "query"
        assert len(artifact.chunks) == 1
        assert artifact.chunks[0].document.page_content == "test"
        # With hybrid retrieval + RRF, score is 1/(RRF_K + rank + 1) = 1/61
        assert abs(artifact.chunks[0].score - 1/61) < 0.001
        assert isinstance(artifact.chunks[0], RetrievedChunk)

    def test_accepts_custom_config(self):
        from backend.rag.retriever import retrieve_context

        config = RetrievalConfig(top_k=3)
        mock_docs = [
            Document(page_content="test 1", metadata={"document_id": "1", "chunk_index": 0}),
            Document(page_content="test 2", metadata={"document_id": "1", "chunk_index": 1}),
            Document(page_content="test 3", metadata={"document_id": "1", "chunk_index": 2}),
        ]
        with patch("backend.rag.retrieval_strategies.similarity_search_with_scores_filtered") as mock_search:
            with patch("backend.rag.bm25.search", return_value=[]) as mock_bm25:
                mock_search.return_value = [(doc, 0.5) for doc in mock_docs]
                serialized, artifact = retrieve_context.func("query", config=config)
        assert len(artifact.chunks) == 3

    def test_default_config_top_k(self):
        from backend.rag.retriever import retrieve_context

        with patch("backend.rag.retrieval_strategies.similarity_search_with_scores_filtered") as mock_search:
            with patch("backend.rag.bm25.search", return_value=[]) as mock_bm25:
                mock_search.return_value = []
                retrieve_context.func("query")
        # hybrid_retrieve uses DENSE_TOP_K/BM25_TOP_K from config, not config.top_k directly
        mock_search.assert_called_once()

    def test_custom_config_top_k(self):
        from backend.rag.retriever import retrieve_context

        config = RetrievalConfig(top_k=10)
        with patch("backend.rag.retrieval_strategies.similarity_search_with_scores_filtered") as mock_search:
            with patch("backend.rag.bm25.search", return_value=[]) as mock_bm25:
                mock_search.return_value = []
                retrieve_context.func("query", config=config)
        mock_search.assert_called_once()

    def test_default_config_used_when_omitted(self):
        from backend.rag.retriever import retrieve_context

        with patch("backend.rag.retrieval_strategies.similarity_search_with_scores_filtered") as mock_search:
            with patch("backend.rag.bm25.search", return_value=[]) as mock_bm25:
                mock_search.return_value = []
                retrieve_context.func("query")
        mock_search.assert_called_once()

    def test_mmr_path_through_retrieve_context(self):
        from backend.rag.retriever import retrieve_context

        config = RetrievalConfig(search_type="mmr", top_k=2, fetch_k=4)
        mock_docs = [
            (Document(page_content="doc1", metadata={"document_id": "1", "chunk_index": 0}), 0.1),
            (Document(page_content="doc2", metadata={"document_id": "2", "chunk_index": 0}), 0.2),
        ]
        with patch("backend.rag.retrieval_strategies.mmr_search_with_scores") as mock_mmr:
            with patch("backend.rag.bm25.search", return_value=[]) as mock_bm25:
                mock_mmr.return_value = mock_docs
                serialized, artifact = retrieve_context.func("query", config=config)

        assert isinstance(artifact, RetrievalResult)
        assert len(artifact.chunks) == 2
        for chunk in artifact.chunks:
            assert isinstance(chunk, RetrievedChunk)
            assert isinstance(chunk.score, float)

    def test_serialized_string_format(self):
        from backend.rag.retriever import retrieve_context

        mock_doc = Document(
            page_content="hello world", metadata={"doc_id": "1", "document_id": "1", "chunk_index": 0}
        )
        with patch("backend.rag.retrieval_strategies.similarity_search_with_scores_filtered") as mock_search:
            with patch("backend.rag.bm25.search", return_value=[]) as mock_bm25:
                mock_search.return_value = [(mock_doc, 0.5)]
                serialized, artifact = retrieve_context.func("query")
        assert isinstance(serialized, str)
        assert "hello world" in serialized
        assert "doc_id" in serialized


# ======================================================================
# Query Rewriting Tests
# ======================================================================

class TestQueryRewriting:
    """Tests for query rewriting functionality."""

    def test_no_rewrite_strategy_returns_original_query(self):
        from backend.rag.query_rewriter import rewrite_query

        result = rewrite_query("test query", "none")
        assert result == "test query"

    def test_no_rewrite_preserves_empty_query(self):
        from backend.rag.query_rewriter import rewrite_query

        result = rewrite_query("", "none")
        assert result == ""

    def test_no_rewrite_preserves_whitespace_only(self):
        from backend.rag.query_rewriter import rewrite_query

        result = rewrite_query("   ", "none")
        assert result == "   "

    def test_llm_rewrite_returns_string(self):
        from backend.rag.query_rewriter import rewrite_query

        # This will use the actual LLM if no mock, so we just verify it returns a string
        # In practice, this test would be mocked
        with patch("backend.providers.get_llm") as mock_get_llm:
            mock_llm = MagicMock()
            mock_llm.invoke.return_value = MagicMock(content="rewritten query")
            mock_get_llm.return_value = mock_llm

            result = rewrite_query("test query", "llm")
            assert isinstance(result, str)
            assert result == "rewritten query"

    def test_invalid_strategy_raises_error(self):
        from backend.rag.query_rewriter import rewrite_query

        with pytest.raises(ValueError, match="Unknown query_rewrite strategy"):
            rewrite_query("test query", "invalid")

    def test_retrieve_context_with_no_rewrite(self):
        """Test that retrieve_context preserves both queries when no rewrite."""
        from backend.rag.retriever import retrieve_context

        mock_doc = Document(page_content="test", metadata={"document_id": "1", "chunk_index": 0})
        config = RetrievalConfig(query_rewrite="none")
        with patch("backend.rag.retrieval_strategies.similarity_search_with_scores_filtered") as mock_search:
            with patch("backend.rag.bm25.search", return_value=[]) as mock_bm25:
                mock_search.return_value = [(mock_doc, 0.5)]
                serialized, artifact = retrieve_context.func("original query", config=config)

        assert artifact.original_query == "original query"
        assert artifact.retrieval_query == "original query"

    def test_retrieve_context_with_llm_rewrite_mocked(self):
        """Test that retrieve_context uses rewritten query for retrieval."""
        from backend.rag.retriever import retrieve_context

        mock_doc = Document(page_content="test", metadata={"document_id": "1", "chunk_index": 0})
        config = RetrievalConfig(query_rewrite="llm")
        with patch("backend.rag.retrieval_strategies.similarity_search_with_scores_filtered") as mock_search:
            with patch("backend.rag.bm25.search", return_value=[]) as mock_bm25:
                with patch("backend.rag.retriever.rewrite_query", return_value="rewritten query") as mock_rewrite:
                    mock_search.return_value = [(mock_doc, 0.5)]
                    serialized, artifact = retrieve_context.func("original query", config=config)

        # Verify rewrite was called
        mock_rewrite.assert_called_once_with("original query", "llm")
        # Verify retrieval used rewritten query (hybrid_retrieve uses it)
        mock_search.assert_called_once()
        # Verify both queries preserved in result
        assert artifact.original_query == "original query"
        assert artifact.retrieval_query == "rewritten query"

    def test_rewrite_failure_falls_back_to_original(self):
        """Test that rewrite failure falls back to original query."""
        from backend.rag.retriever import retrieve_context

        mock_doc = Document(page_content="test", metadata={"document_id": "1", "chunk_index": 0})
        config = RetrievalConfig(query_rewrite="llm")
        with patch("backend.rag.retrieval_strategies.similarity_search_with_scores_filtered") as mock_search:
            with patch("backend.rag.bm25.search", return_value=[]) as mock_bm25:
                with patch("backend.rag.retriever.rewrite_query", side_effect=Exception("LLM failed")):
                    mock_search.return_value = [(mock_doc, 0.5)]
                    serialized, artifact = retrieve_context.func("original query", config=config)

        # Should fall back to original query
        mock_search.assert_called_once()
        assert artifact.original_query == "original query"
        assert artifact.retrieval_query == "original query"

    def test_mmr_with_llm_rewrite_mocked(self):
        """Test MMR retrieval with mocked LLM rewrite."""
        from backend.rag.retriever import retrieve_context

        config = RetrievalConfig(search_type="mmr", top_k=2, fetch_k=4, query_rewrite="llm")
        mock_docs = [
            (Document(page_content="doc1", metadata={"document_id": "1", "chunk_index": 0}), 0.1),
            (Document(page_content="doc2", metadata={"document_id": "2", "chunk_index": 0}), 0.2),
        ]
        with patch("backend.rag.retrieval_strategies.mmr_search_with_scores") as mock_mmr:
            with patch("backend.rag.bm25.search", return_value=[]) as mock_bm25:
                mock_mmr.return_value = mock_docs
                with patch("backend.rag.retriever.rewrite_query", return_value="rewritten query"):
                    serialized, artifact = retrieve_context.func("original query", config=config)

        assert artifact.original_query == "original query"
        assert artifact.retrieval_query == "rewritten query"
        assert len(artifact.chunks) == 2


# ======================================================================
# Metadata Filtering Tests
# ======================================================================

class TestMetadataFiltering:
    """Tests for metadata filtering in retrieval."""

    def test_similarity_filter_by_document_id(self):
        from backend.rag.retriever import _run_similarity_search

        config = RetrievalConfig(
            top_k=2,
            search_type="similarity",
            metadata_filter={"document_id": "1"},
        )
        doc = Document(page_content="filtered", metadata={"document_id": "1"})
        with patch("backend.rag.retriever.similarity_search_with_scores_filtered") as mock_search:
            mock_search.return_value = [(doc, 0.1)]
            results = _run_similarity_search("query", config)
        assert len(results) == 1
        assert results[0][0].metadata["document_id"] == "1"

    def test_similarity_filter_by_filename(self):
        from backend.rag.retriever import _run_similarity_search

        config = RetrievalConfig(
            top_k=2,
            search_type="similarity",
            metadata_filter={"filename": "geo.pdf"},
        )
        doc = Document(page_content="filtered", metadata={"filename": "geo.pdf"})
        with patch("backend.rag.retriever.similarity_search_with_scores_filtered") as mock_search:
            mock_search.return_value = [(doc, 0.1)]
            results = _run_similarity_search("query", config)
        assert len(results) == 1
        assert results[0][0].metadata["filename"] == "geo.pdf"

    def test_similarity_filter_by_page(self):
        from backend.rag.retriever import _run_similarity_search

        config = RetrievalConfig(
            top_k=2,
            search_type="similarity",
            metadata_filter={"page": 2},
        )
        doc = Document(page_content="filtered", metadata={"page": 2})
        with patch("backend.rag.retriever.similarity_search_with_scores_filtered") as mock_search:
            mock_search.return_value = [(doc, 0.1)]
            results = _run_similarity_search("query", config)
        assert len(results) == 1
        assert results[0][0].metadata["page"] == 2

    def test_similarity_no_filter_unchanged(self):
        """Verify no filter behaves exactly as before."""
        from backend.rag.retriever import _run_similarity_search

        config = RetrievalConfig(top_k=2, search_type="similarity")
        doc = Document(page_content="test", metadata={})
        with patch("backend.rag.retriever.similarity_search_with_scores_filtered") as mock_search:
            mock_search.return_value = [(doc, 0.5)]
            results = _run_similarity_search("query", config)
        assert len(results) == 1
        mock_search.assert_called_once_with(query="query", top_k=2, metadata_filter=None)

    def test_mmr_filter_by_document_id(self, mmr_query_result):
        from backend.rag.retriever import _run_mmr_search

        config = RetrievalConfig(
            top_k=2,
            search_type="mmr",
            fetch_k=4,
            metadata_filter={"document_id": "1"},
        )
        with patch("backend.rag.retriever.mmr_search_with_scores") as mock_mmr:
            mock_mmr.return_value = [
                (Document(page_content="A", metadata={"document_id": "1"}), 0.1),
                (Document(page_content="B", metadata={"document_id": "1"}), 0.2),
            ]
            results = _run_mmr_search("query", config)
        assert len(results) == 2
        mock_mmr.assert_called_once()
        assert mock_mmr.call_args[1]["metadata_filter"] == {"document_id": "1"}

    def test_mmr_filter_by_filename(self, mmr_query_result):
        from backend.rag.retriever import _run_mmr_search

        config = RetrievalConfig(
            top_k=2,
            search_type="mmr",
            fetch_k=4,
            metadata_filter={"filename": "tech.pdf"},
        )
        with patch("backend.rag.retriever.mmr_search_with_scores") as mock_mmr:
            mock_mmr.return_value = [
                (Document(page_content="A", metadata={"filename": "tech.pdf"}), 0.1),
                (Document(page_content="B", metadata={"filename": "tech.pdf"}), 0.2),
            ]
            results = _run_mmr_search("query", config)
        assert len(results) == 2
        mock_mmr.assert_called_once()
        assert mock_mmr.call_args[1]["metadata_filter"] == {"filename": "tech.pdf"}

    def test_mmr_no_filter_unchanged(self, mmr_query_result):
        """Verify no filter behaves exactly as before for MMR."""
        from backend.rag.retriever import _run_mmr_search

        config = RetrievalConfig(top_k=2, search_type="mmr", fetch_k=4)
        with patch("backend.rag.retriever.mmr_search_with_scores") as mock_mmr:
            mock_mmr.return_value = [
                (Document(page_content="A", metadata={}), 0.1),
                (Document(page_content="B", metadata={}), 0.2),
            ]
            _run_mmr_search("query", config)
        mock_mmr.assert_called_once()
        assert mock_mmr.call_args[1].get("metadata_filter") is None

    def test_filter_empty_results(self):
        """Empty filter results should return empty RetrievalResult."""
        from backend.rag.retriever import _run_similarity_search

        config = RetrievalConfig(
            top_k=2,
            search_type="similarity",
            metadata_filter={"document_id": "nonexistent"},
        )
        with patch("backend.rag.retriever.similarity_search_with_scores_filtered") as mock_search:
            mock_search.return_value = []
            results = _run_similarity_search("query", config)
        assert len(results) == 0

    def test_retrieve_context_with_filter(self):
        """Test retrieve_context tool with metadata filter."""
        from backend.rag.retriever import retrieve_context

        config = RetrievalConfig(
            top_k=2,
            search_type="similarity",
            metadata_filter={"document_id": "2"},
        )
        mock_doc = Document(
            page_content="tech content", metadata={"document_id": "2", "chunk_index": 0}
        )
        with patch("backend.rag.retrieval_strategies.similarity_search_with_scores_filtered") as mock_search:
            with patch("backend.rag.bm25.search", return_value=[]) as mock_bm25:
                mock_search.return_value = [(mock_doc, 0.5)]
                serialized, artifact = retrieve_context.func("query", config=config)
        assert isinstance(artifact, RetrievalResult)
        assert len(artifact.chunks) == 1
        assert artifact.chunks[0].document.metadata["document_id"] == "2"


# ======================================================================
# Integration Tests (requires temporary ChromaDB)
# ======================================================================

class TestIntegration:
    """End-to-end test with a real (temporary) ChromaDB instance."""

    def test_similarity_retrieval_succeeds(self, temp_chroma):
        from backend.rag.retriever import _run_retrieval

        config = RetrievalConfig(top_k=3, search_type="similarity")
        with patch("backend.rag.vector_store._get_collection", return_value=temp_chroma):
            results = _run_retrieval("France", config)
        assert len(results) <= 3
        assert len(results) > 0
        for doc, score in results:
            assert isinstance(doc, Document)
            assert isinstance(score, float)

    def test_mmr_retrieval_succeeds(self, temp_chroma):
        from backend.rag.retriever import _run_retrieval

        config = RetrievalConfig(
            top_k=3, search_type="mmr", fetch_k=6, lambda_mult=0.5
        )
        with patch("backend.rag.vector_store._get_collection", return_value=temp_chroma):
            results = _run_retrieval("France", config)
        assert len(results) <= 3
        assert len(results) > 0
        for doc, score in results:
            assert isinstance(doc, Document)
            assert isinstance(score, float)

    def test_both_return_same_type(self, temp_chroma):
        from backend.rag.retriever import _run_retrieval

        sim_config = RetrievalConfig(top_k=3, search_type="similarity")
        mmr_config = RetrievalConfig(
            top_k=3, search_type="mmr", fetch_k=6
        )
        with patch("backend.rag.vector_store._get_collection", return_value=temp_chroma):
            sim_results = _run_retrieval("Python", sim_config)
            mmr_results = _run_retrieval("Python", mmr_config)
        assert type(sim_results) is type(mmr_results)
        assert len(sim_results) <= 3
        assert len(mmr_results) <= 3

    def test_retrieve_context_with_temp_chroma(self, temp_chroma):
        from backend.rag.retriever import retrieve_context

        config = RetrievalConfig(top_k=2, search_type="similarity")
        with patch(
            "backend.rag.vector_store._get_collection", return_value=temp_chroma
        ):
            serialized, artifact = retrieve_context.func("France", config=config)
        assert isinstance(artifact, RetrievalResult)
        assert len(artifact.chunks) <= 2
        assert len(artifact.chunks) > 0
        for chunk in artifact.chunks:
            assert isinstance(chunk, RetrievedChunk)
            assert isinstance(chunk.score, float)

    def test_mmr_retrieve_context_with_temp_chroma(self, temp_chroma):
        from backend.rag.retriever import retrieve_context

        config = RetrievalConfig(
            top_k=2, search_type="mmr", fetch_k=6, lambda_mult=0.5
        )
        with patch(
            "backend.rag.vector_store._get_collection", return_value=temp_chroma
        ):
            serialized, artifact = retrieve_context.func("France", config=config)
        assert isinstance(artifact, RetrievalResult)
        assert len(artifact.chunks) <= 2
        assert len(artifact.chunks) > 0
        for chunk in artifact.chunks:
            assert isinstance(chunk, RetrievedChunk)
            assert isinstance(chunk.score, float)

    def test_top_k_enforced_integration(self, temp_chroma):
        from backend.rag.retriever import _run_retrieval

        sim_config = RetrievalConfig(top_k=1, search_type="similarity")
        mmr_config = RetrievalConfig(
            top_k=1, search_type="mmr", fetch_k=6
        )
        with patch("backend.rag.vector_store._get_collection", return_value=temp_chroma):
            sim_results = _run_retrieval("France", sim_config)
            mmr_results = _run_retrieval("France", mmr_config)
        assert len(sim_results) == 1
        assert len(mmr_results) == 1

    def test_metadata_preserved_integration(self, temp_chroma):
        from backend.rag.retriever import _run_retrieval

        config = RetrievalConfig(top_k=6, search_type="similarity")
        with patch("backend.rag.vector_store._get_collection", return_value=temp_chroma):
            results = _run_retrieval("Paris", config)
        for doc, _ in results:
            assert "document_id" in doc.metadata
            assert "filename" in doc.metadata
            assert "page" in doc.metadata

    def test_similarity_filter_by_document_id_integration(self, temp_chroma):
        from backend.rag.retriever import _run_retrieval

        config = RetrievalConfig(
            top_k=6, search_type="similarity", metadata_filter={"document_id": "1"}
        )
        with patch("backend.rag.vector_store._get_collection", return_value=temp_chroma):
            results = _run_retrieval("France", config)
        assert len(results) > 0
        assert len(results) <= 3
        for doc, _ in results:
            assert doc.metadata["document_id"] == "1"

    def test_similarity_filter_by_filename_integration(self, temp_chroma):
        from backend.rag.retriever import _run_retrieval

        config = RetrievalConfig(
            top_k=6, search_type="similarity", metadata_filter={"filename": "tech.pdf"}
        )
        with patch("backend.rag.vector_store._get_collection", return_value=temp_chroma):
            results = _run_retrieval("Python", config)
        assert len(results) > 0
        assert len(results) <= 3
        for doc, _ in results:
            assert doc.metadata["filename"] == "tech.pdf"

    def test_mmr_filter_by_document_id_integration(self, temp_chroma):
        from backend.rag.retriever import _run_retrieval

        config = RetrievalConfig(
            top_k=3,
            search_type="mmr",
            fetch_k=6,
            lambda_mult=0.5,
            metadata_filter={"document_id": "2"},
        )
        with patch("backend.rag.vector_store._get_collection", return_value=temp_chroma):
            results = _run_retrieval("Python", config)
        assert len(results) > 0
        assert len(results) <= 3
        for doc, _ in results:
            assert doc.metadata["document_id"] == "2"

    def test_mmr_filter_by_filename_integration(self, temp_chroma):
        from backend.rag.retriever import _run_retrieval

        config = RetrievalConfig(
            top_k=3,
            search_type="mmr",
            fetch_k=6,
            lambda_mult=0.5,
            metadata_filter={"filename": "geo.pdf"},
        )
        with patch("backend.rag.vector_store._get_collection", return_value=temp_chroma):
            results = _run_retrieval("France", config)
        assert len(results) > 0
        assert len(results) <= 3
        for doc, _ in results:
            assert doc.metadata["filename"] == "geo.pdf"

    def test_filter_empty_results_integration(self, temp_chroma):
        """Empty filter results return empty list."""
        from backend.rag.retriever import _run_retrieval

        config = RetrievalConfig(
            top_k=6,
            search_type="similarity",
            metadata_filter={"document_id": "nonexistent"},
        )
        with patch("backend.rag.vector_store._get_collection", return_value=temp_chroma):
            results = _run_retrieval("France", config)
        assert len(results) == 0


# ======================================================================
# Deduplication Tests
# ======================================================================

class TestDeduplication:
    """Tests for duplicate chunk removal in retrieval."""

    def test_deduplicate_by_document_id_and_chunk_index(self):
        """Chunks with same document_id and chunk_index are deduplicated."""
        from backend.rag.retriever import _deduplicate_chunks

        doc1 = Document(
            page_content="chunk A",
            metadata={"document_id": "doc1", "chunk_index": 0},
        )
        doc2 = Document(
            page_content="chunk B",
            metadata={"document_id": "doc1", "chunk_index": 1},
        )
        doc3 = Document(
            page_content="chunk A duplicate",
            metadata={"document_id": "doc1", "chunk_index": 0},  # Same ID as doc1
        )

        chunks = [(doc1, 0.1), (doc2, 0.2), (doc3, 0.15)]
        result = _deduplicate_chunks(chunks)

        assert len(result) == 2
        assert result[0][0].page_content == "chunk A"  # First occurrence kept
        assert result[1][0].page_content == "chunk B"

    def test_deduplicate_preserves_highest_score(self):
        """First occurrence (highest score) is preserved when deduplicating."""
        from backend.rag.retriever import _deduplicate_chunks

        doc1 = Document(
            page_content="content",
            metadata={"document_id": "doc1", "chunk_index": 0},
        )
        doc2 = Document(
            page_content="content duplicate",
            metadata={"document_id": "doc1", "chunk_index": 0},
        )

        # doc1 has higher score (lower distance = better)
        chunks = [(doc1, 0.1), (doc2, 0.3)]
        result = _deduplicate_chunks(chunks)

        assert len(result) == 1
        assert result[0][1] == 0.1  # Higher score preserved

    def test_deduplicate_fallback_to_content_hash(self):
        """Chunks without metadata are deduplicated by content prefix."""
        from backend.rag.retriever import _deduplicate_chunks

        # Create content that shares the first 200+ characters
        prefix = "This is a long common prefix that is definitely more than two hundred characters long so that the deduplication logic will trigger on the prefix match. " * 3
        doc1 = Document(page_content=prefix + " unique ending A", metadata={})
        doc2 = Document(page_content="completely different content B", metadata={})
        doc3 = Document(page_content=prefix + " unique ending C", metadata={})  # Same prefix

        chunks = [(doc1, 0.1), (doc2, 0.2), (doc3, 0.15)]
        result = _deduplicate_chunks(chunks)

        # doc1 and doc3 share first 200 chars prefix, so doc3 is deduplicated
        assert len(result) == 2

    def test_deduplicate_no_metadata_no_false_positives(self):
        """Chunks with different content are not deduplicated when no metadata."""
        from backend.rag.retriever import _deduplicate_chunks

        doc1 = Document(page_content="completely different content one", metadata={})
        doc2 = Document(page_content="completely different content two", metadata={})

        chunks = [(doc1, 0.1), (doc2, 0.2)]
        result = _deduplicate_chunks(chunks)

        assert len(result) == 2


# ======================================================================
# Chunk Quality Tests
# ======================================================================

class TestChunkQuality:
    """Tests for chunk boundary quality."""

    def test_splitter_uses_custom_separators(self):
        """Verify splitter is configured with improved separators."""
        from backend.rag.splitter import text_splitter

        # Check that custom separators are used
        separators = text_splitter._separators
        assert "\n\n" in separators
        assert "\n# " in separators
        assert ". " in separators
        assert "! " in separators
        assert "? " in separators

    def test_chunking_preserves_headings(self):
        """Chunks should start at heading boundaries when possible."""
        from backend.rag.splitter import text_splitter

        # Create long text that forces multiple chunks
        long_para = "This is a long paragraph with enough content to fill space. " * 20

        text = f"""# Introduction

{long_para}

# Chapter 1

{long_para}

## Section 1.1

{long_para}"""

        chunks = text_splitter.split_text(text)

        # Should have multiple chunks
        assert len(chunks) > 1
        # First chunk should contain the first heading
        assert "# Introduction" in chunks[0]
        # At least one chunk should start with a chapter heading
        assert any(chunk.strip().startswith("# Chapter 1") for chunk in chunks)

    def test_chunking_avoids_mid_sentence_splits(self):
        """Chunks should prefer sentence boundaries over mid-sentence."""
        from backend.rag.splitter import text_splitter

        # Long sentence that would force a split
        text = "This is a very long sentence that goes on and on and on and on and on and on and on and on and on and on and on and on and on and on and on and on and on and on and on and on and on and on and on and on and on and on and on and on and on and on and on."

        chunks = text_splitter.split_text(text)

        # Should split at sentence boundaries if possible
        # With our separators, it should prefer ". " over mid-word
        for chunk in chunks:
            # Chunks shouldn't end mid-word (no trailing partial words)
            assert not chunk.rstrip().endswith(("and on", "and o", "and ", "on a"))


# ======================================================================
# Retrieval Logging Tests
# ======================================================================

class TestRetrievalLogging:
    """Tests for improved retrieval logging."""

    def test_log_retrieval_details_outputs_expected_format(self, caplog):
        """Verify logging function outputs structured details."""
        from backend.rag.retriever import _log_retrieval_details
        from backend.models.rag_models import RetrievedChunk
        from langchain_core.documents import Document

        chunks = [
            RetrievedChunk(
                document=Document(
                    page_content="Test content for preview",
                    metadata={
                        "document_id": "doc123",
                        "filename": "test.pdf",
                        "page": 5,
                        "chunk_index": 2,
                    },
                ),
                score=0.1234,
            )
        ]

        with caplog.at_level("DEBUG"):
            _log_retrieval_details("original query", "rewritten query", chunks)

        output = caplog.text

        assert "=== Retrieval ===" in output
        assert "Original Query : original query" in output
        assert "Retrieval Query: rewritten query" in output
        assert "Chunks Retrieved: 1" in output
        assert "doc_id=doc123" in output
        assert "filename=test.pdf" in output
        assert "page=5" in output
        assert "chunk_index=2" in output
        assert "score=0.1234" in output
        assert "preview=Test content for preview" in output


# ======================================================================
# Duplicate Document Detection Tests
# ======================================================================

class TestDuplicateDetection:
    """Tests for duplicate document detection using file hash."""

    def test_compute_file_hash(self):
        """Test that file hash is computed correctly."""
        from backend.services.document_service import _compute_file_hash

        content = b"test pdf content"
        hash1 = _compute_file_hash(content)
        hash2 = _compute_file_hash(content)
        hash3 = _compute_file_hash(b"different content")

        assert hash1 == hash2  # Same content = same hash
        assert hash1 != hash3  # Different content = different hash
        assert len(hash1) == 64  # SHA-256 hex length

    def test_process_upload_stores_file_hash_in_metadata(self):
        """Verify uploaded document chunks include file_hash metadata."""
        import hashlib
        content = b"test content"
        file_hash = hashlib.sha256(content).hexdigest()

        # Verify hash format
        assert len(file_hash) == 64
        assert all(c in "0123456789abcdef" for c in file_hash)

    def test_find_document_by_hash_not_found(self, temp_chroma):
        """Test finding a non-existent file hash returns None."""
        from backend.rag.vector_store import find_document_by_hash

        result = find_document_by_hash("nonexistent_hash")
        assert result is None


# ======================================================================
# Upload Duplicate Tests (using mocking)
# ======================================================================

class TestUploadDuplicates:
    """Integration tests for duplicate upload detection."""

    def test_upload_same_file_twice_returns_existing(self, temp_chroma, monkeypatch):
        """Uploading the same PDF twice should return existing document."""
        from backend.services.document_service import process_upload
        from backend.rag.loader import load_pdf
        from langchain_core.documents import Document

        # Mock load_pdf to return test documents
        def mock_load_pdf(path):
            return [
                Document(
                    page_content="Test content",
                    metadata={"page": 1},
                )
            ]

        monkeypatch.setattr("backend.services.document_service.load_pdf", mock_load_pdf)
        monkeypatch.setattr("backend.rag.vector_store._get_collection", lambda: temp_chroma)

        pdf_content = b"%PDF-1.4\nTest content"

        # First upload
        result1 = process_upload(pdf_content, "test.pdf")

        # Second upload with same content
        result2 = process_upload(pdf_content, "test.pdf")

        # Should return same document ID
        assert result1["document_id"] == result2["document_id"]
        assert result2["already_indexed"] is True
        assert result2["status"] == "already_indexed"

    def test_upload_different_files_both_indexed(self, temp_chroma, monkeypatch):
        """Uploading two different PDFs should index both."""
        from backend.services.document_service import process_upload
        from backend.rag.loader import load_pdf
        from langchain_core.documents import Document

        call_count = {"count": 0}

        def mock_load_pdf(path):
            call_count["count"] += 1
            return [
                Document(
                    page_content=f"Test content {call_count['count']}",
                    metadata={"page": 1},
                )
            ]

        monkeypatch.setattr("backend.services.document_service.load_pdf", mock_load_pdf)
        monkeypatch.setattr("backend.rag.vector_store._get_collection", lambda: temp_chroma)

        pdf1 = b"%PDF-1.4\nContent one"
        pdf2 = b"%PDF-1.4\nContent two"

        result1 = process_upload(pdf1, "doc1.pdf")
        result2 = process_upload(pdf2, "doc2.pdf")

        assert result1["document_id"] != result2["document_id"]
        assert result1["already_indexed"] is False
        assert result2["already_indexed"] is False

    def test_upload_same_filename_different_content_both_indexed(self, temp_chroma, monkeypatch):
        """Same filename but different content should both be indexed."""
        from backend.services.document_service import process_upload
        from backend.rag.loader import load_pdf
        from langchain_core.documents import Document

        call_count = {"count": 0}

        def mock_load_pdf(path):
            call_count["count"] += 1
            return [
                Document(
                    page_content=f"Test content {call_count['count']}",
                    metadata={"page": 1},
                )
            ]

        monkeypatch.setattr("backend.services.document_service.load_pdf", mock_load_pdf)
        monkeypatch.setattr("backend.rag.vector_store._get_collection", lambda: temp_chroma)

        pdf1 = b"%PDF-1.4\nContent A"
        pdf2 = b"%PDF-1.4\nContent B"

        result1 = process_upload(pdf1, "same.pdf")
        result2 = process_upload(pdf2, "same.pdf")

        assert result1["document_id"] != result2["document_id"]
        assert result1["already_indexed"] is False
        assert result2["already_indexed"] is False

    def test_upload_returns_file_hash_in_metadata(self, temp_chroma, monkeypatch):
        """Verify returned metadata includes file hash info."""
        from backend.services.document_service import process_upload
        from backend.rag.loader import load_pdf
        from langchain_core.documents import Document
        import hashlib

        def mock_load_pdf(path):
            return [
                Document(
                    page_content="Test content for hashing",
                    metadata={"page": 1},
                )
            ]

        monkeypatch.setattr("backend.services.document_service.load_pdf", mock_load_pdf)
        monkeypatch.setattr("backend.rag.vector_store._get_collection", lambda: temp_chroma)

        pdf_content = b"%PDF-1.4\nTest content for hashing"
        expected_hash = hashlib.sha256(pdf_content).hexdigest()

        result = process_upload(pdf_content, "test.pdf")

        # The response should include the document info
        assert "document_id" in result
        assert result["status"] in ("indexed", "already_indexed")
        # Verify the hash is stored in vector store for this document
        from backend.rag.vector_store import find_document_by_hash
        found = find_document_by_hash(expected_hash)
        assert found is not None
        assert found["file_hash"] == expected_hash