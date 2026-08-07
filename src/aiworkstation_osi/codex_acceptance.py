"""Run a real Codex CLI acceptance pass against the six-tool stdio MCP server.

The command uses ``codex exec`` non-interactively and injects a temporary MCP
configuration with ``-c`` overrides. It does not persist Codex configuration.
Actual tool execution is proven by the privacy-safe MCP acceptance ledger rather
than by trusting the model's final prose.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import subprocess
import sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping, Sequence

from .contracts import TOOL_NAMES

SCHEMA_VERSION = "osi.codex-acceptance.v1"
WORKFLOW_VERSION = "osi.codex-live-workflow.v1"
SERVER_NAME = "ai_open_source_intelligence_acceptance"
DEFAULT_BASE_URL = "https://aiworkstation.cn"


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _timestamp_slug() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")


def _toml_string(value: str) -> str:
    # JSON strings are valid TOML basic strings for the characters used here.
    return json.dumps(str(value), ensure_ascii=False)


def _toml_array(values: Sequence[str]) -> str:
    return "[" + ",".join(_toml_string(value) for value in values) + "]"


def _toml_inline_table(values: Mapping[str, str]) -> str:
    return "{" + ",".join(
        f"{key}={_toml_string(value)}" for key, value in values.items()
    ) + "}"


def acceptance_prompt() -> str:
    """Return the fixed read-only workflow that exercises every public tool."""

    return f"""This is a read-only acceptance test for the MCP server `{SERVER_NAME}`.
Do not edit files. Do not use shell commands or web search to answer these tasks.
Use the named MCP server and make at least one successful call to EACH of its six tools.
Do not skip a tool because an earlier result seems sufficient. Unknown or no-match results are acceptable when honest.

Perform these calls:
1. search_ai_projects: find a self-hosted RAG project requiring Docker and a Web UI, locale=en, source_mode=required.
2. get_project_facts: inspect infiniflow/ragflow in English.
3. get_license_evidence: inspect infiniflow/ragflow in English. A missing or unknown license is acceptable; do not infer one.
4. compare_ai_projects: compare langgenius/dify and infiniflow/ragflow for deployment and license considerations, locale=en.
5. find_alternatives: find alternatives to infiniflow/ragflow while preserving self-hosted, Docker, and Web UI requirements, locale=en.
6. compose_ai_stack: compose a private document-QA/RAG stack that is self-hosted and Docker-oriented, locale=en.

After all six tool calls finish, output exactly: ACCEPTANCE_COMPLETE
"""


def _resolve_executable(value: str) -> str:
    candidate = Path(value).expanduser()
    if candidate.is_absolute() and candidate.is_file():
        return str(candidate.resolve())
    resolved = shutil.which(value)
    if not resolved:
        raise FileNotFoundError(f"executable not found: {value}")
    return resolved


def _default_mcp_command() -> str:
    adjacent = Path(sys.executable).resolve().with_name("osi-mcp")
    if adjacent.is_file():
        return str(adjacent)
    return _resolve_executable("osi-mcp")


def _git_head(root: Path) -> str:
    try:
        completed = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=root,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
            timeout=15,
            check=False,
        )
    except (OSError, subprocess.TimeoutExpired):
        return ""
    return completed.stdout.strip() if completed.returncode == 0 else ""


def _codex_version(codex_bin: str) -> str:
    try:
        completed = subprocess.run(
            [codex_bin, "--version"],
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            timeout=20,
            check=False,
        )
    except (OSError, subprocess.TimeoutExpired):
        return ""
    return completed.stdout.strip()[:200]


def build_codex_command(
    *,
    codex_bin: str,
    root: Path,
    mcp_command: str,
    ledger_path: Path,
    provider: str,
    base_url: str,
) -> list[str]:
    """Build a non-persistent Codex exec command with one required MCP server."""

    server = f"mcp_servers.{SERVER_NAME}"
    env = {
        "OSI_PROVIDER": provider,
        "OSI_HTTP_TIMEOUT_SECONDS": "45",
        "OSI_HYDRATE_LIMIT": "5",
        "OSI_ACCEPTANCE_LEDGER_PATH": str(ledger_path.resolve()),
        # Success events still enter the acceptance ledger even when ordinary
        # stderr telemetry remains at its conservative default threshold.
        "OSI_LOG_LEVEL": "WARNING",
    }
    if provider == "http":
        env["AIWORKSTATION_RADAR_BASE_URL"] = base_url

    overrides = [
        f"approval_policy={_toml_string('never')}",
        f"{server}.command={_toml_string(mcp_command)}",
        f"{server}.cwd={_toml_string(str(root.resolve()))}",
        f"{server}.enabled=true",
        f"{server}.required=true",
        f"{server}.startup_timeout_sec=30",
        f"{server}.tool_timeout_sec=120",
        f"{server}.default_tools_approval_mode={_toml_string('approve')}",
        f"{server}.enabled_tools={_toml_array(TOOL_NAMES)}",
        f"{server}.env={_toml_inline_table(env)}",
    ]
    command = [
        codex_bin,
        "exec",
        "--ephemeral",
        "--sandbox",
        "read-only",
        "--color",
        "never",
        "--json",
        "--cd",
        str(root.resolve()),
    ]
    for override in overrides:
        command.extend(("-c", override))
    command.append(acceptance_prompt())
    return command


def load_ledger(path: Path) -> list[dict[str, Any]]:
    if not path.is_file():
        return []
    events: list[dict[str, Any]] = []
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        try:
            payload = json.loads(raw_line)
        except json.JSONDecodeError:
            continue
        if isinstance(payload, dict) and payload.get("schema_version") == "osi.codex-acceptance-ledger.v1":
            events.append(payload)
    return events


def evaluate_ledger(events: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    expected = list(TOOL_NAMES)
    success_counts = Counter(
        str(event.get("tool") or "")
        for event in events
        if event.get("outcome") == "success"
    )
    error_counts = Counter(
        str(event.get("tool") or "")
        for event in events
        if event.get("outcome") != "success"
    )
    missing = [tool for tool in expected if success_counts.get(tool, 0) <= 0]
    return {
        "ok": not missing,
        "expected_tools": expected,
        "successful_tools": [tool for tool in expected if success_counts.get(tool, 0) > 0],
        "missing_tools": missing,
        "success_counts": {tool: int(success_counts.get(tool, 0)) for tool in expected},
        "error_counts": {
            tool: int(error_counts.get(tool, 0))
            for tool in expected
            if error_counts.get(tool, 0) > 0
        },
        "event_count": len(events),
    }


def _sha256_file(path: Path) -> str:
    if not path.is_file():
        return ""
    return hashlib.sha256(path.read_bytes()).hexdigest()


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="osi-codex-acceptance")
    parser.add_argument("--root", type=Path, default=Path.cwd())
    parser.add_argument("--provider", choices=("http", "mock"), default="http")
    parser.add_argument("--base-url", default=DEFAULT_BASE_URL)
    parser.add_argument("--codex-bin", default="codex")
    parser.add_argument("--mcp-command", default="")
    parser.add_argument("--timeout-seconds", type=int, default=600)
    parser.add_argument("--output", type=Path)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    root = args.root.expanduser().resolve()
    output = (
        args.output.expanduser().resolve()
        if args.output
        else root / "tmp" / "codex-acceptance" / f"report-{_timestamp_slug()}.json"
    )
    output.parent.mkdir(parents=True, exist_ok=True)
    ledger_path = output.with_name(output.stem + "-ledger.jsonl")
    ledger_path.unlink(missing_ok=True)

    report: dict[str, Any] = {
        "schema_version": SCHEMA_VERSION,
        "workflow_version": WORKFLOW_VERSION,
        "generated_at": _utc_now_iso(),
        "repository_root": str(root),
        "commit": _git_head(root),
        "provider": args.provider,
        "base_url": args.base_url if args.provider == "http" else "",
        "codex_returncode": None,
        "codex_completed": False,
        "ok": False,
    }

    try:
        codex_bin = _resolve_executable(args.codex_bin)
        mcp_command = (
            _resolve_executable(args.mcp_command)
            if args.mcp_command
            else _default_mcp_command()
        )
        report["codex_version"] = _codex_version(codex_bin)
        report["mcp_command"] = mcp_command
        command = build_codex_command(
            codex_bin=codex_bin,
            root=root,
            mcp_command=mcp_command,
            ledger_path=ledger_path,
            provider=args.provider,
            base_url=args.base_url,
        )
        completed = subprocess.run(
            command,
            cwd=root,
            env=os.environ.copy(),
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=max(60, int(args.timeout_seconds)),
            check=False,
        )
        report["codex_returncode"] = int(completed.returncode)
        report["codex_completed"] = completed.returncode == 0
    except subprocess.TimeoutExpired:
        report["error"] = {"code": "CODEX_TIMEOUT", "message": "Codex acceptance run timed out."}
    except (OSError, ValueError) as exc:
        report["error"] = {"code": "CODEX_START_FAILED", "message": str(exc)}

    events = load_ledger(ledger_path)
    ledger = evaluate_ledger(events)
    report["ledger"] = ledger
    report["ledger_path"] = str(ledger_path.resolve())
    report["ledger_sha256"] = _sha256_file(ledger_path)
    report["ok"] = bool(report.get("codex_completed")) and bool(ledger.get("ok"))

    rendered = json.dumps(report, ensure_ascii=False, indent=2) + "\n"
    output.write_text(rendered, encoding="utf-8")
    print(rendered, end="")
    return 0 if report["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
