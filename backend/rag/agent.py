from langchain.agents import create_agent
from langchain.chat_models import init_chat_model
from config import LLM_MODEL
from rag.retriever import retrieve_context
from rag.prompts import prompt_with_context
from langchain_groq import ChatGroq

def build_agent():
    llm = ChatGroq(
        model=LLM_MODEL,
        max_tokens=None,
        reasoning_format="parsed",
        timeout=None,
        max_retries=2,
    )
    return create_agent(llm, tools=[retrieve_context], middleware=[prompt_with_context])    