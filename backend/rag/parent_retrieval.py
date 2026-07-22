"""Parent Document Retrieval for the Retrieval Pipeline.

Resolves child chunks to their parent blocks after initial retrieval.
The parent blocks provide larger, coherent contexts for the reranker and LLM.

This module contains ONLY retrieval logic — storage is handled by BaseParentStore.
"""

from __future__ import annotations

import logging
from collections import OrderedDict

from langchain_core.documents import Document

from backend.models.rag_models import RetrievedChunk
from backend.storage.parent_store import BaseParentStore, ParentBlock

logger = logging.getLogger(__name__)


def _extract_parent_ref(metadata: dict) -> dict | None:
    parent_id = metadata.get("parent_id")
    if not parent_id:
        return None
    return {
        "parent_id": parent_id,
        "page_range": [
            metadata.get("parent_page_range_start"),
            metadata.get("parent_page_range_end"),
        ],
        "child_indices": [metadata.get("parent_child_index", 0)],
    }


def _best_score(existing: float | None, candidate: float | None) -> float | None:
    if existing is None:
        return candidate
    if candidate is None:
        return existing
    return max(existing, candidate)


def resolve_parents(
    child_chunks: list[RetrievedChunk],
    parent_store: BaseParentStore,
) -> list[RetrievedChunk]:
    if not child_chunks:
        return []

    seen_parents: OrderedDict[str, tuple[ParentBlock, float | None]] = OrderedDict()
    provenance: dict[str, dict] = {}

    for chunk in child_chunks:
        parent_ref = _extract_parent_ref(chunk.document.metadata)
        if not parent_ref:
            continue

        parent_id = parent_ref["parent_id"]
        document_id = chunk.document.metadata.get("document_id", "")

        if not parent_id or not document_id:
            continue

        parent_block = parent_store.load_parent(document_id, parent_id)

        if parent_block is None:
            logger.warning(
                "Parent block %s not found for document %s, falling back to child chunk",
                parent_id,
                document_id,
            )
            seen_parents[chunk.document.metadata.get("chunk_index", str(id(chunk)))] = (
                ParentBlock(
                    parent_id=parent_id or "",
                    content=chunk.document.page_content,
                    start_page=parent_ref.get("page_range", [None, None])[0],
                    end_page=parent_ref.get("page_range", [None, None])[1],
                    child_indices=[chunk.document.metadata.get("chunk_index", 0)],
                    metadata=chunk.document.metadata,
                ),
                chunk.score,
            )
            continue

        if parent_id in seen_parents:
            existing_score = seen_parents[parent_id][1]
            seen_parents[parent_id] = (parent_block, _best_score(existing_score, chunk.score))
        else:
            seen_parents[parent_id] = (parent_block, chunk.score)

        provenance.setdefault(parent_id, {})
        if not provenance[parent_id].get("document_id"):
            provenance[parent_id]["document_id"] = document_id
        if not provenance[parent_id].get("filename"):
            provenance[parent_id]["filename"] = chunk.document.metadata.get("filename", "")

    resolved = []
    for parent_id, (block, score) in seen_parents.items():
        ref = {
            "parent_id": block.parent_id,
            "page_range": [block.start_page, block.end_page],
            "child_indices": block.child_indices,
        }
        meta_doc = Document(
            page_content=block.content,
            metadata={
                "document_id": block.metadata.get("document_id", provenance.get(parent_id, {}).get("document_id", "")),
                "filename": block.metadata.get("filename", provenance.get(parent_id, {}).get("filename", "")),
                "parent_id": block.parent_id,
                "parent_page_range_start": block.start_page,
                "parent_page_range_end": block.end_page,
                "parent_child_index": block.child_indices[0] if block.child_indices else 0,
                "page": block.start_page,
                "chunk_index": 0,
                "source_type": "parent_block",
                "parent_reference": ref,
            },
        )
        resolved.append(RetrievedChunk(document=meta_doc, score=score))

    children_without_parents = [
        c for c in child_chunks
        if not _extract_parent_ref(c.document.metadata)
    ]

    return resolved + children_without_parents


def get_parent_retrieval_metadata(child_chunks: list[RetrievedChunk], resolved: list[RetrievedChunk]) -> dict:
    child_count = len(child_chunks)
    unique_parents = len(resolved)
    children_with_parent = [c for c in child_chunks if _extract_parent_ref(c.document.metadata)]
    merged_children = len(children_with_parent)
    avg_children = round(merged_children / max(unique_parents, 1), 1) if unique_parents > 0 else 0

    return {
        "child_chunks_found": child_count,
        "unique_parents": unique_parents,
        "merged_children": merged_children,
        "average_children_per_parent": avg_children,
    }
