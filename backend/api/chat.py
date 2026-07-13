import json
import uuid
from typing import AsyncGenerator

from fastapi import APIRouter, Request
from fastapi.responses import StreamingResponse

from backend.models.schemas import ChatRequest, ChatResponse, SourceItem
from backend.services.rag_service import RAGService
from backend.utils.performance import StreamPerformanceTracker

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
async def chat_stream(request: ChatRequest, http_request: Request):
    """Stream chat response with performance tracking.

    Timing starts immediately when the endpoint receives the request.
    TTFT is measured when the first token is yielded.
    Total duration is measured when the generator completes.
    """
    request_id = str(uuid.uuid4())[:8]
    tracker = StreamPerformanceTracker(request_id=request_id)
    tracker.start()

    async def event_generator() -> AsyncGenerator[str, None]:
        stream = rag_service.stream_answer(request.message)
        tool_calls: list[dict] = []
        retrieval_result = None
        first_token = True

        try:
            async for kind, item in stream:
                # Check for client disconnection
                if await http_request.is_disconnected():
                    tracker.finish_cancelled()
                    return

                if kind == "messages":
                    token = getattr(item, "text", "")
                    if token:
                        if first_token:
                            tracker.mark_first_token()
                            first_token = False
                        tracker.increment_chunks()
                        yield f"data: {json.dumps({'token': token})}\n\n"
                elif kind == "tool_calls":
                    tool_name = getattr(item, "tool_name", "")
                    tool_input = getattr(item, "input", None)
                    tool_output = getattr(item, "output", None)
                    artifact = getattr(item, "artifact", None)

                    tool_calls.append(
                        {
                            "tool_name": tool_name,
                            "input": tool_input,
                            "output": tool_output,
                        }
                    )
                    if tool_name == "retrieve_context" and artifact:
                        retrieval_result = artifact

            # Check for client disconnection before sending final event
            if await http_request.is_disconnected():
                tracker.finish_cancelled()
                return

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

            tracker.finish_success()

        except Exception as e:
            tracker.finish_error(e)
            raise

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
    )