from __future__ import annotations

from dataclasses import dataclass, field

from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter

from backend.config import CHUNK_OVERLAP, CHUNK_SIZE, PARENT_CHUNK_OVERLAP, PARENT_CHUNK_SIZE

# Separators ordered by preference for logical text boundaries in PDF documents:
# 1. Double newlines (paragraph breaks)
# 2. Single newlines (line breaks)
# 3. Markdown headings (with and without leading newline for document start)
# 4. Numbered list items
# 5. Common document structure keywords (CHAPTER, SECTION, PART, APPENDIX)
# 6. Sentence endings (period, question, exclamation followed by space)
# 7. Clause boundaries (semicolon, colon)
# 8. Word boundaries (space)
# 9. Character level (fallback)
SEPARATORS = [
    "\n\n",
    "\n",
    "\n# ",
    "\n## ",
    "\n### ",
    "\n#### ",
    "# ",
    "## ",
    "### ",
    "#### ",
    "\n1. ",
    "\n2. ",
    "\n3. ",
    "\n4. ",
    "\n5. ",
    "\n6. ",
    "\n7. ",
    "\n8. ",
    "\n9. ",
    "\n0. ",
    "1. ",
    "2. ",
    "3. ",
    "4. ",
    "5. ",
    "6. ",
    "7. ",
    "8. ",
    "9. ",
    "0. ",
    "\nCHAPTER ",
    "\nChapter ",
    "\nSection ",
    "\nSECTION ",
    "\nPart ",
    "\nPART ",
    "\nAppendix ",
    "\nAPPENDIX ",
    "CHAPTER ",
    "Chapter ",
    "Section ",
    "SECTION ",
    "Part ",
    "PART ",
    "Appendix ",
    "APPENDIX ",
    ". ",
    "? ",
    "! ",
    "; ",
    ": ",
    " ",
    "",
]

text_splitter = RecursiveCharacterTextSplitter(
    chunk_size=CHUNK_SIZE,
    chunk_overlap=CHUNK_OVERLAP,
    add_start_index=True,
    separators=SEPARATORS,
)

parent_text_splitter = RecursiveCharacterTextSplitter(
    chunk_size=PARENT_CHUNK_SIZE,
    chunk_overlap=PARENT_CHUNK_OVERLAP,
    add_start_index=True,
    separators=SEPARATORS,
)


@dataclass
class HierarchicalSplitResult:
    parent_blocks: list[Document] = field(default_factory=list)
    child_chunks: list[Document] = field(default_factory=list)


class HierarchicalSplitter:
    """Creates parent blocks then splits each into child chunks.

    Parent blocks are larger chunks suitable for providing broader context.
    Child chunks are smaller, embedded, and used for retrieval.
    Maintains parent-child mapping through metadata on child chunks.

    Future adaptive chunking should extend this class.
    """

    def __init__(
        self,
        parent_splitter: RecursiveCharacterTextSplitter | None = None,
        child_splitter: RecursiveCharacterTextSplitter | None = None,
        document_id: str = "",
        filename: str = "",
        file_hash: str = "",
    ):
        self.parent_splitter = parent_splitter or parent_text_splitter
        self.child_splitter = child_splitter or text_splitter
        self.document_id = document_id
        self.filename = filename
        self.file_hash = file_hash

    def split(self, page_docs: list[Document]) -> HierarchicalSplitResult:
        parent_blocks = self.parent_splitter.split_documents(page_docs)

        for pi, parent in enumerate(parent_blocks):
            tracked_parent_id = f"{self.document_id}_parent_{pi}"
            parent.metadata["parent_id"] = tracked_parent_id
            parent.metadata["document_id"] = self.document_id
            parent.metadata["filename"] = self.filename
            parent.metadata["file_hash"] = self.file_hash

        child_chunks: list[Document] = []
        for pi, parent in enumerate(parent_blocks):
            parent_id = parent.metadata["parent_id"]
            start_page = parent.metadata.get("page")
            end_page = start_page

            children = self.child_splitter.split_documents([parent])
            for ci, child in enumerate(children):
                child.metadata["document_id"] = self.document_id
                child.metadata["filename"] = self.filename
                child.metadata["file_hash"] = self.file_hash
                child.metadata["parent_id"] = parent_id
                child.metadata["parent_page_range_start"] = start_page
                child.metadata["parent_page_range_end"] = end_page
                child.metadata["parent_child_index"] = ci
                child.metadata["chunk_index"] = len(child_chunks)
                child_chunks.append(child)

        return HierarchicalSplitResult(
            parent_blocks=parent_blocks,
            child_chunks=child_chunks,
        )