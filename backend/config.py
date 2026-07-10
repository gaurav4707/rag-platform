"""
Application configuration.

All project-wide constants should live here.
Avoid hardcoding paths, model names, or chunking settings
inside other modules.
"""

from pathlib import Path

# -----------------------------------------------------------------------------
# Project Paths
# -----------------------------------------------------------------------------

BASE_DIR = Path(__file__).resolve().parent

STORAGE_DIR = BASE_DIR / "storage"
CHROMA_DB_DIR = STORAGE_DIR / "chroma_langchain_db"

# Create directories if they don't exist
STORAGE_DIR.mkdir(parents=True, exist_ok=True)
CHROMA_DB_DIR.mkdir(parents=True, exist_ok=True)

# -----------------------------------------------------------------------------
# Uploads
# -----------------------------------------------------------------------------

UPLOAD_DIR = STORAGE_DIR / "uploads"
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

# -----------------------------------------------------------------------------
# ChromaDB
# -----------------------------------------------------------------------------

CHROMA_COLLECTION_NAME = "example_collection"

# -----------------------------------------------------------------------------
# Models
# -----------------------------------------------------------------------------

EMBEDDING_MODEL = "BAAI/bge-base-en-v1.5"

# -----------------------------------------------------------------------------
# Text Splitting
# -----------------------------------------------------------------------------

CHUNK_SIZE = 1000
CHUNK_OVERLAP = 200

# -----------------------------------------------------------------------------
# Retrieval
# -----------------------------------------------------------------------------

TOP_K = 8