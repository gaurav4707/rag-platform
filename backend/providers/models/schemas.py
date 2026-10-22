from pydantic import BaseModel
from typing import Optional


class ChatRequest(BaseModel):
    message: str


class SourceItem(BaseModel):
    document: str
    page: Optional[int] = None
    document_id: str
    score: Optional[float] = None


class ChatResponse(BaseModel):
    answer: str
    sources: list[SourceItem] = []
    tool_calls: list[dict] | None = None


class HealthResponse(BaseModel):
    status: str


class UploadResponse(BaseModel):
    document_id: str
    filename: str
    status: str
    already_indexed: bool = False


class DocumentListItem(BaseModel):
    document_id: str
    filename: str
    status: str = "indexed"


class DeleteResponse(BaseModel):
    status: str
