from backend.rag.agent import build_agent


class RAGService:
    def __init__(self):
        self.agent = build_agent()

    def stream_answer(self, query: str):
        """
        Stream the agent's response for a user query.
        """
        return self.agent.stream_events(
            {"messages": [{"role": "user", "content": query}]},
            version="v3",
        )