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


from langchain_core.documents import Document

from backend.rag.chunking import BaseChunkingStrategy, FixedChunkingStrategy


class TestFixedChunkingStrategy:
    def test_returns_chunking_result(self):
        strategy = FixedChunkingStrategy(chunk_size=500, chunk_overlap=50)
        docs = [Document(page_content="Hello world. " * 100, metadata={"page": 0})]
        result = strategy.split(docs)
        assert isinstance(result, ChunkingResult)
        assert result.success is True
        assert result.metrics.strategy == "fixed"
        assert result.metrics.chunk_count > 0

    def test_respects_chunk_size(self):
        strategy = FixedChunkingStrategy(chunk_size=200, chunk_overlap=20)
        long_text = "word " * 200  # 1000 chars
        docs = [Document(page_content=long_text, metadata={"page": 0})]
        result = strategy.split(docs)
        for chunk in result.chunks:
            assert len(chunk.page_content) <= 220  # some tolerance for overlap

    def test_handles_empty_input(self):
        strategy = FixedChunkingStrategy(chunk_size=500, chunk_overlap=50)
        result = strategy.split([])
        assert result.chunks == []
        assert result.metrics.chunk_count == 0

    def test_single_small_document(self):
        strategy = FixedChunkingStrategy(chunk_size=500, chunk_overlap=50)
        docs = [Document(page_content="Short text.", metadata={"page": 0})]
        result = strategy.split(docs)
        assert result.metrics.chunk_count == 1
        assert result.chunks[0].page_content == "Short text."

    def test_multiple_documents(self):
        strategy = FixedChunkingStrategy(chunk_size=200, chunk_overlap=20)
        docs = [
            Document(page_content="First document. " * 50, metadata={"page": 0}),
            Document(page_content="Second document. " * 50, metadata={"page": 1}),
        ]
        result = strategy.split(docs)
        assert result.metrics.chunk_count > 2  # both docs should produce chunks


from backend.rag.chunking import Boundary, BoundaryRule


class TestBoundary:
    def test_boundary_creation(self):
        b = Boundary(position=10, priority=1, label="heading")
        assert b.position == 10
        assert b.priority == 1
        assert b.label == "heading"

    def test_boundary_ordering(self):
        b1 = Boundary(position=20, priority=3, label="paragraph")
        b2 = Boundary(position=10, priority=1, label="heading")
        boundaries = sorted([b1, b2], key=lambda b: b.position)
        assert boundaries[0].position == 10
        assert boundaries[1].position == 20


from backend.rag.chunking import (
    HeadingRule, NumberedSectionRule, ParagraphRule,
    ListRule, SentenceRule,
)


class TestHeadingRule:
    def test_markdown_heading(self):
        rule = HeadingRule()
        doc = Document(page_content="# Introduction\nSome text here.", metadata={})
        boundaries = rule.detect(doc)
        assert len(boundaries) >= 1
        assert any(b.label == "heading" for b in boundaries)
        assert boundaries[0].position == 0  # heading at start

    def test_standalone_caps(self):
        rule = HeadingRule()
        doc = Document(page_content="INSTALLATION\nFollow these steps.", metadata={})
        boundaries = rule.detect(doc)
        assert any(b.label == "heading" for b in boundaries)

    def test_no_heading(self):
        rule = HeadingRule()
        doc = Document(page_content="Just regular text without any headings.", metadata={})
        boundaries = rule.detect(doc)
        assert len(boundaries) == 0


class TestParagraphRule:
    def test_double_newline(self):
        rule = ParagraphRule()
        doc = Document(page_content="First paragraph.\n\nSecond paragraph.", metadata={})
        boundaries = rule.detect(doc)
        assert len(boundaries) >= 1
        assert boundaries[0].label == "paragraph"
        assert boundaries[0].position == 16  # after "First paragraph."

    def test_no_paragraphs(self):
        rule = ParagraphRule()
        doc = Document(page_content="Single paragraph text.", metadata={})
        boundaries = rule.detect(doc)
        assert len(boundaries) == 0


class TestListRule:
    def test_bullet_list(self):
        rule = ListRule()
        doc = Document(page_content="- Item one\n- Item two\n- Item three", metadata={})
        boundaries = rule.detect(doc)
        assert len(boundaries) == 3
        assert all(b.label == "list" for b in boundaries)

    def test_no_list(self):
        rule = ListRule()
        doc = Document(page_content="No lists here.", metadata={})
        boundaries = rule.detect(doc)
        assert len(boundaries) == 0


class TestSentenceRule:
    def test_sentence_boundaries(self):
        rule = SentenceRule()
        doc = Document(page_content="First sentence. Second sentence. Third sentence.", metadata={})
        boundaries = rule.detect(doc)
        assert len(boundaries) >= 2
        assert all(b.label == "sentence" for b in boundaries)

    def test_no_sentences(self):
        rule = SentenceRule()
        doc = Document(page_content="One sentence only", metadata={})
        boundaries = rule.detect(doc)
        assert len(boundaries) == 0


class TestNumberedSectionRule:
    def test_numbered_sections(self):
        rule = NumberedSectionRule()
        doc = Document(page_content="1. First section\n2. Second section\n3. Third section", metadata={})
        boundaries = rule.detect(doc)
        assert len(boundaries) == 3
        assert all(b.label == "numbered_section" for b in boundaries)


from backend.rag.chunking import BoundaryDetector


class TestBoundaryDetector:
    def test_detects_heading_and_paragraph(self):
        detector = BoundaryDetector()
        doc = Document(
            page_content="# Title\n\nFirst paragraph.\n\nSecond paragraph.",
            metadata={},
        )
        boundaries = detector.detect(doc)
        labels = [b.label for b in boundaries]
        assert "heading" in labels
        assert "paragraph" in labels

    def test_sorts_by_position(self):
        detector = BoundaryDetector()
        doc = Document(
            page_content="# Title\n\nSome text.\n\nMore text.",
            metadata={},
        )
        boundaries = detector.detect(doc)
        positions = [b.position for b in boundaries]
        assert positions == sorted(positions)

    def test_deduplicates_same_position(self):
        detector = BoundaryDetector()
        doc = Document(
            page_content="HEADING\n\nParagraph.",
            metadata={},
        )
        boundaries = detector.detect(doc)
        positions_at_0 = [b for b in boundaries if b.position == 0]
        assert len(positions_at_0) <= 1

    def test_empty_text(self):
        detector = BoundaryDetector()
        doc = Document(page_content="", metadata={})
        boundaries = detector.detect(doc)
        assert boundaries == []

    def test_custom_rules(self):
        detector = BoundaryDetector(rules=[])
        doc = Document(page_content="# Title\n\nParagraph.", metadata={})
        boundaries = detector.detect(doc)
        assert boundaries == []


from backend.rag.chunking import ChunkAssembler


class TestChunkAssembler:
    def test_splits_at_boundaries(self):
        assembler = ChunkAssembler(min_size=10, max_size=100)
        text = "First section.\n\nSecond section.\n\nThird section."
        boundaries = [
            Boundary(position=15, priority=3, label="paragraph"),
            Boundary(position=32, priority=3, label="paragraph"),
        ]
        chunks = assembler.assemble(text, boundaries)
        assert len(chunks) == 3
        assert chunks[0].page_content == "First section."
        assert chunks[1].page_content == "Second section."
        assert chunks[2].page_content == "Third section."

    def test_merges_small_chunks(self):
        assembler = ChunkAssembler(min_size=20, max_size=100)
        text = "Hi.\n\nThis is a longer paragraph with more content."
        boundaries = [
            Boundary(position=3, priority=3, label="paragraph"),
        ]
        chunks = assembler.assemble(text, boundaries)
        # "Hi." is only 3 chars, should merge with next
        assert len(chunks) == 1
        assert "Hi." in chunks[0].page_content

    def test_splits_large_chunks(self):
        assembler = ChunkAssembler(min_size=5, max_size=20)
        text = "Short. " * 10  # 70 chars
        boundaries = [
            Boundary(position=7, priority=5, label="sentence"),
            Boundary(position=14, priority=5, label="sentence"),
            Boundary(position=21, priority=5, label="sentence"),
            Boundary(position=28, priority=5, label="sentence"),
            Boundary(position=35, priority=5, label="sentence"),
            Boundary(position=42, priority=5, label="sentence"),
            Boundary(position=49, priority=5, label="sentence"),
            Boundary(position=56, priority=5, label="sentence"),
            Boundary(position=63, priority=5, label="sentence"),
        ]
        chunks = assembler.assemble(text, boundaries)
        for chunk in chunks:
            assert len(chunk.page_content) <= 25  # some tolerance

    def test_no_boundaries_returns_whole_text(self):
        assembler = ChunkAssembler(min_size=10, max_size=100)
        text = "Just one chunk of text."
        chunks = assembler.assemble(text, [])
        assert len(chunks) == 1
        assert chunks[0].page_content == text

    def test_output_is_exact_substring(self):
        """ChunkAssembler never invents content."""
        assembler = ChunkAssembler(min_size=5, max_size=50)
        text = "Alpha bravo charlie delta echo foxtrot golf hotel."
        boundaries = [
            Boundary(position=14, priority=3, label="paragraph"),
            Boundary(position=28, priority=3, label="paragraph"),
        ]
        chunks = assembler.assemble(text, boundaries)
        for chunk in chunks:
            assert chunk.page_content in text


from backend.rag.chunking import AdaptiveChunkingStrategy


class TestAdaptiveChunkingStrategy:
    def test_heading_preserved(self):
        strategy = AdaptiveChunkingStrategy(min_chunk_size=50, max_chunk_size=500)
        doc = Document(
            page_content="# Introduction\n\n" + "Content here. " * 20 + "\n\n# Methods\n\n" + "Methods content. " * 20,
            metadata={"page": 0},
        )
        result = strategy.split([doc])
        assert result.success is True
        texts = [c.page_content for c in result.chunks]
        assert any("# Introduction" in t for t in texts)
        assert any("# Methods" in t for t in texts)

    def test_paragraph_preserved(self):
        strategy = AdaptiveChunkingStrategy(min_chunk_size=20, max_chunk_size=500)
        doc = Document(
            page_content="First paragraph with enough content to be meaningful.\n\nSecond paragraph with enough content to be meaningful.",
            metadata={"page": 0},
        )
        result = strategy.split([doc])
        assert result.success is True
        assert result.metrics.chunk_count >= 2

    def test_fallback_when_no_boundaries(self):
        from backend.rag.chunking import FixedChunkingStrategy
        fallback = FixedChunkingStrategy(chunk_size=500, chunk_overlap=50)
        strategy = AdaptiveChunkingStrategy(
            min_chunk_size=50, max_chunk_size=500, fallback_strategy=fallback,
        )
        doc = Document(page_content="Hello", metadata={"page": 0})
        result = strategy.split([doc])
        assert result.success is True
        assert result.metrics.fallback_used is True
        assert result.metrics.chunk_count == 1

    def test_deterministic(self):
        strategy = AdaptiveChunkingStrategy(min_chunk_size=50, max_chunk_size=500)
        doc = Document(
            page_content="# Title\n\nParagraph one.\n\nParagraph two.",
            metadata={"page": 0},
        )
        result1 = strategy.split([doc])
        result2 = strategy.split([doc])
        assert len(result1.chunks) == len(result2.chunks)
        for c1, c2 in zip(result1.chunks, result2.chunks):
            assert c1.page_content == c2.page_content

    def test_metrics_populated(self):
        strategy = AdaptiveChunkingStrategy(min_chunk_size=50, max_chunk_size=500)
        doc = Document(
            page_content="# Heading\n\n" + "Content. " * 30,
            metadata={"page": 0},
        )
        result = strategy.split([doc])
        assert result.metrics.strategy == "adaptive"
        assert result.metrics.chunk_count > 0
        assert result.metrics.duration_ms > 0
        assert result.metrics.average_chunk_size > 0

    def test_respects_min_max_size(self):
        strategy = AdaptiveChunkingStrategy(min_chunk_size=30, max_chunk_size=100)
        doc = Document(
            page_content="# Title\n\n" + "Word " * 50 + "\n\n# Section2\n\n" + "Text " * 50,
            metadata={"page": 0},
        )
        result = strategy.split([doc])
        for chunk in result.chunks:
            assert len(chunk.page_content) <= 120
