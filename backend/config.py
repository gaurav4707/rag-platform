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
# ChromaDB
# -----------------------------------------------------------------------------

CHROMA_COLLECTION_NAME = "example_collection"

# -----------------------------------------------------------------------------
# Models
# -----------------------------------------------------------------------------

LLM_MODEL = "google_genai:gemini-2.5-flash"
EMBEDDING_MODEL = "gemini-embedding-2-preview"

# -----------------------------------------------------------------------------
# Text Splitting
# -----------------------------------------------------------------------------

CHUNK_SIZE = 1000
CHUNK_OVERLAP = 200

# -----------------------------------------------------------------------------
# Retrieval
# -----------------------------------------------------------------------------

TOP_K = 8

# -----------------------------------------------------------------------------
# Initial Knowledge Source (Temporary)
# -----------------------------------------------------------------------------

DEFAULT_SOURCE_URL = (
    "https://lilianweng.github.io/posts/2023-06-23-agent/"
)

BS4_CLASSES = (
    "post-title",
    "post-header",
    "post-content",
)