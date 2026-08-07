"""Guarded Streamable HTTP entrypoint for private and hosted alpha testing.

This module intentionally does not make the service public-safe by itself.
Non-loopback binds require explicit host allowlists, an operator deployment
acknowledgement and the live HTTP provider. Authentication, TLS termination,
rate limiting and abuse controls remain the responsibility of the trusted
gateway until native OAuth is implemented.
"""

from __future__ import annotations

import argparse
import ipaddress
import json
import os
import re
import socket
from dataclasses import asdict, dataclass
from typing import Sequence
from urllib.parse import urlparse

from mcp.server.transport_security import TransportSecuritySettings

from .http_provider import DEFAULT_BASE_URL
from .mcp_server import build_mcp_server

PUBLIC_BIND_ACK = "reverse-proxy-or-private-network"
ALLOWED_RADAR_HOSTS = {"aiworkstation.cn", "useaistation.com"}
DEFAULT_MAX_REQUEST_BODY_BYTES = 256 * 1024
MAX_ALLOWED_HOSTS = 20
MAX_ALLOWED_ORIGINS = 20
HOST_ALLOWLIST_PATTERN = re.compile(
    r"^(?:[A-Za-z0-9](?:[A-Za-z0-9.-]{0,251}[A-Za-z0-9])?|\d{1,3}(?:\.\d{1,3}){3})(?::(?:\*|\d{1,5}))?$"
)


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
    try:
        port = parsed.port
    except ValueError as exc:
        raise ValueError("Radar origin contains an invalid port") from exc
    if port not in {None, 443}:
        raise ValueError("Public-bind Radar origin must use the standard HTTPS port")
    return base_url.rstrip("/")


def _csv_values(name: str, *, maximum: int) -> tuple[str, ...]:
    raw = os.getenv(name, "")
    values = tuple(dict.fromkeys(part.strip() for part in raw.split(",") if part.strip()))
    if len(values) > maximum:
        raise ValueError(f"{name} may contain at most {maximum} entries")
    return values


def _validate_allowed_hosts(values: tuple[str, ...]) -> tuple[str, ...]:
    if not values:
        raise ValueError(
            "Non-loopback MCP HTTP binds require OSI_MCP_HTTP_ALLOWED_HOSTS with the exact externally served Host values"
        )
    for value in values:
        if not HOST_ALLOWLIST_PATTERN.fullmatch(value):
            raise ValueError(
                "OSI_MCP_HTTP_ALLOWED_HOSTS entries must be exact host[:port] values or host:* patterns"
            )
        if value.endswith(":*"):
            continue
        if ":" in value:
            port = value.rsplit(":", 1)[1]
            if port.isdigit() and not 1 <= int(port) <= 65535:
                raise ValueError("OSI_MCP_HTTP_ALLOWED_HOSTS contains an invalid port")
    return values


def _validate_allowed_origins(values: tuple[str, ...]) -> tuple[str, ...]:
    validated: list[str] = []
    for value in values:
        parsed = urlparse(value)
        if parsed.scheme != "https" or not parsed.hostname:
            raise ValueError("OSI_MCP_HTTP_ALLOWED_ORIGINS entries must be HTTPS origins")
        if parsed.username or parsed.password or parsed.query or parsed.fragment:
            raise ValueError("OSI_MCP_HTTP_ALLOWED_ORIGINS must not contain credentials, query or fragment")
        if parsed.path not in {"", "/"}:
            raise ValueError("OSI_MCP_HTTP_ALLOWED_ORIGINS entries must not contain a path")
        try:
            port = parsed.port
        except ValueError as exc:
            raise ValueError("OSI_MCP_HTTP_ALLOWED_ORIGINS contains an invalid port") from exc
        if port is not None and not 1 <= port <= 65535:
            raise ValueError("OSI_MCP_HTTP_ALLOWED_ORIGINS contains an invalid port")
        validated.append(value.rstrip("/"))
    return tuple(validated)


@dataclass(frozen=True, slots=True)
class HttpServerSettings:
    host: str
    port: int
    provider: str
    radar_base_url: str
    public_bind: bool
    allowed_hosts: tuple[str, ...] = ()
    allowed_origins: tuple[str, ...] = ()
    max_request_body_size: int = DEFAULT_MAX_REQUEST_BODY_BYTES
    stateless_http: bool = True
    json_response: bool = True
    auth_mode: str = "reverse-proxy-required"

    def to_public_dict(self) -> dict[str, object]:
        """Return settings safe to print in logs and CI."""

        return asdict(self)

    def transport_security(self) -> TransportSecuritySettings | None:
        """Return explicit SDK DNS-rebinding protection for deployed hosts.

        Local loopback mode intentionally uses the SDK's secure localhost
        defaults. Non-loopback mode always passes an explicit allowlist.
        """

        if not self.public_bind:
            return None
        return TransportSecuritySettings(
            allowed_hosts=list(self.allowed_hosts),
            allowed_origins=list(self.allowed_origins),
        )


def load_http_server_settings() -> HttpServerSettings:
    """Load and fail-closed validate hosted-server environment settings."""

    host = os.getenv("OSI_MCP_HTTP_HOST", "127.0.0.1").strip()
    if not host or len(host) > 255 or any(character.isspace() for character in host):
        raise ValueError("OSI_MCP_HTTP_HOST must be a non-empty host without whitespace")

    try:
        port = int(os.getenv("OSI_MCP_HTTP_PORT", "8000"))
        max_request_body_size = int(
            os.getenv("OSI_MCP_HTTP_MAX_REQUEST_BODY_BYTES", str(DEFAULT_MAX_REQUEST_BODY_BYTES))
        )
    except ValueError as exc:
        raise ValueError("MCP HTTP port and request-body limit must be integers") from exc
    if not 1 <= port <= 65535:
        raise ValueError("OSI_MCP_HTTP_PORT must be between 1 and 65535")
    if not 16 * 1024 <= max_request_body_size <= 1024 * 1024:
        raise ValueError(
            "OSI_MCP_HTTP_MAX_REQUEST_BODY_BYTES must be between 16384 and 1048576"
        )

    provider = os.getenv("OSI_PROVIDER", "mock").strip().lower()
    if provider not in {"mock", "http"}:
        raise ValueError("OSI_PROVIDER must be either 'mock' or 'http'")

    public_bind = not _is_loopback_host(host)
    base_url = os.getenv("AIWORKSTATION_RADAR_BASE_URL", DEFAULT_BASE_URL).strip()
    allowed_hosts: tuple[str, ...] = ()
    allowed_origins: tuple[str, ...] = ()

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
        allowed_hosts = _validate_allowed_hosts(
            _csv_values("OSI_MCP_HTTP_ALLOWED_HOSTS", maximum=MAX_ALLOWED_HOSTS)
        )
        allowed_origins = _validate_allowed_origins(
            _csv_values("OSI_MCP_HTTP_ALLOWED_ORIGINS", maximum=MAX_ALLOWED_ORIGINS)
        )

    if _env_bool("OSI_MCP_HTTP_ASSUME_PUBLIC_AUTH", False):
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
        allowed_hosts=allowed_hosts,
        allowed_origins=allowed_origins,
        max_request_body_size=max_request_body_size,
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
    run_arguments: dict[str, object] = {
        "transport": "streamable-http",
        "host": settings.host,
        "port": settings.port,
        "stateless_http": True,
        "json_response": True,
        "max_request_body_size": settings.max_request_body_size,
    }
    transport_security = settings.transport_security()
    if transport_security is not None:
        run_arguments["transport_security"] = transport_security
    server.run(**run_arguments)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
