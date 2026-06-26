from langchain_text_splitters import RecursiveCharacterTextSplitter
from config import CHUNK_OVERLAP
from config import CHUNK_SIZE

text_splitter = RecursiveCharacterTextSplitter(
    chunk_size=CHUNK_SIZE,  # chunk size (characters)
    chunk_overlap=CHUNK_OVERLAP,  # chunk overlap (characters)
    add_start_index=True,  # track index in original document
)