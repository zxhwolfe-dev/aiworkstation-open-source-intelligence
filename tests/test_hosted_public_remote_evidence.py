from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from aiworkstation_osi.contracts import TOOL_NAMES
from aiworkstation_osi.hosted_public_remote_evidence import (
    PUBLIC_GATEWAY_POLICY,
    PUBLIC_HOSTED_REMOTE_SCHEMA,
    validate_public_hosted_remote_evidence,
)


class PublicHostedRemoteEvidenceTests(unittest.TestCase):
    candidate = "a" * 40
    endpoint = "https://mcp.example.com/mcp"

    def _report(self) -> dict:
        return {
            "schema_version": PUBLIC_HOSTED_REMOTE_SCHEMA,
            "ok": True,
            "profile": "hosted-public",
            "endpoint": self.endpoint,
            "commit": self.candidate,
            "server_version": f"0.1.0+git.{self.candidate}",
            "deployment_commit": self.candidate,
            "protocol_version": "2025-06-18",
            "auth": {"mode": "none"},
            "gateway_boundary": {
                "ok": True,
                "status": 405,
                "policy": PUBLIC_GATEWAY_POLICY,
                "errors": [],
            },
            "tools": list(TOOL_NAMES),
            "checks": [
                {"id": "deployment-identity", "ok": True},
                {"id": "tool-set", "ok": True},
                {"id": "tool-annotations", "ok": True},
                {"id": "search-invocation", "ok": True},
            ],
            "search": {"is_error": False, "tool": "search_ai_projects"},
        }

    def _validate(self, report: dict) -> dict:
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "remote.json"
            path.write_text(json.dumps(report), encoding="utf-8")
            return validate_public_hosted_remote_evidence(
                path,
                candidate_commit=self.candidate,
                expected_endpoint=self.endpoint,
            )

    def test_valid_public_report_is_candidate_and_gateway_bound(self) -> None:
        result = self._validate(self._report())
        self.assertTrue(result["ok"])
        self.assertTrue(result["gateway_policy_verified"])
        self.assertEqual(result["tools"], list(TOOL_NAMES))

    def test_oauth_or_premium_surface_cannot_certify_public_mode(self) -> None:
        report = self._report()
        report["auth"] = {"mode": "oauth"}
        report["tools"] = list(TOOL_NAMES) + ["deep_research_ai_projects"]
        result = self._validate(report)
        self.assertFalse(result["ok"])
        self.assertTrue(any("auth mode none" in error for error in result["errors"]))
        self.assertTrue(any("exactly nine" in error for error in result["errors"]))

    def test_missing_gateway_policy_or_wrong_candidate_fails_closed(self) -> None:
        report = self._report()
        report["commit"] = "b" * 40
        report["gateway_boundary"]["ok"] = False
        report["gateway_boundary"]["policy"] = ""
        result = self._validate(report)
        self.assertFalse(result["ok"])
        self.assertTrue(any("different candidate" in error for error in result["errors"]))
        self.assertTrue(any("gateway" in error.lower() for error in result["errors"]))


if __name__ == "__main__":
    unittest.main()
