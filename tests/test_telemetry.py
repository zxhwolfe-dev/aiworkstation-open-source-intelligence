from __future__ import annotations

import io
import json
import os
import unittest
from contextlib import redirect_stderr
from unittest.mock import patch

from aiworkstation_osi.app import create_default_registry
from aiworkstation_osi.mcp_server import _invoke
from aiworkstation_osi.telemetry import emit_tool_event


class TelemetryTests(unittest.TestCase):
    def test_success_event_logs_only_safe_counts_and_request_id_fingerprint(self) -> None:
        stream = io.StringIO()
        with patch.dict(os.environ, {"OSI_LOG_LEVEL": "INFO"}, clear=False), redirect_stderr(stream):
            result = _invoke(
                create_default_registry(),
                "search_ai_projects",
                {
                    "query": "TOP SECRET QUERY TEXT",
                    "constraints": [{"id": "secret_constraint", "value": "DO NOT LOG ME", "polarity": "required"}],
                    "locale": "en",
                    "request_id": "private-correlation-id",
                },
            )

        self.assertEqual(result["tool"], "search_ai_projects")
        rendered = stream.getvalue().strip()
        payload = json.loads(rendered)
        self.assertEqual(payload["event"], "tool_invocation")
        self.assertEqual(payload["tool"], "search_ai_projects")
        self.assertEqual(payload["outcome"], "success")
        self.assertTrue(payload["request_id_fingerprint"].startswith("sha256:"))
        self.assertNotIn("private-correlation-id", rendered)
        self.assertNotIn("TOP SECRET QUERY TEXT", rendered)
        self.assertNotIn("DO NOT LOG ME", rendered)
        self.assertNotIn("constraints", payload)
        self.assertNotIn("query", payload)

    def test_tool_error_logs_public_code_not_invalid_input_value(self) -> None:
        stream = io.StringIO()
        sensitive_value = "SENSITIVE" * 40
        with patch.dict(os.environ, {"OSI_LOG_LEVEL": "WARNING"}, clear=False), redirect_stderr(stream):
            result = _invoke(
                create_default_registry(),
                "get_project_facts",
                {"project_id": sensitive_value, "request_id": "request-secret"},
            )
        self.assertEqual(result["schema_version"], "osi.error.v2")
        rendered = stream.getvalue().strip()
        payload = json.loads(rendered)
        self.assertEqual(payload["outcome"], "tool_error")
        self.assertEqual(payload["error_code"], "INVALID_INPUT")
        self.assertNotIn(sensitive_value, rendered)
        self.assertNotIn("request-secret", rendered)

    def test_default_warning_level_suppresses_success_events(self) -> None:
        stream = io.StringIO()
        with patch.dict(os.environ, {}, clear=True), redirect_stderr(stream):
            emit_tool_event(
                level="INFO",
                tool="search_ai_projects",
                outcome="success",
                duration_ms=1.5,
                request_id="request",
                extra={"result_count": 2},
            )
        self.assertEqual(stream.getvalue(), "")

    def test_extra_fields_are_allowlisted(self) -> None:
        stream = io.StringIO()
        with patch.dict(os.environ, {"OSI_LOG_LEVEL": "INFO"}, clear=False), redirect_stderr(stream):
            emit_tool_event(
                level="INFO",
                tool="search_ai_projects",
                outcome="success",
                duration_ms=2,
                extra={
                    "result_count": 3,
                    "provider": "mock",
                    "query": "must not appear",
                    "authorization": "must not appear",
                },
            )
        rendered = stream.getvalue().strip()
        payload = json.loads(rendered)
        self.assertEqual(payload["result_count"], 3)
        self.assertEqual(payload["provider"], "mock")
        self.assertNotIn("query", payload)
        self.assertNotIn("authorization", payload)
        self.assertNotIn("must not appear", rendered)


if __name__ == "__main__":
    unittest.main()
