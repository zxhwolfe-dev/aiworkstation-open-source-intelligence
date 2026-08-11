from __future__ import annotations

import unittest
from pathlib import Path


class PublicationWorkflowTests(unittest.TestCase):
    ROOT = Path(__file__).resolve().parents[1]

    def _workflow(self, name: str) -> str:
        return (self.ROOT / ".github" / "workflows" / name).read_text(encoding="utf-8")

    def test_release_contains_gated_pypi_chain_with_oidc(self) -> None:
        content = self._workflow("release.yml")
        self.assertIn("build-and-stage-draft:", content)
        self.assertIn("pypi-validate:", content)
        self.assertIn("pypi-publish-and-verify:", content)
        self.assertIn("needs: build-and-stage-draft", content)
        self.assertIn("PYTHON-DISTS-SHA256SUMS", content)
        self.assertIn("gh release download", content)
        self.assertIn("sha256sum --check", content)
        self.assertIn("id-token: write", content)
        self.assertIn("environment: pypi", content)
        self.assertIn("pypa/gh-action-pypi-publish", content)
        self.assertNotIn("PYPI_API_TOKEN", content)
        self.assertNotIn("skip-existing", content)
        self.assertNotIn("types: [published]", content)
        self.assertIn("urllib.request.urlopen(f'https://pypi.org/pypi/aiworkstation-open-source-intelligence/{version}/json", content)
        self.assertIn("PyPI hash mismatch", content)
        self.assertIn("PyPI verification did not converge", content)

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
        self.assertIn("gh release create \"$TAG\" --draft", content)
        self.assertIn("gh release edit \"$TAG\" \"${prerelease_args[@]}\"", content)
        self.assertIn("Create or safely resume matching Draft Release", content)
        self.assertIn("a published Release already exists", content)
        self.assertIn("Draft tag points to a different commit", content)
        self.assertIn("Draft asset differs from deterministic build", content)
        self.assertIn("sha256sum --check SHA256SUMS", content)
        self.assertIn("sha256sum --check PYTHON-DISTS-SHA256SUMS", content)
        self.assertIn("tag exists without matching Draft Release", content)
        self.assertNotIn("--clobber", content)

    def test_release_contains_gated_ghcr_commit_promotion(self) -> None:
        content = self._workflow("release.yml")
        self.assertIn("ghcr-publish-and-verify:", content)
        self.assertIn("sha-${{ inputs.commit }}", content)
        self.assertIn('OSI_IMAGE_COMMIT=$COMMIT', content)
        self.assertIn('org.opencontainers.image.revision=$COMMIT', content)
        self.assertIn("packages: write", content)
        self.assertIn("docker buildx build --push", content)
        self.assertIn("docker image inspect", content)
        self.assertIn("RepoDigests", content)
        self.assertIn("ghcr.io/${{ github.repository }}", content)

    def test_promotion_graph_has_no_release_event_fanout(self) -> None:
        content = self._workflow("release.yml")
        self.assertIn("promotion-complete-and-publish-release:", content)
        self.assertIn("needs: [build-and-stage-draft, pypi-publish-and-verify, ghcr-publish-and-verify]", content)
        self.assertNotIn("types: [published]", content)

    def test_release_uses_explicit_tools_and_exact_artifact_paths(self) -> None:
        content = self._workflow("release.yml")
        self.assertIn("python -m pip install build twine ruff -e", content)
        self.assertIn("mapfile -t wheels", content)
        self.assertIn('test "${#wheels[@]}" -eq 1', content)
        self.assertIn('test "${wheels[0]}" = "$WHEEL_NAME"', content)
        self.assertNotIn('wheels=(dist/python/*.whl)', content)

    def test_old_release_workflows_are_removed(self) -> None:
        self.assertFalse((self.ROOT / ".github/workflows/publish-pypi.yml").exists())
        self.assertFalse((self.ROOT / ".github/workflows/publish-ghcr.yml").exists())

    def test_publishing_documentation_covers_assets_and_recovery(self) -> None:
        content = (self.ROOT / "docs/GITHUB-PUBLISHING.md").read_text(encoding="utf-8")
        for value in (
            "deterministic Skills ZIP",
            "SHA256SUMS",
            "bundle-report.json",
            "Python wheel",
            "Python sdist",
            "PYTHON-DISTS-SHA256SUMS",
            "Draft Release",
            "filename and SHA256",
            "required reviewer",
        ):
            self.assertIn(value, content)


if __name__ == "__main__":
    unittest.main()
