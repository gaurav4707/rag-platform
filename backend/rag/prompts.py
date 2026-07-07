from langchain.agents.middleware import ModelRequest, dynamic_prompt


@dynamic_prompt
def system_prompt(request: ModelRequest) -> str:
    """System prompt for the RAG agent."""
    return (
        "You are a helpful assistant that answers questions using the retrieve_context tool. "
        "You MUST use the retrieve_context tool to find relevant information before answering. "
        "Only use information from the tool results to answer. "
        "If the tool returns no relevant information, say 'I don't know'."
    )