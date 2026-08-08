from __future__ import annotations

import unittest
from pathlib import Path


class RadarBrowseValidationWorkflowTests(unittest.TestCase):
    ROOT = Path(__file__).resolve().parents[1]

    @classmethod
    def setUpClass(cls) -> None:
        cls.content = (cls.ROOT / ".github" / "workflows" / "radar-browse-validation.yml").read_text(
            encoding="utf-8"
        )

    def test_workflow_runs_for_every_main_candidate_and_can_be_manual(self) -> None:
        self.assertIn("push:", self.content)
        self.assertIn("branches: [main]", self.content)
        self.assertIn("workflow_dispatch:", self.content)
        self.assertIn("cancel-in-progress: true", self.content)
        self.assertIn("contents: read", self.content)

    def test_workflow_probes_both_locales_and_all_browse_dimensions(self) -> None:
        self.assertIn("aiworkstation_osi.radar_browse_probe", self.content)
        self.assertIn("--locale en", self.content)
        self.assertIn("--locale zh", self.content)
        # The Python probe itself dynamically exercises rankings, collections,
        # categories, scenarios, Skills listing and Skill detail.
        probe = (self.ROOT / "src" / "aiworkstation_osi" / "radar_browse_probe.py").read_text(
            encoding="utf-8"
        )
        for value in ("rankings", "collections", "categories", "scenarios"):
            self.assertIn(f'("{value}"', probe)
        self.assertIn("browse_radar_skills", probe)
        self.assertIn("skill_id", probe)

    def test_evidence_is_candidate_bound_and_artifact_uploaded_only_after_success(self) -> None:
        self.assertIn('"schema_version": "osi.radar-browse-evidence.v1"', self.content)
        self.assertIn('"commit": os.environ.get("GITHUB_SHA", "")', self.content)
        self.assertIn('"repository": os.environ.get("GITHUB_REPOSITORY", "")', self.content)
        self.assertIn('"browse_en": True', self.content)
        self.assertIn('"browse_zh": True', self.content)
        self.assertIn("actions/upload-artifact@v4", self.content)
        self.assertIn("if-no-files-found: error", self.content)

    def test_user_input_is_not_embedded_directly_in_shell_commands(self) -> None:
        self.assertIn("BASE_URL: ${{ inputs.base_url", self.content)
        self.assertIn('--base-url "$BASE_URL"', self.content)
        self.assertNotIn('--base-url "${{ inputs.base_url', self.content)


if __name__ == "__main__":
    unittest.main()
