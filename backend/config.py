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

MAX_FILE_SIZE = 50 * 1024 * 1024  # 50 MB

# -----------------------------------------------------------------------------
# ChromaDB
# -----------------------------------------------------------------------------

CHROMA_COLLECTION_NAME = "example_collection"

# -----------------------------------------------------------------------------
# Provider Selection
# -----------------------------------------------------------------------------

# Embedding Provider
EMBEDDING_PROVIDER = "huggingface"
EMBEDDING_MODEL = "BAAI/bge-base-en-v1.5"
EMBEDDING_LOCAL_FILES_ONLY = True

# LLM Provider
LLM_PROVIDER = "groq"
LLM_MODEL = "llama-3.1-8b-instant"
LLM_MAX_TOKENS = None
LLM_TIMEOUT = None
LLM_MAX_RETRIES = 2

# -----------------------------------------------------------------------------
# Text Splitting
# -----------------------------------------------------------------------------

CHUNK_SIZE = 1000
CHUNK_OVERLAP = 200

# -----------------------------------------------------------------------------
# Retrieval
# -----------------------------------------------------------------------------

TOP_K = 4

# -----------------------------------------------------------------------------
# Agent Tool Execution Safety Limits
# -----------------------------------------------------------------------------

# Maximum number of tool execution iterations (prevents infinite loops)
MAX_TOOL_ITERATIONS = 10

# Maximum number of tool calls allowed in a single LLM response
MAX_TOOLS_PER_RESPONSE = 5