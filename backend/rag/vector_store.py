import os
import bs4
from config import DEFAULT_SOURCE_URL
from langchain_chroma import Chroma
from rag.loader import load_web_page
from rag.embeddings import embeddings
from rag.splitter import text_splitter
from config import BS4_CLASSES
from config import CHROMA_DB_DIR, CHROMA_COLLECTION_NAME

bs4_strainer = bs4.SoupStrainer(class_=BS4_CLASSES)
def get_vector_store():
    vector_store = Chroma(
    collection_name=CHROMA_COLLECTION_NAME,
    embedding_function=embeddings,
    persist_directory=str(CHROMA_DB_DIR),
    )
    docs = load_web_page(
        DEFAULT_SOURCE_URL,
        bs_kwargs={"parse_only": bs4_strainer}
    )
    all_splits = text_splitter.split_documents(docs)
    
    vector_store.add_documents(all_splits)
    print(f"Indexed {len(all_splits)} chunks.")
    return vector_store