from __future__ import annotations

import io
import json
import os
import tempfile
import unittest
from contextlib import redirect_stderr
from pathlib import Path
from unittest.mock import patch

from aiworkstation_osi.codex_acceptance import (
    SERVER_NAME,
    build_codex_command,
    evaluate_ledger,
    retry_acceptance_prompt,
)
from aiworkstation_osi.contracts import TOOL_NAMES
from aiworkstation_osi.telemetry import emit_tool_event


class CodexAcceptanceTests(unittest.TestCase):
    def test_command_is_ephemeral_read_only_and_enables_exact_tool_set(self) -> None:
        root = Path("/tmp/osi-repo")
        ledger = Path("/tmp/osi-ledger.jsonl")
        command = build_codex_command(
            codex_bin="/usr/bin/codex",
            root=root,
            mcp_command="/tmp/osi-repo/.venv/bin/osi-mcp",
            ledger_path=ledger,
            provider="http",
            base_url="https://aiworkstation.cn",
        )

        self.assertEqual(command[:2], ["/usr/bin/codex", "exec"])
        self.assertIn("--ephemeral", command)
        self.assertIn("--sandbox", command)
        self.assertIn("read-only", command)
        rendered = "\n".join(command)
        self.assertIn('approval_policy="never"', rendered)
        self.assertNotIn("--ask-for-approval", command)
        self.assertIn(f"mcp_servers.{SERVER_NAME}.required=true", rendered)
        self.assertIn(
            f'mcp_servers.{SERVER_NAME}.default_tools_approval_mode="approve"',
            rendered,
        )
        self.assertIn("OSI_ACCEPTANCE_LEDGER_PATH", rendered)
        self.assertIn("AIWORKSTATION_RADAR_BASE_URL", rendered)
        for tool in TOOL_NAMES:
            self.assertIn(tool, rendered)

    def test_retry_prompt_targets_only_missing_tools(self) -> None:
        prompt = retry_acceptance_prompt(["find_alternatives"])
        self.assertIn("find_alternatives", prompt)
        self.assertIn("at least one successful tool result", prompt)
        for tool in TOOL_NAMES:
            if tool != "find_alternatives":
                self.assertNotIn(f". {tool}:", prompt)

    def test_ledger_requires_success_from_all_six_tools(self) -> None:
        events = [
            {
                "schema_version": "osi.codex-acceptance-ledger.v1",
                "tool": tool,
                "outcome": "success",
            }
            for tool in TOOL_NAMES
        ]
        report = evaluate_ledger(events)
        self.assertTrue(report["ok"])
        self.assertEqual(report["missing_tools"], [])
        self.assertEqual(set(report["successful_tools"]), set(TOOL_NAMES))

        incomplete = evaluate_ledger(events[:-1])
        self.assertFalse(incomplete["ok"])
        self.assertEqual(incomplete["missing_tools"], [TOOL_NAMES[-1]])

    def test_acceptance_ledger_records_success_even_when_info_stderr_is_suppressed(self) -> None:
        stream = io.StringIO()
        with tempfile.TemporaryDirectory() as temp_dir:
            ledger = Path(temp_dir) / "acceptance.jsonl"
            with patch.dict(
                os.environ,
                {
                    "OSI_ACCEPTANCE_LEDGER_PATH": str(ledger),
                    "OSI_LOG_LEVEL": "WARNING",
                },
                clear=False,
            ), redirect_stderr(stream):
                emit_tool_event(
                    level="INFO",
                    tool="search_ai_projects",
                    outcome="success",
                    duration_ms=3.5,
                    request_id="private-request-id",
                    extra={
                        "result_count": 2,
                        "query": "SECRET QUERY MUST NOT APPEAR",
                    },
                )

            self.assertEqual(stream.getvalue(), "")
            payload = json.loads(ledger.read_text(encoding="utf-8"))
            self.assertEqual(payload["schema_version"], "osi.codex-acceptance-ledger.v1")
            self.assertEqual(payload["tool"], "search_ai_projects")
            self.assertEqual(payload["outcome"], "success")
            rendered = ledger.read_text(encoding="utf-8")
            self.assertNotIn("private-request-id", rendered)
            self.assertNotIn("SECRET QUERY MUST NOT APPEAR", rendered)
            self.assertNotIn("result_count", payload)

    def test_relative_acceptance_ledger_path_is_ignored(self) -> None:
        with patch.dict(
            os.environ,
            {"OSI_ACCEPTANCE_LEDGER_PATH": "relative-ledger.jsonl", "OSI_LOG_LEVEL": "OFF"},
            clear=False,
        ):
            emit_tool_event(
                level="INFO",
                tool="search_ai_projects",
                outcome="success",
                duration_ms=1,
            )
        self.assertFalse(Path("relative-ledger.jsonl").exists())


if __name__ == "__main__":
    unittest.main()
