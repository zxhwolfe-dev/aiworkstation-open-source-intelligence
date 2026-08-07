"""Privacy-minimized structured runtime telemetry.

Events are written to stderr so stdio MCP protocol output on stdout is never
polluted. Tool arguments, queries, constraints, project IDs and raw request IDs
are intentionally not accepted by the event API.

When ``OSI_ACCEPTANCE_LEDGER_PATH`` is set to an absolute path, the same bounded
tool event is also appended as JSONL for local Codex acceptance testing. The
ledger is operator-controlled and never contains tool arguments or result data.
"""

from __future__ import annotations

import hashlib
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping

LOG_LEVELS = {"OFF": 100, "ERROR": 40, "WARNING": 30, "INFO": 20}
DEFAULT_LOG_LEVEL = "WARNING"


def _configured_threshold() -> int:
    value = os.getenv("OSI_LOG_LEVEL", DEFAULT_LOG_LEVEL).strip().upper()
    if value not in LOG_LEVELS:
        return LOG_LEVELS[DEFAULT_LOG_LEVEL]
    return LOG_LEVELS[value]


def _request_id_fingerprint(request_id: str) -> str:
    value = str(request_id or "").strip()
    if not value:
        return ""
    return "sha256:" + hashlib.sha256(value.encode("utf-8")).hexdigest()[:16]


def _timestamp() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _append_acceptance_event(payload: Mapping[str, Any]) -> None:
    """Best-effort append of one argument-free event for Codex acceptance runs."""

    configured = str(os.getenv("OSI_ACCEPTANCE_LEDGER_PATH") or "").strip()
    if not configured:
        return
    path = Path(configured).expanduser()
    if not path.is_absolute():
        return
    safe = {
        key: payload.get(key)
        for key in (
            "schema_version",
            "timestamp",
            "level",
            "event",
            "tool",
            "outcome",
            "duration_ms",
            "error_code",
        )
    }
    safe["schema_version"] = "osi.codex-acceptance-ledger.v1"
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(safe, ensure_ascii=False, separators=(",", ":")))
            handle.write("\n")
    except OSError:
        # Acceptance evidence must never become an availability dependency.
        return


def emit_tool_event(
    *,
    level: str,
    tool: str,
    outcome: str,
    duration_ms: float,
    request_id: str = "",
    error_code: str = "",
    extra: Mapping[str, Any] | None = None,
) -> None:
    """Emit one bounded JSON event without accepting user prompt content."""

    normalized_level = str(level or "INFO").strip().upper()
    severity = LOG_LEVELS.get(normalized_level, LOG_LEVELS["INFO"])

    safe_extra: dict[str, Any] = {}
    for key, value in (extra or {}).items():
        normalized_key = str(key)
        if normalized_key not in {
            "provider",
            "transport",
            "result_count",
            "unknown_count",
            "risk_count",
        }:
            continue
        if value is None or isinstance(value, (bool, int, float, str)):
            safe_extra[normalized_key] = value

    payload = {
        "schema_version": "osi.telemetry.tool.v1",
        "timestamp": _timestamp(),
        "level": normalized_level,
        "event": "tool_invocation",
        "tool": str(tool)[:128],
        "outcome": str(outcome)[:64],
        "duration_ms": round(max(0.0, float(duration_ms)), 3),
        "request_id_fingerprint": _request_id_fingerprint(request_id),
        "error_code": str(error_code)[:128],
        **safe_extra,
    }
    _append_acceptance_event(payload)
    if severity < _configured_threshold():
        return
    print(json.dumps(payload, ensure_ascii=False, separators=(",", ":")), file=sys.stderr, flush=True)
