"""Dependency-free validation for MCP endpoint URLs used by release tooling."""

from __future__ import annotations

from urllib.parse import urlparse

LOCAL_MCP_HOSTS = {"localhost", "127.0.0.1", "::1"}


def validate_mcp_endpoint(url: str, *, allow_http_localhost: bool) -> str:
    """Validate this product's canonical credential-free MCP endpoint URL.

    Release/readiness tooling imports this module without importing the optional
    MCP SDK. Real client code can therefore share exactly the same URL policy
    while the base package remains usable without ``.[mcp]``.
    """

    value = str(url or "").strip()
    parsed = urlparse(value)
    if parsed.scheme not in {"http", "https"}:
        raise ValueError("MCP endpoint must use http or https")
    if parsed.username or parsed.password:
        raise ValueError("MCP endpoint URL must not contain credentials")
    if parsed.query or parsed.fragment:
        raise ValueError("MCP endpoint URL must not contain query or fragment")
    if not parsed.hostname:
        raise ValueError("MCP endpoint hostname is required")
    if parsed.path not in {"/mcp", "/mcp/"}:
        raise ValueError("MCP endpoint path must be /mcp for this product")
    local = parsed.hostname.lower() in LOCAL_MCP_HOSTS
    if parsed.scheme != "https" and not (allow_http_localhost and local):
        raise ValueError("Remote MCP endpoints must use HTTPS; HTTP is allowed only for localhost")
    try:
        port = parsed.port
    except ValueError as exc:
        raise ValueError("MCP endpoint contains an invalid port") from exc
    if port is not None and not 1 <= port <= 65535:
        raise ValueError("MCP endpoint port must be between 1 and 65535")
    return value.rstrip("/")
