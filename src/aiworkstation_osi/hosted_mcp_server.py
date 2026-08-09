"""Hosted MCP builder for the public nine-tool data/evidence surface.

The current product intentionally contains no runnable server-side AI model,
Premium, credits, checkout or OAuth entitlement path. Natural-language reasoning
belongs to the MCP host model; AI Workstation supplies current public Radar data.
"""

from __future__ import annotations

from typing import Any

from mcp.server import MCPServer

from .app import create_registry_from_env
from .mcp_server import SERVER_INSTRUCTIONS, build_mcp_server
from .tools import ToolRegistry

PUBLIC_HOSTED_INSTRUCTIONS = SERVER_INSTRUCTIONS + (
    " This Hosted product exposes exactly the nine standard read-only Radar tools without requiring login. "
    "AI Workstation is a data/evidence provider on this path: do not request publisher-model or server-side AI execution. "
    "There is no Premium model tool, subscription/credit tool or checkout tool in this release. "
    "Public gateway abuse controls apply independently of the tool contracts."
)

# Kept as an import-compatible name for older local code/tests. It has the same
# data-only semantics as PUBLIC_HOSTED_INSTRUCTIONS and does not enable Premium.
HOSTED_INSTRUCTIONS = PUBLIC_HOSTED_INSTRUCTIONS


def build_public_hosted_mcp_server(
    registry: ToolRegistry | None = None,
) -> MCPServer:
    """Build the anonymous Hosted surface with exactly nine read-only Radar tools."""

    return build_mcp_server(
        registry or create_registry_from_env(),
        instructions=PUBLIC_HOSTED_INSTRUCTIONS,
    )


def build_hosted_mcp_server(
    registry: ToolRegistry | None = None,
    **unsupported_options: Any,
) -> MCPServer:
    """Backward-compatible builder that now enforces the data-only product.

    OAuth/Premium builder options are rejected instead of silently re-enabling a
    server-model path.
    """

    if unsupported_options:
        names = ", ".join(sorted(unsupported_options))
        raise ValueError(
            "OAuth/Premium Hosted options are disabled in the data-only release: " + names
        )
    return build_public_hosted_mcp_server(registry)
