from __future__ import annotations

import hashlib
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from aiworkstation_osi.codex_acceptance import WORKFLOW_VERSION, evaluate_ledger
from aiworkstation_osi.contracts import TOOL_NAMES
from aiworkstation_osi.evidence_readiness import (
    evaluate_evidence_readiness,
    validate_codex_acceptance_report,
)


class EvidenceReadinessTests(unittest.TestCase):
    def _report(
        self,
        path: Path,
        *,
        successful_tools: tuple[str, ...] = TOOL_NAMES,
        **overrides,
    ) -> Path:
        ledger_path = path.with_name(path.stem + "-ledger.jsonl").resolve()
        events = [
            {
                "schema_version": "osi.codex-acceptance-ledger.v1",
                "timestamp": "2026-08-07T00:00:00Z",
                "level": "INFO",
                "event": "tool_invocation",
                "tool": tool,
                "outcome": "success",
                "duration_ms": 1.0,
                "error_code": "",
            }
            for tool in successful_tools
        ]
        ledger_path.write_text(
            "".join(json.dumps(event) + "\n" for event in events),
            encoding="utf-8",
        )
        ledger = evaluate_ledger(events)
        payload = {
            "schema_version": "osi.codex-acceptance.v1",
            "workflow_version": WORKFLOW_VERSION,
            "ok": ledger["ok"],
            "commit": "candidate-sha",
            "provider": "http",
            "base_url": "https://aiworkstation.cn",
            "codex_version": "codex-cli test",
            "codex_completed": True,
            "codex_returncode": 0,
            "ledger": ledger,
            "ledger_path": str(ledger_path),
            "ledger_sha256": hashlib.sha256(ledger_path.read_bytes()).hexdigest(),
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
            report_path = self._report(
                root / "codex.json",
                successful_tools=TOOL_NAMES[:-1],
                provider="mock",
            )
            with patch("aiworkstation_osi.evidence_readiness._git_head", return_value="candidate-sha"):
                result = validate_codex_acceptance_report(report_path, root=root)

        self.assertFalse(result["ok"])
        errors = " ".join(result["errors"])
        self.assertIn("did not pass", errors)
        self.assertIn("live HTTP provider", errors)
        self.assertIn("all six tools", errors)
        self.assertIn("missing tools", errors)

    def test_tampered_ledger_digest_fails_closed(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            report_path = self._report(root / "codex.json")
            payload = json.loads(report_path.read_text(encoding="utf-8"))
            Path(payload["ledger_path"]).write_text("{}\n", encoding="utf-8")
            with patch("aiworkstation_osi.evidence_readiness._git_head", return_value="candidate-sha"):
                result = validate_codex_acceptance_report(report_path, root=root)

        self.assertFalse(result["ok"])
        errors = " ".join(result["errors"])
        self.assertIn("digest", errors)
        self.assertIn("summary", errors)

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
