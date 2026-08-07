"""Local CLI for inspecting contracts and invoking mock or HTTP-backed tools."""

from __future__ import annotations

import argparse
import json
import os
from typing import Sequence

from .app import create_registry_from_env
from .errors import ToolError


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="osi-m0")
    subparsers = parser.add_subparsers(dest="command", required=True)

    subparsers.add_parser("list-tools", help="List the six read-only tools")
    subparsers.add_parser("provider-info", help="Show the selected provider without exposing secrets")

    invoke_parser = subparsers.add_parser("invoke", help="Invoke a tool using a JSON object")
    invoke_parser.add_argument("tool")
    invoke_parser.add_argument("--arguments", default="{}", help="JSON object passed to the tool")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        registry = create_registry_from_env()
    except ValueError as exc:
        print(json.dumps({"error": {"code": "INVALID_CONFIGURATION", "message": str(exc)}}, indent=2))
        return 2

    if args.command == "provider-info":
        selected = os.getenv("OSI_PROVIDER", "mock").strip().lower()
        payload = {
            "provider": selected,
            "network_enabled": selected == "http",
            "base_url": os.getenv("AIWORKSTATION_RADAR_BASE_URL", "https://aiworkstation.cn")
            if selected == "http"
            else None,
        }
        print(json.dumps(payload, ensure_ascii=False, indent=2))
        return 0

    if args.command == "list-tools":
        print(
            json.dumps(
                [
                    {
                        "name": spec.name,
                        "description": spec.description,
                        "input_fields": spec.input_fields,
                        "read_only": True,
                    }
                    for spec in registry.specs
                ],
                ensure_ascii=False,
                indent=2,
            )
        )
        return 0

    try:
        arguments = json.loads(args.arguments)
        if not isinstance(arguments, dict):
            raise ValueError("--arguments must decode to a JSON object")
        result = registry.invoke(args.tool, arguments)
    except (json.JSONDecodeError, ValueError) as exc:
        print(json.dumps({"error": {"code": "INVALID_JSON", "message": str(exc)}}, indent=2))
        return 2
    except ToolError as exc:
        print(json.dumps(exc.to_dict(), ensure_ascii=False, indent=2))
        return 2

    print(json.dumps(result.to_dict(), ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
