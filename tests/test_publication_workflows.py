from __future__ import annotations

import unittest
from pathlib import Path


class PublicationWorkflowTests(unittest.TestCase):
    ROOT = Path(__file__).resolve().parents[1]

    def _workflow(self, name: str) -> str:
        return (self.ROOT / ".github" / "workflows" / name).read_text(encoding="utf-8")

    def test_pypi_requires_manual_confirmation_and_oidc(self) -> None:
        content = self._workflow("publish-pypi.yml")
        self.assertIn("workflow_dispatch:", content)
        self.assertNotIn("push:\n    branches: [main]", content)
        self.assertIn('test "$CONFIRM" = "PUBLISH"', content)
        self.assertIn("id-token: write", content)
        self.assertIn("environment: pypi", content)
        self.assertIn("pypa/gh-action-pypi-publish", content)
        self.assertNotIn("PYPI_API_TOKEN", content)

    def test_github_release_is_manual_and_version_bound(self) -> None:
        content = self._workflow("release.yml")
        self.assertIn("workflow_dispatch:", content)
        self.assertNotIn("push:\n    branches: [main]", content)
        self.assertIn("contents: write", content)
        self.assertIn("tag must look like v0.1.0", content)
        self.assertIn("does not match plugin version", content)
        self.assertIn("osi-build-alpha", content)
        self.assertIn("gh release create", content)

    def test_ghcr_publishes_only_from_tag_or_manual_dispatch(self) -> None:
        content = self._workflow("publish-ghcr.yml")
        self.assertIn("workflow_dispatch:", content)
        self.assertIn('tags:\n      - "v*"', content)
        self.assertNotIn("branches: [main]", content)
        self.assertIn("packages: write", content)
        self.assertIn("docker/build-push-action", content)
        self.assertIn("ghcr.io/${{ github.repository }}", content)


if __name__ == "__main__":
    unittest.main()
