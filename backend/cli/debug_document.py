"""Debug document CLI tool.

Read-only inspection of indexed documents, their chunks, metadata, and validation status.
"""

import argparse
import json
import sys
from pathlib import Path
from typing import Optional

from backend.config import (
    CHROMA_COLLECTION_NAME,
    CHROMA_DB_DIR,
    UPLOAD_DIR,
    TOP_K,
    CHUNK_SIZE,
    CHUNK_OVERLAP,
    EMBEDDING_MODEL,
    EMBEDDING_PROVIDER,
    EMBEDDING_LOCAL_FILES_ONLY,
)
from backend.providers import get_embedding_provider
from backend.rag.vector_store import get_all_documents, list_documents, _get_collection
from backend.services.document_service import list_indexed_documents


def find_document_by_id(document_id: str) -> Optional[dict]:
    """Find document by ID in the vector store."""
    docs = list_documents()
    for doc in docs:
        if doc.get("document_id") == document_id:
            return doc
    return None


def find_document_by_filename(filename: str) -> Optional[dict]:
    """Find document by filename in the vector store."""
    docs = list_documents()
    for doc in docs:
        if doc.get("filename") == filename:
            return doc
    return None


def get_chunks_for_document(document_id: str) -> list:
    """Get all chunks for a specific document from the vector store."""
    all_docs = get_all_documents()
    return [doc for doc in all_docs if doc.metadata.get("document_id") == document_id]


def get_unique_pages(chunks: list) -> int:
    """Get count of unique page numbers from chunks."""
    pages = set()
    for chunk in chunks:
        page = chunk.metadata.get("page")
        if page is not None:
            pages.add(page)
    return len(pages)


def validate_metadata(chunks: list) -> tuple[bool, list]:
    """Validate that all chunks have required metadata fields.

    Returns:
        (all_valid, missing_fields_per_chunk)
    """
    required_fields = ["document_id", "filename", "page", "chunk_index"]
    all_valid = True
    missing_per_chunk = []

    for chunk in chunks:
        missing = [field for field in required_fields if field not in chunk.metadata]
        if missing:
            all_valid = False
        missing_per_chunk.append(missing)

    return all_valid, missing_per_chunk


def get_all_metadata_keys(chunks: list) -> list:
    """Get all unique metadata keys across all chunks."""
    keys = set()
    for chunk in chunks:
        keys.update(chunk.metadata.keys())
    return sorted(keys)


def get_embedding_info() -> tuple[str, str, bool]:
    """Get embedding provider info.

    Returns:
        (provider_class_name, model_name, loads_successfully)
    """
    try:
        provider = get_embedding_provider()
        provider_name = provider.__class__.__name__
        model_name = getattr(provider, "model_name", getattr(provider, "model", "unknown"))
        return provider_name, model_name, True
    except Exception:
        return "Unknown", "Unknown", False


def get_chroma_collection_info() -> dict:
    """Get ChromaDB collection information."""
    try:
        collection = _get_collection()
        chroma_collection = collection._collection
        count = chroma_collection.count()
        return {
            "collection_name": CHROMA_COLLECTION_NAME,
            "persist_directory": str(CHROMA_DB_DIR),
            "vector_count": count,
            "accessible": True,
        }
    except Exception as e:
        return {
            "collection_name": CHROMA_COLLECTION_NAME,
            "persist_directory": str(CHROMA_DB_DIR),
            "vector_count": 0,
            "accessible": False,
            "error": str(e),
        }


def get_vector_count_for_document(document_id: str) -> int:
    """Get vector count for a specific document by querying Chroma directly."""
    try:
        collection = _get_collection()
        chroma_collection = collection._collection
        result = chroma_collection.get(where={"document_id": document_id}, include=[])
        ids = result.get("ids", [])
        return len(ids)
    except Exception:
        return 0


def format_human_report(
    doc_info: dict,
    pdf_path: Path,
    pdf_exists: bool,
    chunks: list,
    unique_pages: int,
    chunk_count: int,
    vector_count: int,
    chroma_info: dict,
    embedding_provider: str,
    embedding_model: str,
    embedding_loads: bool,
    metadata_keys: list,
    sample_chunk: Optional[object],
    validation_results: dict,
) -> str:
    """Format the human-readable debug report."""
    lines = []
    lines.append("=" * 60)
    lines.append("Document Debug Report")
    lines.append("=" * 60)
    lines.append("")

    # Document Information
    lines.append("Document Information")
    lines.append("-" * 60)
    lines.append(f"Document ID:        {doc_info.get('document_id', 'N/A')}")
    lines.append(f"Filename:           {doc_info.get('filename', 'N/A')}")
    lines.append(f"File Hash:          {doc_info.get('file_hash', 'N/A')}")
    lines.append(f"Upload Path:        {pdf_path}")
    lines.append(f"Exists on Disk:     {'✅' if pdf_exists else '❌'}")
    lines.append("")

    # Storage Information
    lines.append("Storage Information")
    lines.append("-" * 60)
    lines.append(f"Chroma Collection:  {chroma_info.get('collection_name', 'N/A')}")
    lines.append(f"Persist Directory:  {chroma_info.get('persist_directory', 'N/A')}")
    lines.append(f"Collection Vectors: {chroma_info.get('vector_count', 'N/A')}")
    lines.append(f"Collection Access:  {'✅' if chroma_info.get('accessible') else '❌'}")
    if not chroma_info.get('accessible'):
        lines.append(f"Error:              {chroma_info.get('error', 'Unknown')}")
    lines.append("")

    # Chunk Statistics
    lines.append("Chunk Statistics")
    lines.append("-" * 60)
    lines.append(f"Pages:              {unique_pages}")
    lines.append(f"Chunk Count:        {chunk_count}")
    lines.append(f"Vector Count:       {vector_count}")
    lines.append("")

    # Retrieval Configuration
    lines.append("Retrieval Configuration")
    lines.append("-" * 60)
    lines.append(f"Top-K:              {TOP_K}")
    lines.append(f"Chunk Size:         {CHUNK_SIZE}")
    lines.append(f"Chunk Overlap:      {CHUNK_OVERLAP}")
    lines.append("")

    # Embedding Information
    lines.append("Embedding Information")
    lines.append("-" * 60)
    lines.append(f"Provider:           {embedding_provider}")
    lines.append(f"Model:              {embedding_model}")
    lines.append(f"Provider Loads:     {'✅' if embedding_loads else '❌'}")
    lines.append(f"Config Provider:    {EMBEDDING_PROVIDER}")
    lines.append(f"Config Model:       {EMBEDDING_MODEL}")
    lines.append(f"Local Files Only:   {EMBEDDING_LOCAL_FILES_ONLY}")
    lines.append("")

    # Metadata Keys
    lines.append("Metadata Keys")
    lines.append("-" * 60)
    for key in metadata_keys:
        lines.append(f"✓ {key}")
    lines.append("")

    # Sample Chunk
    if sample_chunk:
        lines.append(
            f"Sample Chunk (page={sample_chunk.metadata.get('page')}, "
            f"chunk_index={sample_chunk.metadata.get('chunk_index')}, "
            f"chars={len(sample_chunk.page_content)})"
        )
        lines.append("-" * 60)
        preview = sample_chunk.page_content[:300]
        if len(sample_chunk.page_content) > 300:
            preview += "..."
        lines.append(preview)
        lines.append("")

    # Validation
    lines.append("Validation")
    lines.append("-" * 60)
    for check, result in validation_results.items():
        status = "✅" if result else "❌"
        lines.append(f"{status} {check}")
    lines.append("")

    lines.append("=" * 60)

    return "\n".join(lines)


def build_json_report(
    doc_info: dict,
    pdf_path: Path,
    pdf_exists: bool,
    chunks: list,
    unique_pages: int,
    chunk_count: int,
    vector_count: int,
    chroma_info: dict,
    embedding_provider: str,
    embedding_model: str,
    embedding_loads: bool,
    metadata_keys: list,
    sample_chunk: Optional[object],
    validation_results: dict,
) -> dict:
    """Build JSON report dictionary."""
    sample_data = None
    if sample_chunk:
        sample_data = {
            "page": sample_chunk.metadata.get("page"),
            "chunk_index": sample_chunk.metadata.get("chunk_index"),
            "char_count": len(sample_chunk.page_content),
            "preview": sample_chunk.page_content[:300],
        }

    return {
        "document_id": doc_info.get("document_id"),
        "filename": doc_info.get("filename"),
        "file_hash": doc_info.get("file_hash"),
        "pages": unique_pages,
        "chunks": chunk_count,
        "vectors": vector_count,
        "chroma": chroma_info,
        "retrieval_config": {
            "top_k": TOP_K,
            "chunk_size": CHUNK_SIZE,
            "chunk_overlap": CHUNK_OVERLAP,
        },
        "embedding": {
            "provider": embedding_provider,
            "model": embedding_model,
            "provider_loads": embedding_loads,
            "config_provider": EMBEDDING_PROVIDER,
            "config_model": EMBEDDING_MODEL,
            "local_files_only": EMBEDDING_LOCAL_FILES_ONLY,
        },
        "metadata_keys": metadata_keys,
        "sample_chunk": sample_data,
        "validation": validation_results,
    }


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Debug document CLI - inspect indexed documents",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )

    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument(
        "--document-id",
        "-d",
        type=str,
        help="Document UUID to inspect",
    )
    group.add_argument(
        "--filename",
        "-f",
        type=str,
        help="Original filename to inspect",
    )

    parser.add_argument(
        "--json",
        action="store_true",
        help="Output machine-readable JSON instead of formatted report",
    )

    args = parser.parse_args()

    # Find document
    doc_info = None
    if args.document_id:
        doc_info = find_document_by_id(args.document_id)
        if not doc_info:
            print(f"Error: Document with ID '{args.document_id}' not found", file=sys.stderr)
            return 2
    else:
        doc_info = find_document_by_filename(args.filename)
        if not doc_info:
            print(f"Error: Document with filename '{args.filename}' not found", file=sys.stderr)
            return 2

    document_id = doc_info["document_id"]

    # Check PDF exists
    pdf_path = UPLOAD_DIR / f"{document_id}.pdf"
    pdf_exists = pdf_path.exists()

    # Get chunks
    chunks = get_chunks_for_document(document_id)
    chunk_count = len(chunks)

    # Get stats
    unique_pages = get_unique_pages(chunks)

    # Get vector count from Chroma directly
    vector_count = get_vector_count_for_document(document_id)

    # Get Chroma collection info
    chroma_info = get_chroma_collection_info()

    # Embedding info
    embedding_provider, embedding_model, embedding_loads = get_embedding_info()

    # Metadata keys
    metadata_keys = get_all_metadata_keys(chunks)

    # Sample chunk (first by chunk_index)
    sample_chunk = None
    if chunks:
        sorted_chunks = sorted(chunks, key=lambda c: c.metadata.get("chunk_index", 0))
        sample_chunk = sorted_chunks[0]

    # Validation
    metadata_valid, missing_per_chunk = validate_metadata(chunks)
    all_have_metadata = metadata_valid and all(not m for m in missing_per_chunk)

    validation_results = {
        "file_exists": pdf_exists,
        "chunks_indexed": chunk_count > 0,
        "vector_count_matches": vector_count == chunk_count,
        "metadata_complete": all_have_metadata,
        "retrieval_ready": pdf_exists and chunk_count > 0 and vector_count == chunk_count and all_have_metadata,
    }

    # Build and output report
    if args.json:
        report = build_json_report(
            doc_info,
            pdf_path,
            pdf_exists,
            chunks,
            unique_pages,
            chunk_count,
            vector_count,
            chroma_info,
            embedding_provider,
            embedding_model,
            embedding_loads,
            metadata_keys,
            sample_chunk,
            validation_results,
        )
        print(json.dumps(report, indent=2))
    else:
        report = format_human_report(
            doc_info,
            pdf_path,
            pdf_exists,
            chunks,
            unique_pages,
            chunk_count,
            vector_count,
            chroma_info,
            embedding_provider,
            embedding_model,
            embedding_loads,
            metadata_keys,
            sample_chunk,
            validation_results,
        )
        print(report)

    # Exit code based on validation
    if not validation_results["retrieval_ready"]:
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())