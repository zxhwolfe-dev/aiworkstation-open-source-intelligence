from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from aiworkstation_osi.release_readiness import (
    READINESS_SCHEMA_VERSION,
    evaluate_release_readiness,
)


class ReleaseReadinessTests(unittest.TestCase):
    ROOT = Path(__file__).resolve().parents[1]

    def test_current_tree_is_code_ready_but_not_operationally_signed_off(self) -> None:
        report = evaluate_release_readiness(self.ROOT)

        self.assertEqual(report["schema_version"], READINESS_SCHEMA_VERSION)
        self.assertTrue(report["code_ready"])
        self.assertFalse(report["external_alpha_ready"])
        self.assertFalse(report["hosted_private_alpha_ready"])
        self.assertFalse(report["public_launch_ready"])
        self.assertEqual(report["code_blockers"], [])
        rendered = " ".join(report["operational_blockers"])
        self.assertIn("production contract capture", rendered)
        self.assertIn("python 3.10", rendered)
        self.assertIn("python 3.12", rendered)
        self.assertIn("codex", rendered)
        self.assertIn("artifact reviewer", rendered)
        hosted = " ".join(report["hosted_alpha_blockers"])
        self.assertIn("endpoint URL", hosted)
        self.assertIn("smoke test", hosted)
        self.assertIn("gateway", hosted)

    def test_operator_attestations_cannot_replace_contract_evidence(self) -> None:
        report = evaluate_release_readiness(
            self.ROOT,
            ci_python310_passed=True,
            ci_python312_passed=True,
            codex_tested=True,
            artifact_reviewed=True,
            live_validation_run_id="123456789",
            reviewer="reviewer-name",
        )

        self.assertTrue(report["code_ready"])
        self.assertFalse(report["external_alpha_ready"])
        self.assertTrue(report["attestations"]["artifact_reviewed"])
        blockers = " ".join(report["operational_blockers"])
        self.assertIn("en production contract capture", blockers)
        self.assertIn("zh production contract capture", blockers)

    def test_hosted_attestations_cannot_replace_skills_alpha_gates(self) -> None:
        report = evaluate_release_readiness(
            self.ROOT,
            remote_mcp_tested=True,
            remote_mcp_url="https://mcp.example.com/mcp",
            hosted_gateway_protected=True,
        )

        self.assertTrue(report["code_ready"])
        self.assertFalse(report["external_alpha_ready"])
        self.assertFalse(report["hosted_private_alpha_ready"])
        self.assertIn(
            "complete-Plugin external-alpha gates are not complete",
            report["hosted_alpha_blockers"],
        )

    def test_hosted_endpoint_must_be_credential_free_https(self) -> None:
        for url in (
            "http://mcp.example.com/mcp",
            "https://user:pass@mcp.example.com/mcp",
            "https://mcp.example.com/mcp?token=secret",
        ):
            with self.subTest(url=url):
                report = evaluate_release_readiness(
                    self.ROOT,
                    remote_mcp_tested=True,
                    remote_mcp_url=url,
                    hosted_gateway_protected=True,
                )
                endpoint = next(
                    check for check in report["checks"]
                    if check["id"] == "hosted-mcp-endpoint"
                )
                self.assertFalse(endpoint["ok"])
                self.assertFalse(report["hosted_private_alpha_ready"])

    def test_missing_repository_files_fail_code_readiness(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            report = evaluate_release_readiness(Path(temp_dir))

        self.assertFalse(report["code_ready"])
        self.assertFalse(report["external_alpha_ready"])
        self.assertFalse(report["hosted_private_alpha_ready"])
        self.assertTrue(report["code_blockers"])
        required = next(
            check for check in report["checks"]
            if check["id"] == "required-repository-paths"
        )
        self.assertFalse(required["ok"])
        self.assertIn("README.md", required["details"]["missing"])
        self.assertIn("Dockerfile", required["details"]["missing"])
        self.assertIn(
            "skills/ai-open-source-intelligence/SKILL.md",
            required["details"]["missing"],
        )

    def test_public_launch_remains_blocked_after_data_only_hosted_alpha(self) -> None:
        report = evaluate_release_readiness(self.ROOT)

        self.assertFalse(report["public_launch_ready"])
        blockers = " ".join(report["public_launch_blockers"]).lower()
        self.assertIn("hosted privacy/terms", blockers)
        self.assertIn("anonymous-usage monitoring", blockers)
        self.assertIn("platform review", blockers)
        self.assertIn("directory", blockers)
        self.assertNotIn("oauth", blockers)
        self.assertNotIn("native per-user oauth", blockers)


if __name__ == "__main__":
    unittest.main()
