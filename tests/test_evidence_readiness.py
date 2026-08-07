from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from aiworkstation_osi.contracts import TOOL_NAMES
from aiworkstation_osi.evidence_readiness import (
    evaluate_evidence_readiness,
    validate_codex_acceptance_report,
)


class EvidenceReadinessTests(unittest.TestCase):
    def _report(self, path: Path, **overrides) -> Path:
        payload = {
            "schema_version": "osi.codex-acceptance.v1",
            "ok": True,
            "commit": "candidate-sha",
            "provider": "http",
            "base_url": "https://aiworkstation.cn",
            "codex_version": "codex-cli test",
            "codex_completed": True,
            "codex_returncode": 0,
            "ledger": {
                "expected_tools": list(TOOL_NAMES),
                "successful_tools": list(TOOL_NAMES),
                "missing_tools": [],
                "success_counts": {tool: 1 for tool in TOOL_NAMES},
                "event_count": len(TOOL_NAMES),
            },
        }
        payload.update(overrides)
        path.write_text(json.dumps(payload), encoding="utf-8")
        return path

    def test_valid_live_report_is_bound_to_current_candidate(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            report_path = self._report(root / "codex.json")
            with patch("aiworkstation_osi.evidence_readiness._git_head", return_value="candidate-sha"):
                result = validate_codex_acceptance_report(report_path, root=root)

        self.assertTrue(result["ok"])
        self.assertEqual(result["successful_tools"], list(TOOL_NAMES))
        self.assertEqual(result["candidate_commit"], "candidate-sha")
        self.assertEqual(result["errors"], [])

    def test_report_from_different_commit_fails_closed(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            report_path = self._report(root / "codex.json")
            with patch("aiworkstation_osi.evidence_readiness._git_head", return_value="newer-sha"):
                result = validate_codex_acceptance_report(report_path, root=root)

        self.assertFalse(result["ok"])
        self.assertIn("different candidate commit", " ".join(result["errors"]))

    def test_mock_or_incomplete_tool_evidence_cannot_satisfy_live_gate(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            report_path = self._report(root / "codex.json", provider="mock")
            payload = json.loads(report_path.read_text(encoding="utf-8"))
            missing = TOOL_NAMES[-1]
            payload["ledger"]["successful_tools"] = list(TOOL_NAMES[:-1])
            payload["ledger"]["missing_tools"] = [missing]
            payload["ledger"]["success_counts"][missing] = 0
            report_path.write_text(json.dumps(payload), encoding="utf-8")
            with patch("aiworkstation_osi.evidence_readiness._git_head", return_value="candidate-sha"):
                result = validate_codex_acceptance_report(report_path, root=root)

        self.assertFalse(result["ok"])
        errors = " ".join(result["errors"])
        self.assertIn("live HTTP provider", errors)
        self.assertIn("all six tools", errors)
        self.assertIn("missing tools", errors)

    def test_wrapper_derives_codex_gate_from_report_instead_of_manual_boolean(self) -> None:
        fake_base = {
            "code_ready": True,
            "external_alpha_ready": False,
            "hosted_private_alpha_ready": False,
            "checks": [{
                "id": "attestation-codex-tested",
                "ok": True,
                "message": "old",
                "details": {"operator_attested": True},
            }],
        }
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            report_path = self._report(root / "codex.json")
            with patch("aiworkstation_osi.evidence_readiness._git_head", return_value="candidate-sha"), patch(
                "aiworkstation_osi.evidence_readiness.evaluate_release_readiness",
                return_value=fake_base,
            ) as evaluate:
                result = evaluate_evidence_readiness(
                    root,
                    codex_acceptance_report=report_path,
                )

        self.assertTrue(result["codex_acceptance_evidence"]["ok"])
        self.assertTrue(evaluate.call_args.kwargs["codex_tested"])
        check = result["checks"][0]
        self.assertFalse(check["details"]["operator_attested"])
        self.assertTrue(check["details"]["evidence_verified"])
        self.assertIn("candidate-bound", check["message"])


if __name__ == "__main__":
    unittest.main()
