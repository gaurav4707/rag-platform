from dataclasses import dataclass, field
from typing import Optional
from langchain_core.documents import Document


@dataclass
class RetrievedChunk:
    document: Document
    score: float


@dataclass
class RetrievalResult:
    original_query: str
    retrieval_query: str
    chunks: list[RetrievedChunk]
    retrieval_metadata: dict = field(default_factory=dict)


@dataclass
class SourceItem:
    document: str
    page: Optional[int] = None
    document_id: str = ""
    score: Optional[float] = None


@dataclass
class ChatResult:
    answer: str
    sources: list[SourceItem]
    tool_calls: list[dict]