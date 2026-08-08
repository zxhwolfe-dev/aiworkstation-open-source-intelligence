"""Application factories for local, HTTP-provider and MCP entrypoints."""

from __future__ import annotations

import os
from typing import Any, Mapping

from .full_radar_provider import FullRadarHttpProvider
from .full_tools import FullToolRegistry
from .http_provider import DEFAULT_BASE_URL
from .providers import MockProjectIntelligenceProvider, ProjectIntelligenceProvider


def create_default_registry(
    provider: ProjectIntelligenceProvider | None = None,
) -> FullToolRegistry:
    """Build a registry without implicit network access.

    The default remains deterministic fixture data. Production and integration
    entrypoints must inject a provider or explicitly opt into the HTTP provider.
    """

    return FullToolRegistry(provider or MockProjectIntelligenceProvider())


def create_registry_from_env() -> FullToolRegistry:
    """Create a registry from explicit environment configuration.

    Supported values:

    - ``OSI_PROVIDER=mock`` (default): deterministic, offline fixture data.
    - ``OSI_PROVIDER=http``: hardened public AI Workstation Radar HTTP adapter.
    """

    provider_name = os.getenv("OSI_PROVIDER", "mock").strip().lower()
    if provider_name == "mock":
        return create_default_registry()
    if provider_name == "http":
        base_url = os.getenv("AIWORKSTATION_RADAR_BASE_URL", DEFAULT_BASE_URL).strip()
        try:
            timeout = float(os.getenv("OSI_HTTP_TIMEOUT_SECONDS", "30"))
            hydrate_limit = int(os.getenv("OSI_HYDRATE_LIMIT", "5"))
        except ValueError as exc:
            raise ValueError("OSI HTTP timeout and hydrate limit must be numeric") from exc
        if timeout <= 0 or timeout > 240:
            raise ValueError("OSI_HTTP_TIMEOUT_SECONDS must be greater than 0 and no more than 240")
        if hydrate_limit < 1 or hydrate_limit > 5:
            raise ValueError("OSI_HYDRATE_LIMIT must be between 1 and 5")
        return create_default_registry(
            FullRadarHttpProvider(
                base_url,
                timeout=timeout,
                hydrate_limit=hydrate_limit,
            )
        )
    raise ValueError("OSI_PROVIDER must be either 'mock' or 'http'")


def invoke_tool(
    tool_name: str,
    arguments: Mapping[str, Any] | None = None,
    *,
    provider: ProjectIntelligenceProvider | None = None,
) -> dict[str, Any]:
    """Invoke one tool and return a JSON-serializable result envelope."""

    return create_default_registry(provider).invoke(tool_name, arguments).to_dict()
