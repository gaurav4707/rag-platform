from langchain.agents import create_agent
from langchain.chat_models import init_chat_model
from config import LLM_MODEL
from rag.retriever import retrieve_context
from rag.prompts import prompt_with_context

model = init_chat_model(LLM_MODEL)
def build_agent():
    return create_agent(model, tools=[retrieve_context], middleware=[prompt_with_context])