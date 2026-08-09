"""Validate deployed Streamable HTTP MCP endpoints from a real MCP client.

Profiles:

- ``standard``: nine-tool development/public Radar smoke.
- ``hosted-public``: formal anonymous Hosted smoke; proves the exact deployment,
  gateway IP-abuse-control policy, nine read-only tools, and one real search.
- ``hosted-oauth``: formal OAuth Hosted smoke; proves the OAuth boundary,
  exact deployment, nine standard tools plus Premium, and one real search.
- ``hosted``: backward-compatible alias for ``hosted-oauth``.

Tokens are never written to reports.
"""

from __future__ import annotations

import argparse
import asyncio
import getpass
import json
import os
import subprocess
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Any, AsyncIterator, Sequence
from urllib.parse import parse_qs, urlparse

from .contracts import TOOL_NAMES, utc_now_iso
from .endpoint_policy import validate_mcp_endpoint
from .hosted_public_remote_evidence import (
    PUBLIC_HOSTED_REMOTE_SCHEMA,
    inspect_public_gateway,
)
from .hosted_remote_evidence import (
    HOSTED_PREMIUM_TOOL,
    HOSTED_REMOTE_SCHEMA,
    expected_hosted_tools,
    inspect_oauth_boundary,
)
from .release_identity import release_commit_from_server_version

_validate_endpoint = validate_mcp_endpoint
OAUTH_HOSTED_PROFILES = {"hosted", "hosted-oauth"}
HOSTED_PROFILES = OAUTH_HOSTED_PROFILES | {"hosted-public"}


def _is_oauth_hosted(profile: str) -> bool:
    return profile in OAUTH_HOSTED_PROFILES


def _is_hosted(profile: str) -> bool:
    return profile in HOSTED_PROFILES


def _git_head(root: Path) -> str:
    try:
        completed = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=root.expanduser().resolve(),
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
            timeout=15,
            check=False,
        )
    except (OSError, subprocess.TimeoutExpired):
        return ""
    return completed.stdout.strip() if completed.returncode == 0 else ""


def _annotation_summary(tool: Any) -> dict[str, Any]:
    annotations = getattr(tool, "annotations", None)
    return {
        "title": getattr(annotations, "title", None),
        "read_only_hint": getattr(annotations, "read_only_hint", None),
        "destructive_hint": getattr(annotations, "destructive_hint", None),
        "idempotent_hint": getattr(annotations, "idempotent_hint", None),
        "open_world_hint": getattr(annotations, "open_world_hint", None),
    }


def _expected_tool_names(profile: str) -> tuple[str, ...]:
    return expected_hosted_tools() if _is_oauth_hosted(profile) else tuple(TOOL_NAMES)


def _tool_annotations_ok(tool: Any, profile: str) -> bool:
    annotations = getattr(tool, "annotations", None)
    if annotations is None:
        return False
    name = str(getattr(tool, "name", "") or "")
    if _is_oauth_hosted(profile) and name == HOSTED_PREMIUM_TOOL:
        return (
            getattr(annotations, "read_only_hint", None) is False
            and getattr(annotations, "destructive_hint", None) is False
            and getattr(annotations, "idempotent_hint", None) is False
            and getattr(annotations, "open_world_hint", None) is True
        )
    return (
        name in TOOL_NAMES
        and getattr(annotations, "read_only_hint", None) is True
        and getattr(annotations, "destructive_hint", None) is False
        and getattr(annotations, "idempotent_hint", None) is True
        and getattr(annotations, "open_world_hint", None) is True
    )


class _InMemoryTokenStorage:
    """Ephemeral OAuth storage; no access/refresh token is persisted to disk."""

    def __init__(self) -> None:
        self.tokens: Any | None = None
        self.client_info: Any | None = None

    async def get_tokens(self) -> Any | None:
        return self.tokens

    async def set_tokens(self, tokens: Any) -> None:
        self.tokens = tokens

    async def get_client_info(self) -> Any | None:
        return self.client_info

    async def set_client_info(self, client_info: Any) -> None:
        self.client_info = client_info


def _interactive_oauth_provider(url: str) -> Any:
    from pydantic import AnyUrl

    from mcp.client.auth import AuthorizationCodeResult, OAuthClientProvider
    from mcp.shared.auth import OAuthClientMetadata

    async def redirect_handler(authorization_url: str) -> None:
        print("Open this authorization URL in a browser and sign in:", flush=True)
        print(authorization_url, flush=True)

    async def callback_handler() -> Any:
        redirected = await asyncio.to_thread(
            getpass.getpass,
            "Paste the final callback URL from the browser address bar (hidden): ",
        )
        params = parse_qs(urlparse(str(redirected).strip()).query)
        if not params.get("code"):
            raise ValueError("OAuth callback URL is missing code")
        return AuthorizationCodeResult(
            code=params["code"][0],
            state=params.get("state", [None])[0],
            iss=params.get("iss", [None])[0],
        )

    return OAuthClientProvider(
        server_url=url,
        client_metadata=OAuthClientMetadata(
            client_name="AI Workstation Hosted Alpha Validator",
            redirect_uris=[AnyUrl("http://127.0.0.1:3030/callback")],
        ),
        storage=_InMemoryTokenStorage(),
        redirect_handler=redirect_handler,
        callback_handler=callback_handler,
    )


@asynccontextmanager
async def _open_client(
    url: str,
    *,
    auth_mode: str,
    bearer_token: str = "",
) -> AsyncIterator[Any]:
    from mcp import Client

    if auth_mode == "none":
        async with Client(url) as client:
            yield client
        return

    import httpx2
    from mcp.client.streamable_http import streamable_http_client

    kwargs: dict[str, Any] = {
        "follow_redirects": True,
        "timeout": httpx2.Timeout(30.0, read=300.0),
    }
    if auth_mode == "bearer-env":
        token = str(bearer_token or "").strip()
        if not token:
            raise ValueError("bearer token environment variable is missing or empty")
        kwargs["headers"] = {"Authorization": f"Bearer {token}"}
    elif auth_mode == "oauth":
        kwargs["auth"] = _interactive_oauth_provider(url)
    else:
        raise ValueError(f"unsupported auth mode: {auth_mode}")

    async with httpx2.AsyncClient(**kwargs) as http_client:
        transport = streamable_http_client(url, http_client=http_client)
        async with Client(transport) as client:
            yield client


async def smoke_remote_endpoint(
    url: str,
    *,
    invoke_search: bool = False,
    locale: str = "en",
    profile: str = "standard",
    auth_mode: str = "none",
    bearer_token: str = "",
    expected_oauth_issuer: str = "",
    candidate_commit: str = "",
) -> dict[str, Any]:
    """Run a privacy-safe standard, public-Hosted, or OAuth-Hosted smoke."""

    if profile not in ({"standard"} | HOSTED_PROFILES):
        raise ValueError("profile must be standard, hosted-public, hosted-oauth, or hosted")
    if profile == "hosted-public" and auth_mode != "none":
        raise ValueError("hosted-public profile requires auth mode none")
    if _is_oauth_hosted(profile) and auth_mode == "none":
        raise ValueError("OAuth Hosted profile requires oauth or bearer-env authentication")
    if _is_oauth_hosted(profile) and not str(expected_oauth_issuer or "").strip():
        raise ValueError("OAuth Hosted profile requires the expected OAuth issuer")

    oauth_boundary: dict[str, Any] = {}
    gateway_boundary: dict[str, Any] = {}
    if _is_oauth_hosted(profile):
        oauth_boundary = await asyncio.to_thread(
            inspect_oauth_boundary,
            url,
            expected_issuer=expected_oauth_issuer,
        )
        if not oauth_boundary.get("ok"):
            raise ValueError(
                "Hosted OAuth boundary validation failed: "
                + "; ".join(oauth_boundary.get("errors") or [])
            )
    elif profile == "hosted-public":
        gateway_boundary = await asyncio.to_thread(inspect_public_gateway, url)
        if not gateway_boundary.get("ok"):
            raise ValueError(
                "Public Hosted gateway validation failed: "
                + "; ".join(gateway_boundary.get("errors") or [])
            )

    checks: list[dict[str, Any]] = []
    expected_names = _expected_tool_names(profile)
    async with _open_client(url, auth_mode=auth_mode, bearer_token=bearer_token) as client:
        server_info = getattr(client, "server_info", None)
        server_version = str(getattr(server_info, "version", "") or "")
        deployment_commit = release_commit_from_server_version(server_version)
        if _is_hosted(profile):
            deployment_match = bool(candidate_commit) and deployment_commit == str(candidate_commit).strip().lower()
            checks.append(
                {
                    "id": "deployment-identity",
                    "ok": deployment_match,
                    "message": "Remote MCP serverInfo.version identifies the exact local Hosted candidate commit.",
                    "details": {
                        "deployment_commit": deployment_commit,
                        "candidate_commit": str(candidate_commit or "").strip().lower(),
                    },
                }
            )

        listed = await client.list_tools()
        tools = list(listed.tools)
        names = [tool.name for tool in tools]
        exact_tools = set(names) == set(expected_names) and len(names) == len(expected_names)
        if profile == "hosted-public":
            tool_message = "Public Hosted endpoint exposes exactly nine standard read-only Radar tools."
        elif _is_oauth_hosted(profile):
            tool_message = "OAuth Hosted endpoint exposes exactly nine standard Radar tools plus Premium."
        else:
            tool_message = "Endpoint exposes exactly the nine declared standard read-only tools."
        checks.append(
            {
                "id": "tool-set",
                "ok": exact_tools,
                "message": tool_message,
                "details": {"tools": names},
            }
        )

        annotations_ok = all(_tool_annotations_ok(tool, profile) for tool in tools)
        checks.append(
            {
                "id": "tool-annotations",
                "ok": annotations_ok,
                "message": "Discovered tools advertise the expected side-effect annotations.",
                "details": {tool.name: _annotation_summary(tool) for tool in tools},
            }
        )

        search_summary: dict[str, Any] | None = None
        if invoke_search:
            result = await client.call_tool(
                "search_ai_projects",
                {
                    "query": "Find a self-hosted RAG project with Docker and a web UI.",
                    "constraints": {
                        "self_hosted": "required",
                        "docker": "required",
                        "web_ui": "required",
                    },
                    "locale": locale,
                    "source_mode": "required",
                    "request_id": "remote-smoke-search",
                },
            )
            structured = result.structured_content if isinstance(result.structured_content, dict) else {}
            result_ok = (
                not result.is_error
                and structured.get("tool") == "search_ai_projects"
                and structured.get("schema_version") == "osi.tool-result.v1"
                and isinstance(structured.get("verified_facts"), (list, tuple))
                and isinstance(structured.get("recommendations"), (list, tuple))
                and isinstance(structured.get("unknowns"), (list, tuple))
                and isinstance(structured.get("risks"), (list, tuple))
            )
            search_summary = {
                "is_error": bool(result.is_error),
                "schema_version": structured.get("schema_version"),
                "tool": structured.get("tool"),
                "result_count": (
                    structured.get("data", {}).get("total")
                    if isinstance(structured.get("data"), dict)
                    else None
                ),
                "unknown_count": len(structured.get("unknowns") or []),
                "risk_codes": [
                    item.get("code")
                    for item in structured.get("risks") or []
                    if isinstance(item, dict)
                ],
            }
            checks.append(
                {
                    "id": "search-invocation",
                    "ok": result_ok,
                    "message": "A real remote standard-tool call returns the unified structured result contract.",
                    "details": search_summary,
                }
            )

        if _is_oauth_hosted(profile):
            boundary_ok = oauth_boundary.get("ok") is True
        elif profile == "hosted-public":
            boundary_ok = gateway_boundary.get("ok") is True
        else:
            boundary_ok = True
        schema_version = (
            PUBLIC_HOSTED_REMOTE_SCHEMA if profile == "hosted-public" else HOSTED_REMOTE_SCHEMA
        )
        boundary_bonus = 1 if _is_hosted(profile) and boundary_ok else 0
        boundary_failure = 1 if _is_hosted(profile) and not boundary_ok else 0
        return {
            "schema_version": schema_version,
            "generated_at": utc_now_iso(),
            "commit": str(candidate_commit or "").strip().lower(),
            "profile": profile,
            "endpoint": url,
            "protocol_version": str(getattr(client, "protocol_version", "") or ""),
            "server_info": str(server_info or ""),
            "server_version": server_version,
            "deployment_commit": deployment_commit,
            "auth": {"mode": auth_mode},
            "oauth_boundary": oauth_boundary,
            "gateway_boundary": gateway_boundary,
            "tools": names,
            "ok": boundary_ok and all(check["ok"] for check in checks),
            "summary": {
                "passed": sum(1 for check in checks if check["ok"]) + boundary_bonus,
                "failed": sum(1 for check in checks if not check["ok"]) + boundary_failure,
            },
            "checks": checks,
            "search": search_summary,
        }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="osi-remote-smoke")
    parser.add_argument("--url", default="http://127.0.0.1:8000/mcp")
    parser.add_argument("--locale", choices=("zh", "en"), default="en")
    parser.add_argument(
        "--profile",
        choices=("standard", "hosted-public", "hosted-oauth", "hosted"),
        default="standard",
    )
    parser.add_argument("--auth-mode", choices=("none", "bearer-env", "oauth"), default="none")
    parser.add_argument(
        "--bearer-token-env",
        default="OSI_HOSTED_MCP_BEARER_TOKEN",
        help="Environment variable containing a temporary bearer token; the token is never written to output.",
    )
    parser.add_argument("--expected-oauth-issuer", default="")
    parser.add_argument("--root", type=Path, default=Path.cwd())
    parser.add_argument(
        "--invoke-search",
        action="store_true",
        help="Perform one read-only search after tool discovery. Hosted profiles always perform this check.",
    )
    parser.add_argument("--output")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        url = validate_mcp_endpoint(args.url, allow_http_localhost=args.profile == "standard")
        candidate_commit = _git_head(args.root)
        if _is_hosted(args.profile) and not candidate_commit:
            raise ValueError("Hosted evidence requires a Git candidate commit")
        bearer_token = ""
        if args.auth_mode == "bearer-env":
            bearer_token = str(os.getenv(args.bearer_token_env) or "")
            if not bearer_token.strip():
                raise ValueError(f"{args.bearer_token_env} is missing or empty")
        report = asyncio.run(
            smoke_remote_endpoint(
                url,
                invoke_search=bool(args.invoke_search or _is_hosted(args.profile)),
                locale=args.locale,
                profile=args.profile,
                auth_mode=args.auth_mode,
                bearer_token=bearer_token,
                expected_oauth_issuer=args.expected_oauth_issuer,
                candidate_commit=candidate_commit,
            )
        )
    except Exception as exc:
        print(
            json.dumps(
                {
                    "ok": False,
                    "error": {
                        "code": "REMOTE_MCP_SMOKE_FAILED",
                        "message": str(exc),
                    },
                },
                ensure_ascii=False,
                indent=2,
            )
        )
        return 1

    rendered = json.dumps(report, ensure_ascii=False, indent=2) + "\n"
    if args.output:
        output = Path(args.output)
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(rendered, encoding="utf-8")
    print(rendered, end="")
    return 0 if report["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
