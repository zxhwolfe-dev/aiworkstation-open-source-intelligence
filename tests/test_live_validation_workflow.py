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

    def test_workflow_supports_automatic_and_manual_read_only_validation(self) -> None:
        self.assertIn("push:", self.content)
        self.assertIn("branches: [main]", self.content)
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

    def test_user_inputs_are_passed_through_environment_not_shell_templates(self) -> None:
        # The expression may provide safe defaults for automatic push runs, but
        # workflow inputs must still cross into shell/Python only through env.
        self.assertIn("BASE_URL: ${{ inputs.base_url", self.content)
        self.assertIn("PROJECT_ID: ${{ inputs.project_id", self.content)
        self.assertIn('--base-url "$BASE_URL"', self.content)
        self.assertIn('--project-id "$PROJECT_ID"', self.content)
        self.assertNotIn('--base-url "${{ inputs.base_url', self.content)
        self.assertNotIn('--project-id "${{ inputs.project_id', self.content)
        self.assertIn('os.environ["BASE_URL"]', self.content)
        self.assertIn('os.environ["PROJECT_ID"]', self.content)

    def test_workflow_does_not_duplicate_selector_preflight(self) -> None:
        # The selector task transport is exercised by the real probe/capture path.
        # Avoid a second heavy selector call merely for diagnostics.
        self.assertNotIn("Diagnose public evidence path availability", self.content)
        self.assertIn("Run English and Chinese public probes", self.content)
        self.assertIn("Capture sanitized public contracts", self.content)

    def test_replay_uses_capture_manifest_instead_of_duplicate_identity_flags(self) -> None:
        replay_block = self.content.split("Validate and replay captured contracts", 1)[1].split(
            "Scan artifacts for forbidden JSON keys", 1
        )[0]
        self.assertIn("osi-replay-contracts", replay_block)
        self.assertIn('--directory "$directory"', replay_block)
        self.assertIn('--output "$VALIDATION_ROOT/replay-$locale.json"', replay_block)
        self.assertNotIn("--project-id", replay_block)
        self.assertNotIn("--locale", replay_block)

    def test_validation_precedes_artifact_upload(self) -> None:
        scan_position = self.content.index("Scan artifacts for forbidden JSON keys")
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

    def test_forbidden_key_scan_targets_json_keys_not_free_text(self) -> None:
        self.assertIn("forbidden_key_pattern", self.content)
        self.assertIn('"[[:space:]]*:', self.content)
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
