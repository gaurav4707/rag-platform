from backend.rag import agent
from backend.models.rag_models import ChatResult


class RAGService:
    def stream_answer(self, query: str):
        return agent.stream_events(query)

    def invoke(self, query: str) -> ChatResult:
        return agent.invoke(query)
