import json

from fastapi import APIRouter
from fastapi.responses import StreamingResponse

from backend.models.schemas import ChatRequest, ChatResponse, SourceItem
from backend.services.rag_service import RAGService

router = APIRouter(tags=["chat"])
rag_service = RAGService()


@router.post("/chat", response_model=ChatResponse)
def chat(request: ChatRequest):
    result = rag_service.invoke(request.message)
    return ChatResponse(
        answer=result.answer,
        sources=[SourceItem(**s.__dict__) for s in result.sources],
        tool_calls=result.tool_calls,
    )


@router.post("/chat/stream")
def chat_stream(request: ChatRequest):
    return StreamingResponse(
        _stream_events(request.message),
        media_type="text/event-stream",
    )


def _stream_events(message: str):
    stream = rag_service.stream_answer(message)
    tool_calls: list[dict] = []
    retrieval_result = None

    for kind, item in stream.interleave("messages", "tool_calls"):
        if kind == "messages":
            for token in item.text:
                yield f"data: {json.dumps({'token': token})}\n\n"
        elif kind == "tool_calls":
            tool_calls.append(
                {
                    "tool_name": item.tool_name,
                    "input": item.input,
                    "output": item.output,
                }
            )
            # Check if this is a retrieve_context tool call with artifact
            if item.tool_name == "retrieve_context" and hasattr(item, "artifact") and item.artifact:
                retrieval_result = item.artifact

    # Build sources from retrieval result
    sources = []
    if retrieval_result:
        from backend.rag.citations import build_sources
        sources = build_sources(retrieval_result)

    final = {
        "done": True,
        "sources": [s.__dict__ for s in sources],
        "tool_calls": tool_calls,
    }
    yield f"data: {json.dumps(final)}\n\n"