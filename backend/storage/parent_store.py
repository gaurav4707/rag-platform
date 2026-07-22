"""Parent store abstraction with file-based implementation.

Parent blocks are persisted independently from vector embeddings.
The retrieval layer depends only on BaseParentStore, never on storage details.
"""

from __future__ import annotations

import json
import logging
from abc import ABC, abstractmethod
from dataclasses import asdict, dataclass, field
from functools import lru_cache
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


@dataclass
class ParentBlock:
    parent_id: str
    content: str
    start_page: int | None = None
    end_page: int | None = None
    child_indices: list[int] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)


class BaseParentStore(ABC):
    @abstractmethod
    def store_parents(self, document_id: str, parents: list[ParentBlock]) -> None:
        ...

    @abstractmethod
    def load_parents(self, document_id: str) -> list[ParentBlock]:
        ...

    @abstractmethod
    def load_parent(self, document_id: str, parent_id: str) -> ParentBlock | None:
        ...

    @abstractmethod
    def delete_parents(self, document_id: str) -> None:
        ...

    @abstractmethod
    def parent_exists(self, document_id: str) -> bool:
        ...


class FileParentStore(BaseParentStore):

    def __init__(self, storage_dir: Path):
        self.storage_dir = storage_dir
        self.storage_dir.mkdir(parents=True, exist_ok=True)

    def _path(self, document_id: str) -> Path:
        return self.storage_dir / f"{document_id}.json"

    def store_parents(self, document_id: str, parents: list[ParentBlock]) -> None:
        data = {
            "document_id": document_id,
            "parents": [asdict(p) for p in parents],
        }
        path = self._path(document_id)
        path.write_text(json.dumps(data, indent=2))
        self._load_parents_cache.cache_clear()

    @lru_cache(maxsize=128)
    def _load_parents_cache(self, document_id: str) -> list[ParentBlock]:
        path = self._path(document_id)
        if not path.exists():
            return []
        try:
            data = json.loads(path.read_text())
            return [ParentBlock(**p) for p in data.get("parents", [])]
        except (json.JSONDecodeError, KeyError) as e:
            logger.warning("Failed to load parents for %s: %s", document_id, e)
            return []

    def load_parents(self, document_id: str) -> list[ParentBlock]:
        return self._load_parents_cache(document_id)

    def load_parent(self, document_id: str, parent_id: str) -> ParentBlock | None:
        parents = self.load_parents(document_id)
        for p in parents:
            if p.parent_id == parent_id:
                return p
        return None

    def delete_parents(self, document_id: str) -> None:
        path = self._path(document_id)
        path.unlink(missing_ok=True)
        self._load_parents_cache.cache_clear()

    def parent_exists(self, document_id: str) -> bool:
        return self._path(document_id).exists()
