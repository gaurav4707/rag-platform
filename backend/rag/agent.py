from langchain.agents import create_agent
from langchain_groq import ChatGroq

from backend.config import LLM_MODEL
from backend.models.rag_models import ChatResult
from backend.rag.tool_registry import get_tools
from backend.rag.prompts import system_prompt
from backend.rag.citations import build_sources


def _build_agent():
    llm = ChatGroq(
        model=LLM_MODEL,
        max_tokens=None,
        reasoning_format="parsed",
        timeout=None,
        max_retries=2,
    )
    return create_agent(llm, tools=get_tools(), middleware=[system_prompt])



_agent = None


def _get_agent():
    global _agent
    if _agent is None:
        _agent = _build_agent()
    return _agent


def invoke(question: str) -> ChatResult:
    agent_instance = _get_agent()
    result = agent_instance.invoke(
        {"messages": [{"role": "user", "content": question}]}
    )

    messages = result.get("messages", [])
    answer = messages[-1].content if messages else ""

    retrieval_result = None
    for msg in messages:
        if msg.type == "tool" and msg.name == "retrieve_context":
            if hasattr(msg, "artifact") and msg.artifact:
                retrieval_result = msg.artifact
                break

    tool_calls = []
    for msg in messages:
        if hasattr(msg, "tool_calls") and msg.tool_calls:
            for tc in msg.tool_calls:
                tool_calls.append({
                    "tool_name": tc.get("name", "unknown"),
                    "input": tc.get("args", {}),
                    "output": tc.get("output", ""),
                })

    sources = []
    if retrieval_result:
        sources = build_sources(retrieval_result)

    return ChatResult(
        answer=answer,
        sources=sources,
        tool_calls=tool_calls,
    )


def stream_events(question: str):
    agent_instance = _get_agent()
    return agent_instance.stream_events(
        {"messages": [{"role": "user", "content": question}]},
        version="v3",
    )
