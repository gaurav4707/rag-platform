from langchain_text_splitters import RecursiveCharacterTextSplitter
from backend.config import CHUNK_OVERLAP
from backend.config import CHUNK_SIZE

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