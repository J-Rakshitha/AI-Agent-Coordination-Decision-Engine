"""
Tool Registry — Milestone 2: "Develop custom enterprise tools and API connectors"
====================================================================================
A single, explicit catalog every tool an agent is allowed to invoke. Each
`Tool` wraps an existing agent capability behind a uniform interface
(name, description, keywords, async handler), so:

  - New tools can be added in one place without touching the selection or
    execution logic.
  - The Tool Selector Agent can reason about *which* tool to use just from
    each tool's name/description/keywords — it doesn't need to know how
    any tool is implemented internally.
"""
from dataclasses import dataclass, field
from typing import Any, Awaitable, Callable


@dataclass
class Tool:
    name: str
    description: str
    keywords: list[str]  # used by the rule-based fallback selector
    handler: Callable[..., Awaitable[dict]]  # async fn(db, **kwargs) -> {"success": bool, "output": ...}


TOOL_REGISTRY: dict[str, "Tool"] = {}


def register_tool(tool: Tool) -> None:
    TOOL_REGISTRY[tool.name] = tool


def get_tool(name: str) -> Tool | None:
    return TOOL_REGISTRY.get(name)


def list_tools() -> list[Tool]:
    return list(TOOL_REGISTRY.values())


def list_tools_public() -> list[dict]:
    """Serializable view for the API layer (no function objects)."""
    return [
        {"name": t.name, "description": t.description, "keywords": t.keywords}
        for t in TOOL_REGISTRY.values()
    ]
