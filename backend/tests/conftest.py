import sys
import types
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


class _MockEmbeddings:
    def embed_query(self, query: str) -> list[float]:
        return [0.1, 0.2, 0.3, 0.4]

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        return [self.embed_query(t) for _ in texts]


_mock_mod = types.ModuleType("backend.rag.embeddings")
_mock_mod.embeddings = _MockEmbeddings()
sys.modules["backend.rag.embeddings"] = _mock_mod
