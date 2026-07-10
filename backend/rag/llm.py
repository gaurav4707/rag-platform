from langchain_groq import ChatGroq

def get_llm() -> ChatGroq:
    return ChatGroq(
        model="llama-3.1-8b-instant",
        max_tokens=None,
        timeout=None,
        max_retries=2,
    )