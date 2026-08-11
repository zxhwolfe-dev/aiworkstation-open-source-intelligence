from __future__ import annotations

import unittest
from pathlib import Path


class AlphaPackageWorkflowTests(unittest.TestCase):
    ROOT = Path(__file__).resolve().parents[1]

    @classmethod
    def setUpClass(cls) -> None:
        cls.content = (
            cls.ROOT / ".github" / "workflows" / "alpha-package.yml"
        ).read_text(encoding="utf-8")

    def test_workflow_is_manual_and_read_only(self) -> None:
        self.assertIn("workflow_dispatch:", self.content)
        self.assertNotIn("schedule:", self.content)
        self.assertNotIn("pull_request:", self.content)
        self.assertIn("permissions:\n  contents: read", self.content)
        self.assertNotIn("contents: write", self.content)

    def test_package_runs_validation_before_upload(self) -> None:
        tests = self.content.index("Run release gates")
        build = self.content.index("Build deterministic complete Plugin bundle")
        inspect = self.content.index("Inspect package surface")
        upload = self.content.index("Upload reviewed alpha package")
        self.assertLess(tests, build)
        self.assertLess(build, inspect)
        self.assertLess(inspect, upload)
        self.assertNotIn("if: always()", self.content)

    def test_package_explicitly_bundles_the_hosted_mcp_configuration(self) -> None:
        self.assertIn("osi-build-alpha", self.content)
        self.assertIn("distribution_mode", self.content)
        self.assertIn("skill-plus-hosted-mcp", self.content)
        self.assertIn("hosted_mcp_config_bundled", self.content)
        self.assertIn("live_mcp_bundled", self.content)
        self.assertIn('".mcp.json"', self.content)
        self.assertIn("name.startswith(\"src/\")", self.content)
        self.assertIn("name == \"pyproject.toml\"", self.content)

    def test_checksum_and_required_skill_checks_are_present(self) -> None:
        self.assertIn("sha256sum --check SHA256SUMS", self.content)
        for path in (
            "product-skills/ai-open-source-intelligence/SKILL.md",
            "docs/alpha-tester-guide.md",
            "SECURITY.md",
            "PRIVACY.md",
        ):
            with self.subTest(path=path):
                self.assertIn(path, self.content)


if __name__ == "__main__":
    unittest.main()
