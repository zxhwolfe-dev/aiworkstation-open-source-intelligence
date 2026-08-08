"""Hardened OAuth Streamable HTTP entrypoint for the public hosted MCP."""

from __future__ import annotations

import argparse
import json
import os
from typing import Sequence

from mcp.server.transport_security import TransportSecuritySettings

from .endpoint_policy import validate_mcp_endpoint
from .hosted_auth import load_hosted_oauth_config
from .hosted_backend import load_hosted_backend_config
from .hosted_mcp_server import build_hosted_mcp_server
from .hosted_rate_limit import load_hosted_rate_limit_config
from .http_server import HttpServerConfig, validate_http_configuration


def _validate_hosted_configuration() -> tuple[HttpServerConfig, str, str, str, dict[str, int]]:
    if str(os.getenv("OSI_PROVIDER") or "").strip().lower() != "http":
        raise ValueError("public hosted MCP requires OSI_PROVIDER=http")
    http_config = validate_http_configuration()
    oauth = load_hosted_oauth_config()
    backend = load_hosted_backend_config()
    rate_limit = load_hosted_rate_limit_config()
    resource_url = validate_mcp_endpoint(oauth.resource_url, allow_http_localhost=False)
    if not resource_url.startswith("https://") or not resource_url.endswith("/mcp"):
        raise ValueError("OSI_OAUTH_RESOURCE_URL must be the public HTTPS /mcp endpoint")
    limits = {
        "per_minute": rate_limit.per_minute,
        "per_hour": rate_limit.per_hour,
        "premium_per_minute": rate_limit.premium_per_minute,
        "max_subjects": rate_limit.max_subjects,
    }
    return http_config, oauth.issuer_url, resource_url, backend.base_url, limits


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="osi-mcp-hosted")
    parser.add_argument(
        "--check-config",
        action="store_true",
        help="Validate hosted OAuth/MCP configuration without opening a socket.",
    )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        config, issuer_url, resource_url, backend_url, rate_limits = _validate_hosted_configuration()
    except ValueError as exc:
        print(json.dumps({"ok": False, "error": str(exc)}, ensure_ascii=False, indent=2))
        return 2

    public_config = {
        "ok": True,
        "mode": "hosted-oauth",
        "host": config.host,
        "port": config.port,
        "path": "/mcp",
        "provider": "http",
        "oauth_issuer": issuer_url,
        "oauth_resource": resource_url,
        "backend_origin": backend_url,
        "allowed_hosts": list(config.allowed_hosts),
        "allowed_origins": list(config.allowed_origins),
        "cors_enabled": config.cors_enabled,
        "request_body_limit": config.request_body_limit,
        "rate_limits": rate_limits,
        "stateless_http": True,
        "json_response": True,
    }
    if args.check_config:
        print(json.dumps(public_config, ensure_ascii=False, indent=2))
        return 0

    try:
        import uvicorn
    except ImportError:
        print(json.dumps({"ok": False, "error": "uvicorn is not installed"}, indent=2))
        return 2

    server = build_hosted_mcp_server()
    transport_security = TransportSecuritySettings(
        enable_dns_rebinding_protection=True,
        allowed_hosts=list(config.allowed_hosts),
        allowed_origins=list(config.allowed_origins),
    )
    app = server.streamable_http_app(
        transport_security=transport_security,
        stateless_http=True,
        json_response=True,
    )
    if config.cors_enabled:
        from starlette.middleware.cors import CORSMiddleware

        app.add_middleware(
            CORSMiddleware,
            allow_origins=list(config.allowed_origins),
            allow_methods=["GET", "POST", "DELETE"],
            allow_headers=["Authorization", "Content-Type", "MCP-Protocol-Version"],
            expose_headers=["MCP-Session-Id"],
            allow_credentials=False,
        )
    print(json.dumps(public_config, ensure_ascii=False), flush=True)
    uvicorn.run(
        app,
        host=config.host,
        port=config.port,
        log_level="info",
        access_log=False,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
