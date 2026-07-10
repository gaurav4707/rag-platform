import sys
import types
from pathlib import Path

import pytest
from langchain_chroma import Chroma
from langchain_core.documents import Document

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


class _MockEmbeddings:
    def embed_query(self, query: str) -> list[float]:
        return [0.1, 0.2, 0.3, 0.4]

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        return [self.embed_query(t) for t in texts]


_mock_mod = types.ModuleType("backend.rag.embeddings")
_mock_mod.embeddings = _MockEmbeddings()
sys.modules["backend.rag.embeddings"] = _mock_mod


class _DummyEmbeddings:
    """Deterministic embedding function for testing."""

    def embed_query(self, text: str) -> list[float]:
        import hashlib

        h = hashlib.md5(text.encode()).hexdigest()
        return [float(ord(c)) / 255.0 for c in h[:4]]

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        return [self.embed_query(t) for t in texts]


@pytest.fixture
def temp_chroma(tmp_path):
    """Create a temporary Chroma collection with dummy embeddings."""
    db_dir = tmp_path / "chroma_test"
    db_dir.mkdir(parents=True, exist_ok=True)

    collection = Chroma(
        collection_name="test_collection",
        embedding_function=_DummyEmbeddings(),
        persist_directory=str(db_dir),
    )

    docs = [
        Document(
            page_content="The capital of France is Paris.",
            metadata={
                "document_id": "1",
                "filename": "geo.pdf",
                "page": 1,
                "file_hash": "",
            },
        ),
        Document(
            page_content="Paris is known for the Eiffel Tower.",
            metadata={
                "document_id": "1",
                "filename": "geo.pdf",
                "page": 2,
                "file_hash": "",
            },
        ),
        Document(
            page_content="The Eiffel Tower was built in 1889.",
            metadata={
                "document_id": "1",
                "filename": "geo.pdf",
                "page": 3,
                "file_hash": "",
            },
        ),
        Document(
            page_content="Python is a programming language.",
            metadata={
                "document_id": "2",
                "filename": "tech.pdf",
                "page": 1,
                "file_hash": "",
            },
        ),
        Document(
            page_content="Python was created by Guido van Rossum.",
            metadata={
                "document_id": "2",
                "filename": "tech.pdf",
                "page": 2,
                "file_hash": "",
            },
        ),
        Document(
            page_content="Python supports object-oriented programming.",
            metadata={
                "document_id": "2",
                "filename": "tech.pdf",
                "page": 3,
                "file_hash": "",
            },
        ),
    ]
    collection.add_documents(docs)
    yield collection
