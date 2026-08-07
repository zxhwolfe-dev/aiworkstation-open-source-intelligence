"""Validate a deployed Streamable HTTP MCP endpoint from a real MCP client.

The command is read-only. By default it discovers tools only. ``--invoke-search``
adds one read-only project search so operators can verify structured results end
to end after deployment.
"""

from __future__ import annotations

import argparse
import asyncio
import json
from typing import Any, Sequence
from urllib.parse import urlparse

from mcp import Client

from .contracts import TOOL_NAMES, utc_now_iso


def _validate_endpoint(url: str, *, allow_http_localhost: bool) -> str:
    parsed = urlparse(url)
    if parsed.scheme not in {"http", "https"}:
        raise ValueError("MCP endpoint must use http or https")
    if parsed.username or parsed.password:
        raise ValueError("MCP endpoint URL must not contain credentials")
    if parsed.query or parsed.fragment:
        raise ValueError("MCP endpoint URL must not contain query or fragment")
    if not parsed.hostname:
        raise ValueError("MCP endpoint hostname is required")
    local_hosts = {"localhost", "127.0.0.1", "::1"}
    if parsed.scheme != "https" and not (
        allow_http_localhost and parsed.hostname.lower() in local_hosts
    ):
        raise ValueError("Remote MCP endpoints must use HTTPS; HTTP is allowed only for localhost")
    return url


def _annotation_summary(tool: Any) -> dict[str, Any]:
    annotations = getattr(tool, "annotations", None)
    return {
        "title": getattr(annotations, "title", None),
        "read_only_hint": getattr(annotations, "read_only_hint", None),
        "destructive_hint": getattr(annotations, "destructive_hint", None),
        "idempotent_hint": getattr(annotations, "idempotent_hint", None),
        "open_world_hint": getattr(annotations, "open_world_hint", None),
    }


async def smoke_remote_endpoint(
    url: str,
    *,
    invoke_search: bool = False,
    locale: str = "en",
) -> dict[str, Any]:
    checks: list[dict[str, Any]] = []
    async with Client(url) as client:
        listed = await client.list_tools()
        tools = list(listed.tools)
        names = [tool.name for tool in tools]
        exact_tools = set(names) == set(TOOL_NAMES) and len(names) == len(TOOL_NAMES)
        checks.append(
            {
                "id": "tool-set",
                "ok": exact_tools,
                "message": "Endpoint exposes exactly the six declared read-only tools.",
                "details": {"tools": names},
            }
        )

        annotations_ok = all(
            getattr(tool, "annotations", None) is not None
            and getattr(tool.annotations, "read_only_hint", None) is True
            and getattr(tool.annotations, "destructive_hint", None) is False
            and getattr(tool.annotations, "idempotent_hint", None) is True
            and getattr(tool.annotations, "open_world_hint", None) is True
            for tool in tools
        )
        checks.append(
            {
                "id": "tool-annotations",
                "ok": annotations_ok,
                "message": "All discovered tools advertise the expected side-effect annotations.",
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
                    "message": "A real remote tool call returns the unified structured result contract.",
                    "details": search_summary,
                }
            )

        return {
            "schema_version": "osi.remote-smoke.v1",
            "generated_at": utc_now_iso(),
            "endpoint": url,
            "protocol_version": str(getattr(client, "protocol_version", "") or ""),
            "server_info": str(getattr(client, "server_info", "") or ""),
            "ok": all(check["ok"] for check in checks),
            "summary": {
                "passed": sum(1 for check in checks if check["ok"]),
                "failed": sum(1 for check in checks if not check["ok"]),
            },
            "checks": checks,
            "search": search_summary,
        }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="osi-remote-smoke")
    parser.add_argument("--url", default="http://127.0.0.1:8000/mcp")
    parser.add_argument("--locale", choices=("zh", "en"), default="en")
    parser.add_argument(
        "--invoke-search",
        action="store_true",
        help="Perform one read-only search after tool discovery.",
    )
    parser.add_argument("--output")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        url = _validate_endpoint(args.url, allow_http_localhost=True)
        report = asyncio.run(
            smoke_remote_endpoint(
                url,
                invoke_search=args.invoke_search,
                locale=args.locale,
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
        from pathlib import Path

        output = Path(args.output)
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(rendered, encoding="utf-8")
    print(rendered, end="")
    return 0 if report["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
