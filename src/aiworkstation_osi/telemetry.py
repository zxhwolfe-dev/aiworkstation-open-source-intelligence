"""Privacy-minimized structured runtime telemetry.

Events are written to stderr so stdio MCP protocol output on stdout is never
polluted. Tool arguments, queries, constraints, project IDs and raw request IDs
are intentionally not accepted by the event API.
"""

from __future__ import annotations

import hashlib
import json
import os
import sys
from datetime import datetime, timezone
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
    if severity < _configured_threshold():
        return

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
    print(json.dumps(payload, ensure_ascii=False, separators=(",", ":")), file=sys.stderr, flush=True)
