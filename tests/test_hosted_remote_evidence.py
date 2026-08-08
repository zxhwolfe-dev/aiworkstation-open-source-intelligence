from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from aiworkstation_osi.hosted_remote_evidence import (
    HOSTED_PREMIUM_TOOL,
    HOSTED_REMOTE_SCHEMA,
    expected_hosted_tools,
    validate_hosted_remote_evidence,
)


class HostedRemoteEvidenceTests(unittest.TestCase):
    def _write_report(self, path: Path, **overrides) -> Path:
        tools = list(expected_hosted_tools())
        payload = {
            "schema_version": HOSTED_REMOTE_SCHEMA,
            "ok": True,
            "commit": "candidate-sha",
            "profile": "hosted",
            "endpoint": "https://mcp.aiworkstation.cn/mcp",
            "protocol_version": "2026-07-28",
            "auth": {"mode": "oauth"},
            "oauth_boundary": {
                "ok": True,
                "challenge_status": 401,
                "resource": "https://mcp.aiworkstation.cn/mcp",
                "authorization_servers": ["https://auth.example.com"],
            },
            "tools": tools,
            "checks": [
                {"id": "tool-set", "ok": True},
                {"id": "tool-annotations", "ok": True},
                {"id": "search-invocation", "ok": True},
            ],
            "search": {
                "is_error": False,
                "tool": "search_ai_projects",
                "schema_version": "osi.tool-result.v1",
            },
        }
        payload.update(overrides)
        path.write_text(json.dumps(payload), encoding="utf-8")
        return path

    def test_valid_report_is_candidate_and_oauth_bound(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            report = self._write_report(Path(temp_dir) / "hosted.json")
            result = validate_hosted_remote_evidence(
                report,
                candidate_commit="candidate-sha",
                expected_endpoint="https://mcp.aiworkstation.cn/mcp",
                expected_issuer="https://auth.example.com",
            )

        self.assertTrue(result["ok"])
        self.assertTrue(result["oauth_boundary_verified"])
        self.assertTrue(result["search_verified"])
        self.assertIn(HOSTED_PREMIUM_TOOL, result["tools"])
        self.assertEqual(result["errors"], [])

    def test_different_candidate_fails_closed(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            report = self._write_report(Path(temp_dir) / "hosted.json")
            result = validate_hosted_remote_evidence(
                report,
                candidate_commit="newer-sha",
                expected_endpoint="https://mcp.aiworkstation.cn/mcp",
                expected_issuer="https://auth.example.com",
            )

        self.assertFalse(result["ok"])
        self.assertIn("different candidate commit", " ".join(result["errors"]))

    def test_missing_premium_or_authentication_cannot_pass(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "hosted.json"
            report = self._write_report(
                path,
                tools=list(expected_hosted_tools())[:-1],
                auth={"mode": "none"},
            )
            result = validate_hosted_remote_evidence(
                report,
                candidate_commit="candidate-sha",
                expected_endpoint="https://mcp.aiworkstation.cn/mcp",
                expected_issuer="https://auth.example.com",
            )

        self.assertFalse(result["ok"])
        rendered = " ".join(result["errors"])
        self.assertIn("authenticated MCP access", rendered)
        self.assertIn("nine standard tools plus Premium", rendered)

    def test_wrong_issuer_or_failed_search_cannot_pass(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "hosted.json"
            report = self._write_report(
                path,
                oauth_boundary={
                    "ok": True,
                    "challenge_status": 401,
                    "resource": "https://mcp.aiworkstation.cn/mcp",
                    "authorization_servers": ["https://wrong.example.com"],
                },
                checks=[
                    {"id": "tool-set", "ok": True},
                    {"id": "tool-annotations", "ok": True},
                    {"id": "search-invocation", "ok": False},
                ],
                search={"is_error": True, "tool": "search_ai_projects"},
            )
            result = validate_hosted_remote_evidence(
                report,
                candidate_commit="candidate-sha",
                expected_endpoint="https://mcp.aiworkstation.cn/mcp",
                expected_issuer="https://auth.example.com",
            )

        self.assertFalse(result["ok"])
        rendered = " ".join(result["errors"])
        self.assertIn("expected issuer", rendered)
        self.assertIn("search-invocation", rendered)


if __name__ == "__main__":
    unittest.main()
