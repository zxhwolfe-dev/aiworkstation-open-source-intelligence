"""Application factory for local tests and future MCP transports."""

from __future__ import annotations

from typing import Any, Mapping

from .providers import MockProjectIntelligenceProvider, ProjectIntelligenceProvider
from .tools import ToolRegistry


def create_default_registry(
    provider: ProjectIntelligenceProvider | None = None,
) -> ToolRegistry:
    """Build the M0 registry.

    The default provider is intentionally deterministic fixture data. A future
    production entrypoint must inject an explicit AI Workstation adapter rather
    than silently making network requests from this factory.
    """

    return ToolRegistry(provider or MockProjectIntelligenceProvider())


def invoke_tool(
    tool_name: str,
    arguments: Mapping[str, Any] | None = None,
    *,
    provider: ProjectIntelligenceProvider | None = None,
) -> dict[str, Any]:
    """Invoke one tool and return a JSON-serializable result envelope."""

    return create_default_registry(provider).invoke(tool_name, arguments).to_dict()
