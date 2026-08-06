from __future__ import annotations

import unittest
from pathlib import Path


class LiveValidationWorkflowTests(unittest.TestCase):
    ROOT = Path(__file__).resolve().parents[1]

    @classmethod
    def setUpClass(cls) -> None:
        cls.content = (
            cls.ROOT / ".github" / "workflows" / "live-contract-validation.yml"
        ).read_text(encoding="utf-8")

    def test_workflow_is_manual_and_read_only(self) -> None:
        self.assertIn("workflow_dispatch:", self.content)
        self.assertNotIn("schedule:", self.content)
        self.assertNotIn("pull_request:", self.content)
        self.assertIn("permissions:\n  contents: read", self.content)
        self.assertNotIn("contents: write", self.content)

    def test_public_origin_is_allowlisted(self) -> None:
        self.assertIn("type: choice", self.content)
        self.assertIn("https://aiworkstation.cn", self.content)
        self.assertIn("https://useaistation.com", self.content)
        self.assertIn("allowed_hosts", self.content)
        self.assertIn("parsed.scheme != \"https\"", self.content)

    def test_validation_precedes_artifact_upload(self) -> None:
        scan_position = self.content.index("Scan artifacts for forbidden keys")
        summary_position = self.content.index("Write validation summary")
        upload_position = self.content.index("Upload sanitized validation bundle")
        self.assertLess(scan_position, summary_position)
        self.assertLess(summary_position, upload_position)
        self.assertNotIn("if: always()", self.content)

    def test_workflow_runs_both_local_and_live_gates(self) -> None:
        for command in (
            "python -m unittest discover -s tests -v",
            "osi-validate-plugin --root .",
            "osi-probe",
            "osi-capture-contracts",
            "osi-validate-contracts",
            "osi-replay-contracts",
        ):
            with self.subTest(command=command):
                self.assertIn(command, self.content)

    def test_forbidden_key_scan_covers_sensitive_and_internal_fields(self) -> None:
        for marker in (
            "authorization",
            "cookie",
            "access[_-]?token",
            "password",
            "email",
            "source_hash",
            "evidence_ids",
            "claim_refs",
            "publication_version",
        ):
            with self.subTest(marker=marker):
                self.assertIn(marker, self.content)


if __name__ == "__main__":
    unittest.main()
