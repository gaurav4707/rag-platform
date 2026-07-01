from fastapi import APIRouter

from models.schemas import ChatRequest, ChatResponse, SourceItem
from services.rag_service import RAGService
from rag.vector_store import similarity_search_with_scores

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

    sources = _build_sources(request.message)
    return ChatResponse(answer=answer, sources=sources, tool_calls=tool_calls)


def _build_sources(query: str) -> list[SourceItem]:
    """Build source citations from retrieved documents."""
    results = similarity_search_with_scores(query, k=4)
    sources = []
    for doc, distance in results:
        meta = doc.metadata
        sources.append(
            SourceItem(
                document=meta.get("filename", "unknown"),
                page=meta.get("page"),
                document_id=meta.get("document_id", ""),
                score=round(distance, 4) if distance is not None else None,
            )
        )
    return sources
