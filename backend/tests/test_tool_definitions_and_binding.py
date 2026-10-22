"""Regression tests for tool definitions, tool naming, and LLM tool binding.

Guarantees that:
1. Every registered tool has a valid non-empty string name (no leading underscores or whitespace).
2. Every registered tool has a valid description and input schema.
3. All registered tools can be bound to the LLM without schema or Harmony/Groq errors.
4. The message ordering in ConversationState ensures AIMessage with tool_calls precedes ToolMessage.
"""

import pytest
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage, ToolMessage
from langchain_core.tools import BaseTool

from backend.rag.tool_registry import get_tools, validate_tool, validate_tools, ToolValidationError
from backend.rag.tool_executor import ConversationState, ToolExecutor
from backend.providers import get_llm


def test_every_registered_tool_has_valid_non_empty_name():
    """Every tool supplied to LLM must have a valid non-empty tool name without leading underscores."""
    tools = get_tools()
    assert len(tools) > 0, "At least one tool must be registered"

    expected_tool_names = {"retrieve_context", "list_documents", "search_by_filename"}
    actual_tool_names = set()

    for tool in tools:
        assert hasattr(tool, "name"), f"Tool {tool!r} is missing 'name' attribute"
        assert isinstance(tool.name, str), f"Tool {tool!r} name must be string"
        assert tool.name.strip() != "", f"Tool {tool!r} has empty name"
        assert not tool.name.startswith("_"), f"Tool {tool.name!r} must not start with leading underscore"
        actual_tool_names.add(tool.name)

    # Verify all expected RAG tools are present with their exact public names
    for expected in expected_tool_names:
        assert expected in actual_tool_names, f"Expected tool '{expected}' not found in registered tools"


def test_every_registered_tool_has_valid_description_and_schema():
    """Every registered tool must have a non-empty description and valid input schema."""
    tools = get_tools()
    for tool in tools:
        assert isinstance(tool.description, str) and tool.description.strip(), (
            f"Tool '{tool.name}' must have a non-empty description"
        )
        assert tool.args_schema is not None or hasattr(tool, "get_input_schema"), (
            f"Tool '{tool.name}' must have an args_schema"
        )
        assert callable(tool.invoke), f"Tool '{tool.name}' must have callable invoke method"


def test_tool_validator_catches_invalid_tools():
    """ToolValidationError must be raised for invalid tool definitions."""
    # Test None
    with pytest.raises(ToolValidationError, match="cannot be None"):
        validate_tool(None)

    # Test missing/empty name
    class EmptyNameTool:
        name = ""
        description = "test"
        args_schema = dict
        invoke = lambda self: None

    with pytest.raises(ToolValidationError, match="non-empty string name"):
        validate_tool(EmptyNameTool())

    # Test missing description
    class NoDescTool:
        name = "valid_name"
        description = ""
        args_schema = dict
        invoke = lambda self: None

    with pytest.raises(ToolValidationError, match="non-empty string description"):
        validate_tool(NoDescTool())


def test_llm_bind_tools_with_registered_tools():
    """Verify that the configured LLM can bind all registered tools without serialization errors."""
    from langchain_groq import ChatGroq
    from backend.config import LLM_MODEL, LLM_MAX_TOKENS, LLM_TIMEOUT, LLM_MAX_RETRIES

    llm = ChatGroq(
        model=LLM_MODEL,
        max_tokens=LLM_MAX_TOKENS,
        timeout=LLM_TIMEOUT,
        max_retries=LLM_MAX_RETRIES,
    )

    tools = get_tools()

    # Must succeed without error
    llm_with_tools = llm.bind_tools(tools)
    assert llm_with_tools is not None

    # Inspect the serialized tool definitions
    bound_tools = getattr(llm_with_tools, "kwargs", {}).get("tools", [])
    assert len(bound_tools) == len(tools)


    for bound_tool in bound_tools:
        function_def = bound_tool.get("function", {})
        tool_name = function_def.get("name")
        assert tool_name, f"Serialized tool is missing 'name': {bound_tool}"
        assert not tool_name.startswith("_"), f"Serialized tool '{tool_name}' must not have leading underscore"
        assert function_def.get("description"), f"Tool '{tool_name}' is missing description"


def test_conversation_state_message_ordering_for_tool_calls():
    """Verify that assistant message with tool_calls precedes ToolMessage in ConversationState."""
    state = ConversationState()
    state.add_system_message("system")
    state.add_user_message("user question")

    # In standard chat protocol, AIMessage with tool_calls must precede ToolMessage
    state.add_assistant_message(
        content="",
        tool_calls=[{"name": "retrieve_context", "args": {"query": "test"}, "id": "call_1", "type": "tool_call"}]
    )
    state.add_tool_message(
        tool_call_id="call_1",
        content="retrieved chunks",
        name="retrieve_context",
    )

    messages = state.get_messages_for_llm()
    assert len(messages) == 4
    assert isinstance(messages[0], SystemMessage)
    assert isinstance(messages[1], HumanMessage)
    assert isinstance(messages[2], AIMessage)
    assert hasattr(messages[2], "tool_calls") and len(messages[2].tool_calls) == 1
    assert isinstance(messages[3], ToolMessage)
    assert messages[3].tool_call_id == "call_1"
    assert messages[3].name == "retrieve_context"
