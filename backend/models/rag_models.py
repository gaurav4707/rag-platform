from dataclasses import dataclass
from typing import Optional
from langchain_core.documents import Document


@dataclass
class RetrievedChunk:
    document: Document
    score: float


@dataclass
class RetrievalResult:
    query: str
    chunks: list[RetrievedChunk]


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