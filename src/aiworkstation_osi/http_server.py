"""Guarded Streamable HTTP entrypoint for private and hosted alpha testing.

This module intentionally does not make the service public-safe by itself.
Non-loopback binds require an explicit operator acknowledgement and the live HTTP
provider. Authentication, TLS termination, rate limiting and abuse controls
remain the responsibility of the trusted reverse proxy until native OAuth is
implemented.
"""

from __future__ import annotations

import argparse
import ipaddress
import json
import os
import socket
from dataclasses import asdict, dataclass
from typing import Sequence
from urllib.parse import urlparse

from .http_provider import DEFAULT_BASE_URL
from .mcp_server import build_mcp_server

PUBLIC_BIND_ACK = "reverse-proxy-or-private-network"
ALLOWED_RADAR_HOSTS = {"aiworkstation.cn", "useaistation.com"}


def _env_bool(name: str, default: bool = False) -> bool:
    raw = os.getenv(name)
    if raw is None:
        return default
    normalized = raw.strip().lower()
    if normalized in {"1", "true", "yes", "on"}:
        return True
    if normalized in {"0", "false", "no", "off"}:
        return False
    raise ValueError(f"{name} must be a boolean value")


def _is_loopback_host(host: str) -> bool:
    normalized = host.strip().lower()
    if normalized in {"localhost", "ip6-localhost"}:
        return True
    try:
        return ipaddress.ip_address(normalized).is_loopback
    except ValueError:
        pass

    # Hostnames are treated conservatively. Only names resolving exclusively to
    # loopback addresses qualify as a local bind.
    try:
        addresses = {
            item[4][0]
            for item in socket.getaddrinfo(normalized, None, type=socket.SOCK_STREAM)
        }
    except OSError:
        return False
    if not addresses:
        return False
    try:
        return all(ipaddress.ip_address(address).is_loopback for address in addresses)
    except ValueError:
        return False


def _validate_live_radar_origin(base_url: str) -> str:
    parsed = urlparse(base_url.rstrip("/"))
    if parsed.scheme != "https":
        raise ValueError("Public-bind HTTP mode requires an HTTPS Radar origin")
    if parsed.hostname not in ALLOWED_RADAR_HOSTS:
        raise ValueError(
            "Public-bind HTTP mode requires an allow-listed AI Workstation Radar origin"
        )
    if parsed.username or parsed.password or parsed.query or parsed.fragment:
        raise ValueError("Radar origin must not contain credentials, query, or fragment")
    if parsed.path not in {"", "/"}:
        raise ValueError("Radar origin must be an origin without a path")
    if parsed.port not in {None, 443}:
        raise ValueError("Public-bind Radar origin must use the standard HTTPS port")
    return base_url.rstrip("/")


@dataclass(frozen=True, slots=True)
class HttpServerSettings:
    host: str
    port: int
    provider: str
    radar_base_url: str
    public_bind: bool
    stateless_http: bool = True
    json_response: bool = True
    auth_mode: str = "reverse-proxy-required"

    def to_public_dict(self) -> dict[str, object]:
        """Return settings safe to print in logs and CI."""

        return asdict(self)


def load_http_server_settings() -> HttpServerSettings:
    """Load and fail-closed validate hosted-server environment settings."""

    host = os.getenv("OSI_MCP_HTTP_HOST", "127.0.0.1").strip()
    if not host or len(host) > 255 or any(character.isspace() for character in host):
        raise ValueError("OSI_MCP_HTTP_HOST must be a non-empty host without whitespace")

    try:
        port = int(os.getenv("OSI_MCP_HTTP_PORT", "8000"))
    except ValueError as exc:
        raise ValueError("OSI_MCP_HTTP_PORT must be an integer") from exc
    if not 1 <= port <= 65535:
        raise ValueError("OSI_MCP_HTTP_PORT must be between 1 and 65535")

    provider = os.getenv("OSI_PROVIDER", "mock").strip().lower()
    if provider not in {"mock", "http"}:
        raise ValueError("OSI_PROVIDER must be either 'mock' or 'http'")

    public_bind = not _is_loopback_host(host)
    base_url = os.getenv("AIWORKSTATION_RADAR_BASE_URL", DEFAULT_BASE_URL).strip()

    if public_bind:
        acknowledgement = os.getenv("OSI_MCP_HTTP_PUBLIC_BIND_ACK", "").strip()
        if acknowledgement != PUBLIC_BIND_ACK:
            raise ValueError(
                "Non-loopback MCP HTTP binds require "
                f"OSI_MCP_HTTP_PUBLIC_BIND_ACK={PUBLIC_BIND_ACK}"
            )
        if provider != "http":
            raise ValueError("Non-loopback MCP HTTP binds require OSI_PROVIDER=http")
        base_url = _validate_live_radar_origin(base_url)

    if _env_bool("OSI_MCP_HTTP_ASSUME_PUBLIC_AUTH", False):
        # This switch is deliberately rejected. It exists only to prevent an
        # operator from interpreting a boolean as an authentication feature.
        raise ValueError(
            "OSI_MCP_HTTP_ASSUME_PUBLIC_AUTH is not supported; configure real reverse-proxy "
            "authentication or native OAuth before Internet exposure"
        )

    return HttpServerSettings(
        host=host,
        port=port,
        provider=provider,
        radar_base_url=base_url.rstrip("/"),
        public_bind=public_bind,
    )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="osi-mcp-http")
    parser.add_argument(
        "--check-config",
        action="store_true",
        help="Validate environment configuration and exit without opening a socket.",
    )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        settings = load_http_server_settings()
    except ValueError as exc:
        print(
            json.dumps(
                {
                    "ok": False,
                    "error": {"code": "INVALID_HOSTED_CONFIGURATION", "message": str(exc)},
                },
                ensure_ascii=False,
                indent=2,
            )
        )
        return 2

    if args.check_config:
        print(
            json.dumps(
                {
                    "ok": True,
                    "endpoint": f"http://{settings.host}:{settings.port}/mcp",
                    "settings": settings.to_public_dict(),
                    "warnings": [
                        "Non-loopback deployment still requires trusted TLS termination, authentication, rate limiting, and abuse controls."
                    ]
                    if settings.public_bind
                    else [],
                },
                ensure_ascii=False,
                indent=2,
            )
        )
        return 0

    server = build_mcp_server()
    server.run(
        transport="streamable-http",
        host=settings.host,
        port=settings.port,
        stateless_http=True,
        json_response=True,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
