"""Replay sanitized public Radar fixtures through the production adapter.

This module is offline. It validates a capture directory, serves its four
responses through the JsonTransport protocol, and exercises the same hardened
provider used by MCP and CLI entrypoints.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, Mapping, Sequence

from .contracts import utc_now_iso
from .fixture_validation import validate_contract_directory
from .http_provider import PUBLIC_API_PREFIX, JsonResponse
from .probe import evaluate_probe
from .selector_task_transport import SelectorTaskJsonTransport
from .strict_http_provider import AIWorkstationHttpProvider
from .tools import ToolRegistry


class FixtureReplayTransport:
    """Serve a validated capture directory through the JsonTransport protocol."""

    TASK_ID = "fixture-selector-task"

    def __init__(self, directory: Path, *, selector_scenario: str = "formal") -> None:
        self.directory = Path(directory)
        validation = validate_contract_directory(self.directory)
        if not validation["ok"]:
            raise ValueError(
                "contract fixture directory is invalid: " + "; ".join(validation["errors"])
            )
        if selector_scenario not in {"formal", "no-match"}:
            raise ValueError("selector_scenario must be 'formal' or 'no-match'")
        self.selector_scenario = selector_scenario
        self.calls: list[dict[str, Any]] = []
        self._fixtures = {
            "project-list": self._load("project-list.json"),
            "project-detail": self._load("project-detail.json"),
            "selector-formal": self._load("selector-formal.json"),
            "selector-no-match": self._load("selector-no-match.json"),
        }

    def _load(self, filename: str) -> Mapping[str, Any]:
        payload = json.loads((self.directory / filename).read_text(encoding="utf-8"))
        if not isinstance(payload, Mapping):
            raise ValueError(f"{filename} must contain a JSON object")
        return payload

    def _selector_fixture(self) -> Mapping[str, Any]:
        return self._fixtures[
            "selector-formal" if self.selector_scenario == "formal" else "selector-no-match"
        ]

    def request(
        self,
        method: str,
        path: str,
        *,
        query: Mapping[str, Any] | None = None,
        body: Mapping[str, Any] | None = None,
        timeout: float = 30.0,
    ) -> JsonResponse:
        method_upper = method.upper()
        self.calls.append(
            {
                "method": method_upper,
                "path": path,
                "query_keys": sorted((query or {}).keys()),
                "body_keys": sorted((body or {}).keys()),
                "timeout": timeout,
            }
        )
        fixture: Mapping[str, Any] | None = None
        status = 200
        headers: Mapping[str, Any] = {"content-type": "application/json"}
        observed_at = utc_now_iso()
        scenario = "task"

        if method_upper == "GET" and path == f"{PUBLIC_API_PREFIX}/projects":
            fixture = self._fixtures["project-list"]
        elif method_upper == "GET" and path.startswith(f"{PUBLIC_API_PREFIX}/projects/"):
            fixture = self._fixtures["project-detail"]
        elif method_upper == "POST" and path == f"{PUBLIC_API_PREFIX}/selector/tasks":
            status = 202
            payload: Mapping[str, Any] = {
                "ok": True,
                "task_id": self.TASK_ID,
                "status": "queued",
            }
            return JsonResponse(
                status=status,
                headers={"content-type": "application/json"},
                payload=payload,
                url=f"fixture://{self.directory.name}/selector/tasks",
                observed_at=observed_at,
            )
        elif method_upper == "GET" and path == f"{PUBLIC_API_PREFIX}/selector/tasks/{self.TASK_ID}":
            selector_fixture = self._selector_fixture()
            result = selector_fixture.get("payload")
            if not isinstance(result, Mapping):
                raise ValueError("selector fixture is missing payload")
            return JsonResponse(
                status=200,
                headers={"content-type": "application/json"},
                payload={
                    "task_id": self.TASK_ID,
                    "status": "completed",
                    "error": "",
                    "result": dict(result),
                },
                url=f"fixture://{self.directory.name}/selector/tasks/{self.TASK_ID}",
                observed_at=str(selector_fixture.get("observed_at") or observed_at),
            )
        elif method_upper == "DELETE" and path == f"{PUBLIC_API_PREFIX}/selector/tasks/{self.TASK_ID}":
            return JsonResponse(
                status=202,
                headers={"content-type": "application/json"},
                payload={"ok": True, "status": "cancelling"},
                url=f"fixture://{self.directory.name}/selector/tasks/{self.TASK_ID}",
                observed_at=observed_at,
            )
        else:
            raise ValueError(f"fixture transport has no response for {method} {path}")

        payload = fixture.get("payload") if fixture else None
        fixture_headers = fixture.get("headers") if fixture else None
        if not isinstance(payload, Mapping) or not isinstance(fixture_headers, Mapping):
            raise ValueError("fixture response is missing payload or headers")
        headers = fixture_headers
        observed_at = str(fixture.get("observed_at") or utc_now_iso())
        scenario = str(fixture.get("scenario") or "fixture")
        return JsonResponse(
            status=int(fixture.get("status") or 0),
            headers={str(key).lower(): str(value) for key, value in headers.items()},
            payload=dict(payload),
            url=f"fixture://{self.directory.name}/{scenario}",
            observed_at=observed_at,
        )


def replay_contract_directory(directory: Path) -> dict[str, Any]:
    """Replay project facts, license, formal search and no-match search offline."""

    root = Path(directory)
    validation = validate_contract_directory(root)
    if not validation["ok"]:
        return {
            "schema_version": "osi.public-contract-replay.v1",
            "generated_at": utc_now_iso(),
            "directory": str(root),
            "ok": False,
            "validation": validation,
            "checks": [],
        }
    manifest = json.loads((root / "manifest.json").read_text(encoding="utf-8"))
    locale = str(manifest.get("locale") or "en")
    project_id = str(manifest.get("project_id") or "")

    formal_transport = FixtureReplayTransport(root, selector_scenario="formal")
    formal_registry = ToolRegistry(
        AIWorkstationHttpProvider(
            "https://fixture.invalid",
            transport=SelectorTaskJsonTransport(formal_transport, poll_interval=0),
            hydrate_limit=3,
        )
    )
    facts = formal_registry.invoke(
        "get_project_facts",
        {"project_id": project_id, "locale": locale, "request_id": "replay-facts"},
    ).to_dict()
    license_result = formal_registry.invoke(
        "get_license_evidence",
        {"project_id": project_id, "locale": locale, "request_id": "replay-license"},
    ).to_dict()
    formal_search = formal_registry.invoke(
        "search_ai_projects",
        {
            "query": "Replay the captured formal selector scenario.",
            "constraints": [],
            "locale": locale,
            "request_id": "replay-formal",
        },
    ).to_dict()
    checks = evaluate_probe(facts, license_result, formal_search)

    no_match_transport = FixtureReplayTransport(root, selector_scenario="no-match")
    no_match_registry = ToolRegistry(
        AIWorkstationHttpProvider(
            "https://fixture.invalid",
            transport=SelectorTaskJsonTransport(no_match_transport, poll_interval=0),
            hydrate_limit=3,
        )
    )
    no_match = no_match_registry.invoke(
        "search_ai_projects",
        {
            "query": "Replay the captured no-match selector scenario.",
            "constraints": [],
            "locale": locale,
            "request_id": "replay-no-match",
        },
    ).to_dict()
    no_match_data = no_match.get("data") if isinstance(no_match.get("data"), Mapping) else {}
    no_match_ok = int(no_match_data.get("total") or 0) == 0 and bool(
        str(no_match_data.get("no_match_reason") or "").strip()
    )
    checks.append(
        {
            "id": "no-match-replay",
            "ok": no_match_ok,
            "message": "Captured no-match response remains an explicit no-match through the provider.",
            "details": {
                "total": int(no_match_data.get("total") or 0),
                "no_match_reason": no_match_data.get("no_match_reason"),
            },
        }
    )
    return {
        "schema_version": "osi.public-contract-replay.v1",
        "generated_at": utc_now_iso(),
        "directory": str(root),
        "locale": locale,
        "project_id": project_id,
        "ok": all(bool(check.get("ok")) for check in checks),
        "summary": {
            "passed": sum(1 for check in checks if check.get("ok")),
            "failed": sum(1 for check in checks if not check.get("ok")),
        },
        "checks": checks,
        "validation": validation,
        "request_summary": {
            "formal_calls": formal_transport.calls,
            "no_match_calls": no_match_transport.calls,
        },
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="osi-replay-contracts")
    parser.add_argument("--directory", type=Path, required=True)
    parser.add_argument("--output", type=Path)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    report = replay_contract_directory(args.directory)
    rendered = json.dumps(report, ensure_ascii=False, indent=2) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(rendered, encoding="utf-8")
    print(rendered, end="")
    return 0 if report["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
