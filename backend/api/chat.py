from fastapi import APIRouter
from models.schemas import ChatRequest, ChatResponse
from services.rag_service import RAGService

router = APIRouter(tags=["chat"])
rag_service = RAGService()


@router.post("/chat", response_model=ChatResponse)
def chat(request: ChatRequest):
    stream = rag_service.stream_answer(request.message)
    answer = ""
    tool_calls: list[dict] = []
    for kind, item in stream.interleave("messages", "tool_calls"):
        if kind == "messages":
            for token in item.text:
                answer += token
        elif kind == "tool_calls":
            tool_calls.append(
                {
                    "tool_name": item.tool_name,
                    "input": item.input,
                    "output": item.output,
                }
            )
    return ChatResponse(answer=answer, tool_calls=tool_calls)
