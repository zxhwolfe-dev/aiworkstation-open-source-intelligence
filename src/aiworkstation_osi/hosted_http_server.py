"""Hardened data-only Streamable HTTP entrypoint for the public Hosted MCP."""

from __future__ import annotations

import argparse
import json
import os
from typing import Sequence

from .hosted_access import HOSTED_ACCESS_PUBLIC, load_hosted_access_mode
from .hosted_mcp_server import build_public_hosted_mcp_server
from .http_server import HttpServerSettings, load_http_server_settings
from .release_identity import validate_hosted_deployment_identity


def _validate_hosted_configuration() -> tuple[HttpServerSettings, str, str]:
    if str(os.getenv("OSI_PROVIDER") or "").strip().lower() != "http":
        raise ValueError("public hosted MCP requires OSI_PROVIDER=http")

    http_config = load_http_server_settings()
    access_mode = load_hosted_access_mode()
    if access_mode != HOSTED_ACCESS_PUBLIC:  # defensive; loader already validates
        raise ValueError("unsupported Hosted access mode")
    release_commit = validate_hosted_deployment_identity()
    return http_config, access_mode, release_commit


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="osi-mcp-hosted")
    parser.add_argument(
        "--check-config",
        action="store_true",
        help="Validate the data-only Hosted MCP configuration without opening a socket.",
    )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        config, access_mode, release_commit = _validate_hosted_configuration()
    except ValueError as exc:
        print(json.dumps({"ok": False, "error": str(exc)}, ensure_ascii=False, indent=2))
        return 2

    public_config: dict[str, object] = {
        "ok": True,
        "mode": "hosted-public",
        "access_mode": access_mode,
        "release_commit": release_commit,
        "host": config.host,
        "port": config.port,
        "path": "/mcp",
        "provider": "http",
        "tool_count": 9,
        "premium_enabled": False,
        "server_model_enabled": False,
        "oauth_enabled": False,
        "allowed_hosts": list(config.allowed_hosts),
        "allowed_origins": list(config.allowed_origins),
        "cors_enabled": bool(config.allowed_origins),
        "request_body_limit": config.max_request_body_size,
        "stateless_http": config.stateless_http,
        "json_response": config.json_response,
        "gateway_abuse_control": "required-dual-ip-rate-limit",
    }

    if args.check_config:
        print(json.dumps(public_config, ensure_ascii=False, indent=2))
        return 0

    server = build_public_hosted_mcp_server()
    run_arguments: dict[str, object] = {
        "transport": "streamable-http",
        "host": config.host,
        "port": config.port,
        "stateless_http": config.stateless_http,
        "json_response": config.json_response,
        "max_request_body_size": config.max_request_body_size,
    }
    transport_security = config.transport_security()
    if transport_security is not None:
        run_arguments["transport_security"] = transport_security

    print(json.dumps(public_config, ensure_ascii=False), flush=True)
    server.run(**run_arguments)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
