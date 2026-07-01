import bs4

from langchain_chroma import Chroma

from config import (
    BS4_CLASSES,
    CHROMA_COLLECTION_NAME,
    CHROMA_DB_DIR,
    DEFAULT_SOURCE_URL,
)
from rag.embeddings import embeddings
from rag.loader import load_web_page
from rag.splitter import text_splitter


bs4_strainer = bs4.filter.SoupStrainer(class_=BS4_CLASSES)


def get_vector_store():
    """Return the Chroma vector store."""

    return Chroma(
        collection_name=CHROMA_COLLECTION_NAME,
        embedding_function=embeddings,
        persist_directory=str(CHROMA_DB_DIR),
    )


def index_documents():
    """Load, split and index documents."""

    vector_store = get_vector_store()

    # Clear existing data to avoid duplicates during development
    vector_store.delete_collection()
    vector_store = get_vector_store()

    docs = load_web_page(
        DEFAULT_SOURCE_URL,
        bs_kwargs={"parse_only": bs4_strainer},
    )

    splits = text_splitter.split_documents(docs)

    vector_store.add_documents(splits)

    print(f"Indexed {len(splits)} chunks.")