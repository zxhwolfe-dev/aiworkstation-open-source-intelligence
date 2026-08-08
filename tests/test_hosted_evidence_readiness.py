from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from aiworkstation_osi.hosted_evidence_readiness import evaluate_hosted_evidence_readiness


class HostedEvidenceReadinessTests(unittest.TestCase):
    def test_valid_hosted_evidence_drives_remote_and_gateway_gates(self) -> None:
        fake_report = {
            "code_ready": True,
            "external_alpha_ready": True,
            "hosted_private_alpha_ready": True,
            "public_launch_ready": False,
            "machine_evidence": {
                "ci": {"ok": True},
                "live_validation": {"ok": True},
                "codex": {"ok": True},
            },
            "checks": [
                {"id": "hosted-mcp-endpoint", "ok": True, "message": "old", "details": {}},
                {"id": "attestation-remote-mcp-tested", "ok": True, "message": "old", "details": {"operator_attested": True}},
                {"id": "attestation-hosted-gateway-protected", "ok": True, "message": "old", "details": {"operator_attested": True}},
            ],
        }
        hosted = {
            "ok": True,
            "path": "/tmp/hosted.json",
            "endpoint": "https://mcp.aiworkstation.cn/mcp",
            "errors": [],
        }
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            inputs = [root / name for name in ("ci.json", "live.json", "codex.json", "hosted.json")]
            for path in inputs:
                path.write_text("{}", encoding="utf-8")
            with patch("aiworkstation_osi.hosted_evidence_readiness._git_head", return_value="candidate-sha"), patch(
                "aiworkstation_osi.hosted_evidence_readiness.validate_hosted_remote_evidence",
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
                    expected_oauth_issuer="https://auth.example.com",
                )

        kwargs = evaluate.call_args.kwargs
        self.assertTrue(kwargs["remote_mcp_tested"])
        self.assertTrue(kwargs["hosted_gateway_protected"])
        self.assertEqual(kwargs["remote_mcp_url"], "https://mcp.aiworkstation.cn/mcp")
        self.assertTrue(result["machine_evidence"]["hosted_remote"]["ok"])
        for check in result["checks"][1:]:
            self.assertFalse(check["details"]["operator_attested"])
            self.assertTrue(check["details"]["evidence_verified"])
        self.assertTrue(result["checks"][0]["details"]["remote_evidence_verified"])

    def test_invalid_hosted_evidence_cannot_be_overridden(self) -> None:
        fake_report = {
            "code_ready": True,
            "external_alpha_ready": True,
            "hosted_private_alpha_ready": False,
            "public_launch_ready": False,
            "machine_evidence": {},
            "checks": [
                {"id": "hosted-mcp-endpoint", "ok": True, "message": "old", "details": {}},
                {"id": "attestation-remote-mcp-tested", "ok": False, "message": "old", "details": {"operator_attested": False}},
                {"id": "attestation-hosted-gateway-protected", "ok": False, "message": "old", "details": {"operator_attested": False}},
            ],
        }
        hosted = {
            "ok": False,
            "path": "/tmp/hosted.json",
            "endpoint": "https://mcp.aiworkstation.cn/mcp",
            "errors": ["wrong candidate"],
        }
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            inputs = [root / name for name in ("ci.json", "live.json", "codex.json", "hosted.json")]
            for path in inputs:
                path.write_text("{}", encoding="utf-8")
            with patch("aiworkstation_osi.hosted_evidence_readiness._git_head", return_value="candidate-sha"), patch(
                "aiworkstation_osi.hosted_evidence_readiness.validate_hosted_remote_evidence",
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
                    expected_oauth_issuer="https://auth.example.com",
                )

        kwargs = evaluate.call_args.kwargs
        self.assertFalse(kwargs["remote_mcp_tested"])
        self.assertFalse(kwargs["hosted_gateway_protected"])
        self.assertFalse(result["hosted_private_alpha_ready"])
        self.assertFalse(result["machine_evidence"]["hosted_remote"]["ok"])


if __name__ == "__main__":
    unittest.main()
