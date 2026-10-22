"""Tool Registry for the Agentic RAG system.

Registers, validates, and exposes available tools to the Agent.
"""

import logging
from typing import Any

from langchain_core.tools import BaseTool

from backend.rag.tools import get_tools as _get_tools

logger = logging.getLogger(__name__)


class ToolValidationError(ValueError):
    """Raised when a registered tool fails validation."""
    pass


def validate_tool(tool: Any) -> None:
    """Validate that a registered tool meets all structural and execution requirements.

    Ensures:
    1. Tool is not None.
    2. Has a non-empty string name.
    3. Has a non-empty string description.
    4. Has a valid input schema (args_schema or get_input_schema).
    5. Has a callable execution implementation.
    """
    if tool is None:
        raise ToolValidationError("Registered tool cannot be None.")

    name = getattr(tool, "name", None)
    if not isinstance(name, str) or not name.strip():
        raise ToolValidationError(
            f"Tool {tool!r} must have a non-empty string name, got {name!r}."
        )

    description = getattr(tool, "description", None)
    if not isinstance(description, str) or not description.strip():
        raise ToolValidationError(
            f"Tool '{name}' must have a non-empty string description, got {description!r}."
        )

    args_schema = getattr(tool, "args_schema", None)
    if args_schema is None and not hasattr(tool, "get_input_schema"):
        raise ToolValidationError(
            f"Tool '{name}' must have a valid input schema (args_schema)."
        )

    if not (
        callable(getattr(tool, "invoke", None))
        or callable(getattr(tool, "_run", None))
        or callable(getattr(tool, "func", None))
    ):
        raise ToolValidationError(
            f"Tool '{name}' must have a callable execution implementation."
        )


def validate_tools(tools: list[Any]) -> list[Any]:
    """Validate a list of tools and return them."""
    for tool in tools:
        validate_tool(tool)
    return tools


def get_tools() -> list[BaseTool]:
    """Return all registered tools after validation."""
    tools = _get_tools()
    return validate_tools(tools)