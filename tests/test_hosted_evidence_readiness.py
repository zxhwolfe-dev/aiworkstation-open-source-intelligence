from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from aiworkstation_osi.hosted_evidence_readiness import evaluate_hosted_evidence_readiness


class HostedEvidenceReadinessTests(unittest.TestCase):
    def _fake_report(self, hosted_ready: bool) -> dict:
        return {
            "code_ready": True,
            "external_alpha_ready": True,
            "hosted_private_alpha_ready": hosted_ready,
            "public_launch_ready": False,
            "machine_evidence": {
                "ci": {"ok": True},
                "live_validation": {"ok": True},
                "codex": {"ok": True},
            },
            "checks": [
                {"id": "hosted-mcp-endpoint", "ok": True, "message": "old", "details": {}},
                {"id": "attestation-remote-mcp-tested", "ok": hosted_ready, "message": "old", "details": {"operator_attested": hosted_ready}},
                {"id": "attestation-hosted-gateway-protected", "ok": hosted_ready, "message": "old", "details": {"operator_attested": hosted_ready}},
            ],
        }

    def _inputs(self, root: Path) -> list[Path]:
        values = [root / name for name in ("ci.json", "live.json", "codex.json", "hosted.json")]
        for path in values:
            path.write_text("{}", encoding="utf-8")
        return values

    def test_valid_public_hosted_evidence_drives_remote_and_gateway_gates(self) -> None:
        fake_report = self._fake_report(True)
        hosted = {
            "ok": True,
            "path": "/tmp/hosted.json",
            "endpoint": "https://mcp.aiworkstation.cn/mcp",
            "errors": [],
        }
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            inputs = self._inputs(root)
            with patch("aiworkstation_osi.hosted_evidence_readiness._git_head", return_value="candidate-sha"), patch(
                "aiworkstation_osi.hosted_evidence_readiness.validate_public_hosted_remote_evidence",
                return_value=hosted,
            ) as public_validator, patch(
                "aiworkstation_osi.hosted_evidence_readiness.evaluate_evidence_readiness",
                return_value=fake_report,
            ) as evaluate:
                result = evaluate_hosted_evidence_readiness(
                    root,
                    ci_evidence=inputs[0],
                    live_validation_evidence=inputs[1],
                    codex_acceptance_report=inputs[2],
                    hosted_remote_evidence=inputs[3],
                    artifact_reviewed=True,
                    reviewer="Human Reviewer",
                    expected_base_url="https://aiworkstation.cn",
                    expected_hosted_mcp_url="https://mcp.aiworkstation.cn/mcp",
                    expected_access_mode="public",
                )

        public_validator.assert_called_once()
        kwargs = evaluate.call_args.kwargs
        self.assertTrue(kwargs["remote_mcp_tested"])
        self.assertTrue(kwargs["hosted_gateway_protected"])
        self.assertEqual(kwargs["remote_mcp_url"], "https://mcp.aiworkstation.cn/mcp")
        self.assertEqual(result["hosted_access_mode"], "public")
        self.assertTrue(result["machine_evidence"]["hosted_remote"]["ok"])
        self.assertIn("anonymous Hosted", result["checks"][1]["message"])
        self.assertIn("IP-rate-limit", result["checks"][2]["message"])
        for check in result["checks"][1:]:
            self.assertFalse(check["details"]["operator_attested"])
            self.assertTrue(check["details"]["evidence_verified"])
        self.assertTrue(result["checks"][0]["details"]["remote_evidence_verified"])

    def test_oauth_access_mode_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            inputs = self._inputs(root)
            with patch("aiworkstation_osi.hosted_evidence_readiness._git_head", return_value="candidate-sha"):
                with self.assertRaises(ValueError) as context:
                    evaluate_hosted_evidence_readiness(
                        root,
                        ci_evidence=inputs[0],
                        live_validation_evidence=inputs[1],
                        codex_acceptance_report=inputs[2],
                        hosted_remote_evidence=inputs[3],
                        artifact_reviewed=True,
                        reviewer="Human Reviewer",
                        expected_base_url="https://aiworkstation.cn",
                        expected_hosted_mcp_url="https://mcp.aiworkstation.cn/mcp",
                        expected_access_mode="oauth",
                        expected_oauth_issuer="https://auth.example.com",
                    )
        self.assertIn("OAuth Hosted mode is disabled", str(context.exception))

    def test_invalid_public_evidence_cannot_be_overridden(self) -> None:
        fake_report = self._fake_report(False)
        hosted = {
            "ok": False,
            "path": "/tmp/hosted.json",
            "endpoint": "https://mcp.aiworkstation.cn/mcp",
            "errors": ["wrong candidate"],
        }
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            inputs = self._inputs(root)
            with patch("aiworkstation_osi.hosted_evidence_readiness._git_head", return_value="candidate-sha"), patch(
                "aiworkstation_osi.hosted_evidence_readiness.validate_public_hosted_remote_evidence",
                return_value=hosted,
            ), patch(
                "aiworkstation_osi.hosted_evidence_readiness.evaluate_evidence_readiness",
                return_value=fake_report,
            ) as evaluate:
                result = evaluate_hosted_evidence_readiness(
                    root,
                    ci_evidence=inputs[0],
                    live_validation_evidence=inputs[1],
                    codex_acceptance_report=inputs[2],
                    hosted_remote_evidence=inputs[3],
                    artifact_reviewed=True,
                    reviewer="Human Reviewer",
                    expected_base_url="https://aiworkstation.cn",
                    expected_hosted_mcp_url="https://mcp.aiworkstation.cn/mcp",
                )

        kwargs = evaluate.call_args.kwargs
        self.assertFalse(kwargs["remote_mcp_tested"])
        self.assertFalse(kwargs["hosted_gateway_protected"])
        self.assertFalse(result["hosted_private_alpha_ready"])
        self.assertFalse(result["machine_evidence"]["hosted_remote"]["ok"])


if __name__ == "__main__":
    unittest.main()
