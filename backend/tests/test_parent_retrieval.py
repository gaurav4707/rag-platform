"""Tests for Parent Document Retrieval.

Covers:
- ParentStore (BaseParentStore + FileParentStore)
- resolve_parents() child-to-parent mapping
- Duplicate parent merging
- Score preservation
- Parent metadata
- Page provenance
- Fallback when parent missing
- Parent retrieval disabled
- Reranker receives parent contexts
- HierarchicalSplitter
- ParentRetrievalStage
"""

from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from langchain_core.documents import Document

from backend.models.rag_models import RetrievedChunk
from backend.rag.parent_retrieval import get_parent_retrieval_metadata, resolve_parents
from backend.rag.retrieval_config import RetrievalConfig, QueryProcessingConfig
from backend.rag.retrieval_pipeline import (
    MergeStage,
    ParentRetrievalStage,
    PipelineContext,
    RetrievalPipeline,
    RetrievalStage,
    RerankStage,
    ResultBuilderStage,
    RewriteStage,
    create_pipeline_from_config,
)
from backend.rag.splitter import HierarchicalSplitResult, HierarchicalSplitter
from backend.storage.parent_store import BaseParentStore, FileParentStore, ParentBlock

# ======================================================================
# Fixtures
# ======================================================================


@pytest.fixture
def parent_store(tmp_path) -> FileParentStore:
    return FileParentStore(tmp_path / "parents")


@pytest.fixture
def sample_parent_blocks():
    return [
        ParentBlock(
            parent_id="doc1_parent_0",
            content="Large parent block one with substantial content for context.",
            start_page=1,
            end_page=2,
            child_indices=[0, 1],
            metadata={"document_id": "doc1", "filename": "test.pdf"},
        ),
        ParentBlock(
            parent_id="doc1_parent_1",
            content="Large parent block two with more substantial content.",
            start_page=3,
            end_page=4,
            child_indices=[2, 3],
            metadata={"document_id": "doc1", "filename": "test.pdf"},
        ),
    ]


@pytest.fixture
def child_chunks():
    return [
        RetrievedChunk(
            document=Document(
                page_content="First child chunk content.",
                metadata={
                    "document_id": "doc1",
                    "filename": "test.pdf",
                    "chunk_index": 0,
                    "parent_id": "doc1_parent_0",
                    "parent_page_range_start": 1,
                    "parent_page_range_end": 2,
                    "parent_child_index": 0,
                },
            ),
            score=0.9,
        ),
        RetrievedChunk(
            document=Document(
                page_content="Second child chunk content.",
                metadata={
                    "document_id": "doc1",
                    "filename": "test.pdf",
                    "chunk_index": 1,
                    "parent_id": "doc1_parent_0",
                    "parent_page_range_start": 1,
                    "parent_page_range_end": 2,
                    "parent_child_index": 1,
                },
            ),
            score=0.7,
        ),
        RetrievedChunk(
            document=Document(
                page_content="Third child chunk content.",
                metadata={
                    "document_id": "doc1",
                    "filename": "test.pdf",
                    "chunk_index": 2,
                    "parent_id": "doc1_parent_1",
                    "parent_page_range_start": 3,
                    "parent_page_range_end": 4,
                    "parent_child_index": 2,
                },
            ),
            score=0.5,
        ),
    ]


@pytest.fixture
def child_chunks_no_parent_ref():
    return [
        RetrievedChunk(
            document=Document(
                page_content="A chunk without parent reference.",
                metadata={
                    "document_id": "doc2",
                    "filename": "legacy.pdf",
                    "chunk_index": 0,
                },
            ),
            score=0.8,
        ),
    ]


def _make_chunk(text: str, doc_id: str = "1", chunk_index: int = 0, score: float = 0.5, parent_ref: dict | None = None) -> RetrievedChunk:
    meta = {"document_id": doc_id, "chunk_index": chunk_index, "filename": "test.pdf"}
    if parent_ref:
        meta["parent_id"] = parent_ref.get("parent_id")
        pr = parent_ref.get("page_range", [None, None])
        meta["parent_page_range_start"] = pr[0]
        meta["parent_page_range_end"] = pr[1]
        meta["parent_child_index"] = (parent_ref.get("child_indices") or [0])[0]
    return RetrievedChunk(
        document=Document(page_content=text, metadata=meta),
        score=score,
    )


def _default_config(**kwargs) -> RetrievalConfig:
    qp_kwargs = {k: v for k, v in kwargs.items() if k.startswith("qp_")}
    other_kwargs = {k: v for k, v in kwargs.items() if not k.startswith("qp_")}
    qp = QueryProcessingConfig(**{k[3:]: v for k, v in qp_kwargs.items()})
    return RetrievalConfig(query_processing=qp, **other_kwargs)


# ======================================================================
# ParentStore Tests
# ======================================================================


class TestBaseParentStore:
    def test_abstract_methods(self):
        """BaseParentStore cannot be instantiated."""
        with pytest.raises(TypeError):
            BaseParentStore()  # type: ignore[abstract]


class TestFileParentStore:
    def test_store_and_load(self, parent_store, sample_parent_blocks):
        parent_store.store_parents("doc1", sample_parent_blocks)
        loaded = parent_store.load_parents("doc1")
        assert len(loaded) == 2
        assert loaded[0].parent_id == "doc1_parent_0"
        assert loaded[0].content == sample_parent_blocks[0].content
        assert loaded[0].start_page == 1
        assert loaded[0].end_page == 2

    def test_load_parent(self, parent_store, sample_parent_blocks):
        parent_store.store_parents("doc1", sample_parent_blocks)
        block = parent_store.load_parent("doc1", "doc1_parent_0")
        assert block is not None
        assert block.parent_id == "doc1_parent_0"

    def test_load_parent_not_found(self, parent_store):
        block = parent_store.load_parent("doc1", "nonexistent")
        assert block is None

    def test_parent_exists(self, parent_store, sample_parent_blocks):
        parent_store.store_parents("doc1", sample_parent_blocks)
        assert parent_store.parent_exists("doc1") is True
        assert parent_store.parent_exists("nonexistent") is False

    def test_delete_parents(self, parent_store, sample_parent_blocks):
        parent_store.store_parents("doc1", sample_parent_blocks)
        parent_store.delete_parents("doc1")
        assert parent_store.parent_exists("doc1") is False
        assert parent_store.load_parents("doc1") == []

    def test_load_empty_document(self, parent_store):
        assert parent_store.load_parents("empty_doc") == []

    def test_file_persistence(self, tmp_path, sample_parent_blocks):
        store = FileParentStore(tmp_path / "parents")
        store.store_parents("doc1", sample_parent_blocks)
        path = tmp_path / "parents" / "doc1.json"
        assert path.exists()
        data = json.loads(path.read_text())
        assert data["document_id"] == "doc1"
        assert len(data["parents"]) == 2

    def test_corrupted_file(self, parent_store):
        path = parent_store._path("corrupted")
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("not valid json")
        assert parent_store.load_parents("corrupted") == []


# ======================================================================
# HierarchicalSplitter Tests
# ======================================================================


class TestHierarchicalSplitter:
    def test_split_creates_parents_and_children(self):
        pages = [
            Document(page_content="Page one content. " * 50, metadata={"page": 1}),
            Document(page_content="Page two content. " * 50, metadata={"page": 2}),
        ]
        splitter = HierarchicalSplitter(document_id="doc1", filename="test.pdf")
        result = splitter.split(pages)
        assert len(result.parent_blocks) > 0
        assert len(result.child_chunks) > 0
        for child in result.child_chunks:
            assert child.metadata["document_id"] == "doc1"
            assert child.metadata["filename"] == "test.pdf"
            assert "parent_id" in child.metadata
            assert child.metadata["parent_id"] is not None

    def test_child_chunks_have_chunk_index(self):
        pages = [
            Document(page_content="Page one content. " * 50, metadata={"page": 1}),
        ]
        splitter = HierarchicalSplitter(document_id="doc2", filename="test.pdf")
        result = splitter.split(pages)
        for i, child in enumerate(result.child_chunks):
            assert child.metadata["chunk_index"] == i

    def test_parent_blocks_have_document_metadata(self):
        pages = [
            Document(page_content="Page one content. " * 50, metadata={"page": 1}),
        ]
        splitter = HierarchicalSplitter(document_id="doc3", filename="report.pdf", file_hash="abc123")
        result = splitter.split(pages)
        for parent in result.parent_blocks:
            assert parent.metadata["document_id"] == "doc3"
            assert parent.metadata["filename"] == "report.pdf"
            assert parent.metadata["file_hash"] == "abc123"
            assert "parent_id" in parent.metadata

    def test_parent_blocks_empty_content(self):
        splitter = HierarchicalSplitter(document_id="doc4", filename="empty.pdf")
        result = splitter.split([])
        assert len(result.parent_blocks) == 0
        assert len(result.child_chunks) == 0

    def test_short_content_single_parent(self):
        pages = [Document(page_content="Short content.", metadata={"page": 1})]
        splitter = HierarchicalSplitter(document_id="doc5", filename="short.pdf")
        result = splitter.split(pages)
        assert len(result.parent_blocks) == 1


# ======================================================================
# resolve_parents() Tests
# ======================================================================


class TestResolveParents:
    def test_basic_child_to_parent_mapping(self, parent_store, sample_parent_blocks, child_chunks):
        parent_store.store_parents("doc1", sample_parent_blocks)
        resolved = resolve_parents(child_chunks, parent_store)
        assert len(resolved) == 2
        assert "Large parent block one" in resolved[0].document.page_content
        assert "Large parent block two" in resolved[1].document.page_content

    def test_duplicate_parent_merging(self, parent_store, sample_parent_blocks):
        parent_store.store_parents("doc1", sample_parent_blocks)
        chunks = [
            _make_chunk("child a", doc_id="doc1", chunk_index=0, score=0.9, parent_ref={"parent_id": "doc1_parent_0", "page_range": [1, 2]}),
            _make_chunk("child b", doc_id="doc1", chunk_index=1, score=0.7, parent_ref={"parent_id": "doc1_parent_0", "page_range": [1, 2]}),
        ]
        resolved = resolve_parents(chunks, parent_store)
        assert len(resolved) == 1
        assert "Large parent block one" in resolved[0].document.page_content

    def test_score_preservation(self, parent_store, sample_parent_blocks):
        parent_store.store_parents("doc1", sample_parent_blocks)
        chunks = [
            _make_chunk("child a", doc_id="doc1", chunk_index=0, score=0.9, parent_ref={"parent_id": "doc1_parent_0", "page_range": [1, 2]}),
            _make_chunk("child b", doc_id="doc1", chunk_index=1, score=0.7, parent_ref={"parent_id": "doc1_parent_0", "page_range": [1, 2]}),
        ]
        resolved = resolve_parents(chunks, parent_store)
        assert resolved[0].score == 0.9

    def test_parent_metadata_preserved(self, parent_store, sample_parent_blocks, child_chunks):
        parent_store.store_parents("doc1", sample_parent_blocks)
        resolved = resolve_parents(child_chunks, parent_store)
        for chunk in resolved:
            assert "parent_id" in chunk.document.metadata
            assert "parent_reference" in chunk.document.metadata
            assert chunk.document.metadata["document_id"] == "doc1"
            assert chunk.document.metadata["filename"] == "test.pdf"

    def test_page_provenance(self, parent_store, sample_parent_blocks, child_chunks):
        parent_store.store_parents("doc1", sample_parent_blocks)
        resolved = resolve_parents(child_chunks, parent_store)
        ref = resolved[0].document.metadata["parent_reference"]
        assert ref["page_range"] == [1, 2]
        ref2 = resolved[1].document.metadata["parent_reference"]
        assert ref2["page_range"] == [3, 4]

    def test_fallback_when_parent_missing(self, parent_store, child_chunks):
        resolved = resolve_parents(child_chunks, parent_store)
        assert len(resolved) == 3
        for chunk in resolved:
            assert chunk is not None

    def test_children_without_parent_reference(self, parent_store, child_chunks_no_parent_ref):
        resolved = resolve_parents(child_chunks_no_parent_ref, parent_store)
        assert len(resolved) == 1
        assert resolved[0].document.page_content == "A chunk without parent reference."

    def test_empty_input(self, parent_store):
        resolved = resolve_parents([], parent_store)
        assert resolved == []

    def test_mixed_parent_and_non_parent(self, parent_store, sample_parent_blocks, child_chunks, child_chunks_no_parent_ref):
        parent_store.store_parents("doc1", sample_parent_blocks)
        mixed = child_chunks + child_chunks_no_parent_ref
        resolved = resolve_parents(mixed, parent_store)
        assert len(resolved) == 3
        parent_chunks = [c for c in resolved if c.document.metadata.get("parent_reference")]
        non_parent_chunks = [c for c in resolved if not c.document.metadata.get("parent_reference")]
        assert len(parent_chunks) == 2
        assert len(non_parent_chunks) == 1

    def test_resolved_chunks_are_retrieved_chunk_type(self, parent_store, sample_parent_blocks, child_chunks):
        parent_store.store_parents("doc1", sample_parent_blocks)
        resolved = resolve_parents(child_chunks, parent_store)
        for chunk in resolved:
            assert isinstance(chunk, RetrievedChunk)

    def test_resolved_chunks_have_source_type(self, parent_store, sample_parent_blocks, child_chunks):
        parent_store.store_parents("doc1", sample_parent_blocks)
        resolved = resolve_parents(child_chunks, parent_store)
        for chunk in resolved:
            if chunk.document.metadata.get("parent_reference"):
                assert chunk.document.metadata.get("source_type") == "parent_block"


# ======================================================================
# get_parent_retrieval_metadata Tests
# ======================================================================


class TestGetParentRetrievalMetadata:
    def test_returns_metadata(self, parent_store, sample_parent_blocks, child_chunks):
        parent_store.store_parents("doc1", sample_parent_blocks)
        resolved = resolve_parents(child_chunks, parent_store)
        meta = get_parent_retrieval_metadata(child_chunks, resolved)
        assert "child_chunks_found" in meta
        assert "unique_parents" in meta
        assert "merged_children" in meta
        assert "average_children_per_parent" in meta

    def test_counts_are_correct(self, parent_store, sample_parent_blocks, child_chunks):
        parent_store.store_parents("doc1", sample_parent_blocks)
        resolved = resolve_parents(child_chunks, parent_store)
        meta = get_parent_retrieval_metadata(child_chunks, resolved)
        assert meta["child_chunks_found"] == 3
        assert meta["unique_parents"] == 2
        assert meta["merged_children"] == 3
        assert meta["average_children_per_parent"] == 1.5

    def test_empty_input(self):
        meta = get_parent_retrieval_metadata([], [])
        assert meta["child_chunks_found"] == 0
        assert meta["unique_parents"] == 0
        assert meta["average_children_per_parent"] == 0


# ======================================================================
# ParentRetrievalStage Tests
# ======================================================================


class TestParentRetrievalStage:
    def test_skipped_when_disabled(self):
        stage = ParentRetrievalStage(MagicMock())
        config = _default_config(parent_retrieval_enabled=False)
        ctx = PipelineContext(original_query="test", config=config)
        ctx.merged_chunks = [_make_chunk("a")]
        result = stage.execute(ctx)
        assert result.parent_chunks == ctx.merged_chunks
        assert result.pipeline_trace[-1]["skipped"] is True

    def test_skipped_when_no_chunks(self):
        stage = ParentRetrievalStage(MagicMock())
        config = _default_config(parent_retrieval_enabled=True)
        ctx = PipelineContext(original_query="test", config=config)
        ctx.merged_chunks = []
        result = stage.execute(ctx)
        assert result.parent_chunks == []
        assert result.pipeline_trace[-1]["skipped"] is True

    def test_resolves_parents(self, parent_store, sample_parent_blocks, child_chunks):
        parent_store.store_parents("doc1", sample_parent_blocks)
        stage = ParentRetrievalStage(parent_store)
        config = _default_config(parent_retrieval_enabled=True)
        ctx = PipelineContext(original_query="test", config=config)
        ctx.merged_chunks = child_chunks
        result = stage.execute(ctx)
        assert len(result.parent_chunks) == 2
        assert "parent_retrieval" in result.pipeline_trace[-1]["stage"]

    def test_failure_falls_back(self):
        mock_store = MagicMock()
        mock_store.load_parent.side_effect = Exception("store failure")
        stage = ParentRetrievalStage(mock_store)
        config = _default_config(parent_retrieval_enabled=True)
        ctx = PipelineContext(original_query="test", config=config)
        ctx.merged_chunks = [_make_chunk("a", parent_ref={"parent_id": "p0", "page_range": [1, 2]})]
        result = stage.execute(ctx)
        assert len(result.parent_chunks) == 1
        assert result.pipeline_trace[-1].get("fallback") is True

    def test_pipeline_trace_with_metadata(self, parent_store, sample_parent_blocks, child_chunks):
        parent_store.store_parents("doc1", sample_parent_blocks)
        stage = ParentRetrievalStage(parent_store)
        config = _default_config(parent_retrieval_enabled=True)
        ctx = PipelineContext(original_query="test", config=config)
        ctx.merged_chunks = child_chunks
        result = stage.execute(ctx)
        trace = result.pipeline_trace[-1]
        assert trace["child_chunks_found"] == 3
        assert trace["unique_parents"] == 2


# ======================================================================
# Full Pipeline Integration Tests
# ======================================================================


class TestPipelineWithParentRetrieval:
    def test_parent_retrieval_in_pipeline_execution(self, parent_store, sample_parent_blocks, child_chunks):
        parent_store.store_parents("doc1", sample_parent_blocks)

        strategy = MagicMock()
        strategy.retrieve.return_value.chunks = child_chunks

        pipeline = RetrievalPipeline(strategy=strategy)
        config = _default_config(
            parent_retrieval_enabled=True,
            qp_rewrite_enabled=False,
            qp_expand_enabled=False,
            reranker="none",
        )
        serialized, result = pipeline.execute("test query", config)
        assert isinstance(result.chunks, list)
        for chunk in result.chunks:
            assert isinstance(chunk, RetrievedChunk)
        assert "pipeline" in result.retrieval_metadata
        parent_stages = [s for s in result.retrieval_metadata["pipeline"] if s.get("stage") == "parent_retrieval"]
        assert len(parent_stages) > 0

    def test_parent_retrieval_disabled_pipeline(self, child_chunks):
        strategy = MagicMock()
        strategy.retrieve.return_value.chunks = child_chunks

        pipeline = RetrievalPipeline(strategy=strategy)
        config = _default_config(
            parent_retrieval_enabled=False,
            qp_rewrite_enabled=False,
            qp_expand_enabled=False,
            reranker="none",
        )
        serialized, result = pipeline.execute("test query", config)
        parent_stages = [s for s in result.retrieval_metadata["pipeline"] if s.get("stage") == "parent_retrieval"]
        for s in parent_stages:
            if s.get("skipped") is not True:
                assert False, "parent_retrieval should be skipped when disabled"

    def test_reranker_receives_parent_contexts(self, parent_store, sample_parent_blocks, child_chunks):
        parent_store.store_parents("doc1", sample_parent_blocks)

        strategy = MagicMock()
        strategy.retrieve.return_value.chunks = child_chunks

        reranker = MagicMock()
        reranker.rerank.side_effect = lambda q, chunks: chunks

        pipeline = RetrievalPipeline(strategy=strategy, reranker=reranker)
        config = _default_config(
            parent_retrieval_enabled=True,
            qp_rewrite_enabled=False,
            qp_expand_enabled=False,
            reranker="cross_encoder",
        )
        serialized, result = pipeline.execute("test query", config)
        reranker.rerank.assert_called_once()
        reranked_chunks = reranker.rerank.call_args[0][1]
        for chunk in reranked_chunks:
            meta = chunk.document.metadata
            if meta.get("parent_reference"):
                assert meta.get("source_type") == "parent_block"

    def test_parent_retrieval_in_pipeline_trace_config(self, parent_store, sample_parent_blocks, child_chunks):
        parent_store.store_parents("doc1", sample_parent_blocks)

        strategy = MagicMock()
        strategy.retrieve.return_value.chunks = child_chunks

        pipeline = RetrievalPipeline(strategy=strategy)
        config = _default_config(
            parent_retrieval_enabled=True,
            qp_rewrite_enabled=False,
            qp_expand_enabled=False,
            reranker="none",
        )
        serialized, result = pipeline.execute("test query", config)
        assert result.retrieval_metadata["config"]["parent_retrieval_enabled"] is True

    def test_data_model_unchanged(self, parent_store, sample_parent_blocks, child_chunks):
        parent_store.store_parents("doc1", sample_parent_blocks)

        strategy = MagicMock()
        strategy.retrieve.return_value.chunks = child_chunks

        pipeline = RetrievalPipeline(strategy=strategy)
        config = _default_config(
            parent_retrieval_enabled=True,
            qp_rewrite_enabled=False,
            qp_expand_enabled=False,
            reranker="none",
        )
        serialized, result = pipeline.execute("test query", config)
        assert isinstance(result.original_query, str)
        assert isinstance(result.retrieval_query, str)
        assert isinstance(result.chunks, list)
        assert isinstance(result.retrieval_metadata, dict)
        for chunk in result.chunks:
            assert isinstance(chunk, RetrievedChunk)

    def test_create_pipeline_from_config(self):
        config = _default_config(parent_retrieval_enabled=True)
        pipeline = create_pipeline_from_config(config)
        assert isinstance(pipeline, RetrievalPipeline)
