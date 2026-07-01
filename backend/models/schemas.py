from pydantic import BaseModel

class ChatRequest(BaseModel):
    message: str

class ChatResponse(BaseModel):
    answer: str
    tool_calls: list[dict] | None = None

class HealthResponse(BaseModel):
    status: str


class UploadResponse(BaseModel):
    document_id: str
    filename: str
    status: str