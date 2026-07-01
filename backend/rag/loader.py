from langchain_community.document_loaders import PyPDFLoader
from langchain_core.documents import Document


def load_pdf(file_path: str) -> list[Document]:
    """Load a PDF document from the filesystem and return pages as Documents."""
    loader = PyPDFLoader(file_path)
    return loader.load()