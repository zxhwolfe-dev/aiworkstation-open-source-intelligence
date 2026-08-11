from __future__ import annotations

import unittest
from pathlib import Path


class PublicationWorkflowTests(unittest.TestCase):
    ROOT = Path(__file__).resolve().parents[1]

    def _workflow(self, name: str) -> str:
        return (self.ROOT / ".github" / "workflows" / name).read_text(encoding="utf-8")

    def test_pypi_promotes_successful_release_artifact_with_oidc(self) -> None:
        content = self._workflow("publish-pypi.yml")
        self.assertIn("release:", content)
        self.assertIn("types: [published]", content)
        self.assertIn("PYTHON-DISTS-SHA256SUMS", content)
        self.assertIn("gh release download", content)
        self.assertIn("sha256sum --check", content)
        self.assertIn("id-token: write", content)
        self.assertIn("environment: pypi", content)
        self.assertIn("pypa/gh-action-pypi-publish", content)
        self.assertNotIn("PYPI_API_TOKEN", content)

    def test_github_release_is_manual_and_version_bound(self) -> None:
        content = self._workflow("release.yml")
        self.assertIn("workflow_dispatch:", content)
        self.assertNotIn("push:\n    branches: [main]", content)
        self.assertIn("contents: write", content)
        self.assertIn("tag must look like v0.3.0", content)
        self.assertIn("Full commit SHA to release", content)
        self.assertIn("commit must be a full 40-character SHA", content)
        self.assertIn("ref: ${{ inputs.commit }}", content)
        self.assertIn("does not match plugin version", content)
        self.assertIn("osi-build-alpha", content)
        self.assertIn("gh release create", content)

    def test_ghcr_promotes_the_successful_release_sha(self) -> None:
        content = self._workflow("publish-ghcr.yml")
        self.assertIn("release:", content)
        self.assertIn("types: [published]", content)
        self.assertIn("Resolve release commit", content)
        self.assertIn("sha-${{ steps.identity.outputs.commit }}", content)
        self.assertIn("OSI_IMAGE_COMMIT=${{ steps.identity.outputs.commit }}", content)
        self.assertIn("packages: write", content)
        self.assertIn("docker/build-push-action", content)
        self.assertIn("ghcr.io/${{ github.repository }}", content)


if __name__ == "__main__":
    unittest.main()
