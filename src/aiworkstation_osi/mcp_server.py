"""MCP transport for the six read-only Open Source Intelligence tools.

Install the optional dependency with ``python -m pip install -e '.[mcp]'``.
The server uses deterministic mock data unless ``OSI_PROVIDER=http`` is set.
"""

from __future__ import annotations

from typing import Any, Literal

from mcp.server import MCPServer

from .app import create_registry_from_env
from .errors import ToolError
from .tools import ToolRegistry


def _invoke(registry: ToolRegistry, tool_name: str, arguments: dict[str, Any]) -> dict[str, Any]:
    try:
        return registry.invoke(tool_name, arguments).to_dict()
    except ToolError as exc:
        # MCP SDK v2 converts tool exceptions into model-readable tool errors.
        # Only stable public code/message text is forwarded.
        raise ValueError(f"{exc.code}: {exc.message}") from None


def build_mcp_server(registry: ToolRegistry | None = None) -> MCPServer:
    """Build an in-memory-testable MCP server without starting a transport."""

    active_registry = registry or create_registry_from_env()
    server = MCPServer("AI Workstation Open Source Intelligence")

    @server.tool()
    def search_ai_projects(
        query: str,
        constraints: dict[str, Any] | None = None,
        locale: Literal["zh", "en"] = "en",
        source_mode: Literal["required", "preferred", "off"] = "required",
        request_id: str = "",
    ) -> dict[str, Any]:
        """Find and verify open-source AI projects from explicit requirements."""

        return _invoke(
            active_registry,
            "search_ai_projects",
            {
                "query": query,
                "constraints": constraints or {},
                "locale": locale,
                "source_mode": source_mode,
                "request_id": request_id,
            },
        )

    @server.tool()
    def get_project_facts(
        project_id: str,
        locale: Literal["zh", "en"] = "en",
        request_id: str = "",
    ) -> dict[str, Any]:
        """Get current evidence-backed public facts for one project."""

        return _invoke(
            active_registry,
            "get_project_facts",
            {"project_id": project_id, "locale": locale, "request_id": request_id},
        )

    @server.tool()
    def get_license_evidence(
        project_id: str,
        locale: Literal["zh", "en"] = "en",
        request_id: str = "",
    ) -> dict[str, Any]:
        """Get observed license evidence; the result is not legal advice."""

        return _invoke(
            active_registry,
            "get_license_evidence",
            {"project_id": project_id, "locale": locale, "request_id": request_id},
        )

    @server.tool()
    def compare_ai_projects(
        project_ids: list[str],
        criteria: list[str] | None = None,
        context: dict[str, Any] | None = None,
        locale: Literal["zh", "en"] = "en",
        request_id: str = "",
    ) -> dict[str, Any]:
        """Compare two to five projects in one explicit decision context."""

        return _invoke(
            active_registry,
            "compare_ai_projects",
            {
                "project_ids": project_ids,
                "criteria": criteria or [],
                "context": context or {},
                "locale": locale,
                "request_id": request_id,
            },
        )

    @server.tool()
    def find_alternatives(
        project_id: str,
        constraints: dict[str, Any] | None = None,
        locale: Literal["zh", "en"] = "en",
        request_id: str = "",
    ) -> dict[str, Any]:
        """Find verified candidate alternatives while preserving constraints."""

        return _invoke(
            active_registry,
            "find_alternatives",
            {
                "project_id": project_id,
                "constraints": constraints or {},
                "locale": locale,
                "request_id": request_id,
            },
        )

    @server.tool()
    def compose_ai_stack(
        business_goal: str,
        constraints: dict[str, Any] | None = None,
        existing_stack: list[str] | None = None,
        locale: Literal["zh", "en"] = "en",
        request_id: str = "",
    ) -> dict[str, Any]:
        """Compose a candidate open-source AI stack and expose unknown compatibility."""

        return _invoke(
            active_registry,
            "compose_ai_stack",
            {
                "business_goal": business_goal,
                "constraints": constraints or {},
                "existing_stack": existing_stack or [],
                "locale": locale,
                "request_id": request_id,
            },
        )

    return server


mcp = build_mcp_server()


def main() -> None:
    """Run the local stdio transport used by Codex and other MCP hosts."""

    mcp.run()


if __name__ == "__main__":
    main()
