from backend.rag.retriever import retrieve_context


def get_tools() -> list:
    return [retrieve_context]
