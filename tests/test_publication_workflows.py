from __future__ import annotations

import json
import os
import re
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from aiworkstation_osi.release_promotion import validate_asset_ids


class PublicationWorkflowTests(unittest.TestCase):
    ROOT = Path(__file__).resolve().parents[1]

    def _workflow(self, name: str) -> str:
        return (self.ROOT / ".github" / "workflows" / name).read_text(encoding="utf-8")

    def _assert_src_helper_block(self, block: str, helper: str) -> None:
        command = "PYTHONPATH=src python - <<'PY'"
        if command not in block:
            raise AssertionError("src-layout inline Python command lacks PYTHONPATH=src")
        if f"from aiworkstation_osi.release_promotion import {helper}" not in block:
            raise AssertionError(f"inline Python block does not import {helper}")

    def test_release_contains_gated_pypi_chain_with_oidc(self) -> None:
        content = self._workflow("release.yml")
        self.assertIn("build-and-stage-draft:", content)
        self.assertIn("pypi-validate:", content)
        self.assertIn("pypi-publish-and-verify:", content)
        self.assertIn("needs: build-and-stage-draft", content)
        self.assertIn("PYTHON-DISTS-SHA256SUMS", content)
        self.assertIn("os.environ['GITHUB_REPOSITORY']}/releases/{sys.argv[1]}/assets/{assets[name]}", content)
        self.assertIn("sha256sum --check", content)
        self.assertIn("id-token: write", content)
        self.assertIn("environment: pypi", content)
        self.assertIn("pypa/gh-action-pypi-publish", content)
        self.assertNotIn("PYPI_API_TOKEN", content)
        self.assertNotIn("skip-existing", content)
        self.assertNotIn("types: [published]", content)
        self.assertIn("urllib.request.urlopen(f'https://pypi.org/pypi/aiworkstation-open-source-intelligence/{version}/json", content)
        self.assertIn("PyPI hash mismatch", content)
        self.assertIn("decide_pypi_promotion", content)
        self.assertIn("Revalidate Release state after environment approval", content)
        self.assertIn("Revalidate Draft immediately before any PyPI write", content)
        self.assertIn("steps.before-upload.outputs.allow_upload == 'true'", content)
        self.assertIn("public Release is missing PyPI files", content)
        self.assertIn("PyPI verification did not converge", content)
        self.assertIn("asset_ids", content)
        self.assertIn("verify_checksum_manifest", content)

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
        self.assertIn("gh api -X PATCH \"repos/${GITHUB_REPOSITORY}/releases/$RELEASE_ID\"", content)
        self.assertIn("-F draft=false", content)
        self.assertIn('-F prerelease="$PRERELEASE"', content)
        self.assertNotIn("-f draft=false", content)
        self.assertIn("Create or safely resume matching Draft Release", content)
        self.assertIn("a published Release already exists", content)
        self.assertIn("tag ref exists before Draft promotion", content)
        self.assertIn("Draft Skills archive differs from deterministic build", content)
        self.assertIn("validate_bundle_report", content)
        self.assertIn("sha256sum --check SHA256SUMS", content)
        self.assertIn("sha256sum --check PYTHON-DISTS-SHA256SUMS", content)
        self.assertIn("tag exists without matching Draft Release", content)
        self.assertNotIn("--clobber", content)
        self.assertNotIn('commits/$TAG', content)
        self.assertIn("target_commitish", content)
        self.assertIn("release_id", content)
        self.assertIn("GITHUB_REF", content)
        self.assertIn("GITHUB_SHA", content)
        self.assertEqual(content.count("git fetch origin main --no-tags --depth=1"), 1)
        first_create = content.index('if [ -z "$release_record" ]; then')
        moving_main_check = content.index("git fetch origin main --no-tags --depth=1")
        create_draft = content.index('gh release create "$TAG" --draft')
        self.assertLess(first_create, moving_main_check)
        self.assertLess(moving_main_check, create_draft)
        self.assertIn("overwrite: true", content)
        self.assertIn("is True", content)
        self.assertIn("is False", content)
        self.assertIn("verify_checksum_manifest", content)
        self.assertIn("validate_sdist_metadata", content)
        self.assertLess(content.index("verify_checksum_manifest((root/'SHA256SUMS')"), content.index("pypi-validate:"))
        self.assertIn("locate_draft", content)
        self.assertIn('test "$COMMIT" = "$(git rev-parse FETCH_HEAD)"', content)
        self.assertIn('gh api -H \'Accept: application/octet-stream\' --output "tmp/staged-assets/$name"', content)
        self.assertLess(content.index("test -n \"${{ needs.pypi-publish-and-verify.outputs.wheel_sha }}\""), content.index("-F draft=false"))
        self.assertLess(content.index("-F draft=false"), content.rindex("published tag ref does not resolve to input"))

    def test_release_asset_id_jq_builds_integer_name_map(self) -> None:
        content = self._workflow("release.yml")
        match = re.search(r"asset_ids=\"\$\(jq -c '([^']+)' tmp/draft\.json\)\"", content)
        self.assertIsNotNone(match, "release workflow asset_ids jq expression was not found")
        payload = {
            "assets": [
                {"name": "wheel.whl", "id": 41},
                {"name": "source.tar.gz", "id": 42},
            ]
        }
        result = subprocess.run(
            ["jq", "-c", match.group(1)],
            input=json.dumps(payload),
            text=True,
            capture_output=True,
            check=True,
        )
        asset_ids = json.loads(result.stdout)
        self.assertEqual(asset_ids, {"wheel.whl": 41, "source.tar.gz": 42})
        self.assertTrue(all(type(asset_id) is int for asset_id in asset_ids.values()))
        self.assertEqual(
            validate_asset_ids(
                payload,
                expected_assets=["wheel.whl", "source.tar.gz"],
                expected_asset_ids=asset_ids,
            ),
            asset_ids,
        )

    def test_release_contains_gated_ghcr_commit_promotion(self) -> None:
        content = self._workflow("release.yml")
        self.assertIn("ghcr-publish-and-verify:", content)
        self.assertIn("IMAGE: ghcr.io/${{ github.repository }}:sha-${{ inputs.commit }}", content)
        self.assertNotIn("IMAGE: ghcr.io/${{ github.repository }}/sha-${{ inputs.commit }}", content)
        self.assertNotIn("--tag latest", content)
        self.assertIn('OSI_IMAGE_COMMIT=$COMMIT', content)
        self.assertIn('org.opencontainers.image.revision=$COMMIT', content)
        self.assertIn("packages: write", content)
        self.assertIn("docker buildx build --load", content)
        self.assertIn("docker push \"$IMAGE\"", content)
        self.assertNotIn("docker buildx build --push", content)
        self.assertIn("docker image inspect", content)
        self.assertIn("decide_ghcr_promotion", content)
        self.assertIn("A public Release missing its image is a hard failure", content)
        self.assertIn("/tmp/release-before-image-write.json", content)
        self.assertIn("RepoDigests", content)
        self.assertIn("repository=os.environ['IMAGE'].rsplit(':',1)[0]", content)
        self.assertIn("validate_repo_digest", content)
        inspect_block = content.split("      - name: Inspect pushed image identity and digest\n", 1)[1].split("  promotion-complete-and-publish-release:\n", 1)[0]
        self._assert_src_helper_block(inspect_block, "validate_image_identity")
        self.assertNotIn("python - <<'PY'", inspect_block.replace("PYTHONPATH=src python - <<'PY'", ""))
        self.assertIn("merge_release_states", content)
        self.assertIn("release-after-image-build.json", content)
        self.assertIn("docker push \"$IMAGE\"", content)
        self.assertNotIn("docker buildx build --push", content)
        self.assertIn("validate_repo_digest", content)
        self.assertIn("packages: read", content)
        self.assertNotIn('commits/$TAG', content)
        self.assertIn("ghcr.io/${{ github.repository }}", content)
        self.assertIn("release_id", content)
        self.assertIn("target_commitish", content)
        self.assertIn("validate_asset_ids", content)
        self.assertIn("final-release-latest.json", content)
        self.assertNotIn("cp /tmp/final-release-before.json /tmp/final-release-after.json", content)
        self.assertIn("INITIAL_ASSET_IDS", content)
        prebuild = content.index("/tmp/prebuild-release-state")
        build = content.index("docker buildx build --load")
        self.assertLess(prebuild, build)
        self.assertIn("merge_release_states([os.environ['INITIAL_STATE'], os.environ['JOB_START_STATE'], os.environ['PRIOR_STATE'], current])", content)

    def test_pypi_publish_checkout_has_minimal_read_permission(self) -> None:
        content = self._workflow("release.yml")
        pypi_job = content.split("  pypi-publish-and-verify:\n", 1)[1].split("  ghcr-publish-and-verify:\n", 1)[0]
        self.assertIn("    permissions:\n      contents: read\n      id-token: write\n", pypi_job)

    def test_promotion_graph_has_no_release_event_fanout(self) -> None:
        content = self._workflow("release.yml")
        self.assertIn("promotion-complete-and-publish-release:", content)
        self.assertIn("needs: [build-and-stage-draft, pypi-publish-and-verify, ghcr-publish-and-verify]", content)
        self.assertNotIn("types: [published]", content)
        self.assertIn("promotion_decision", content)
        self.assertIn("published tag ref does not resolve to input commit", content)

    def test_final_promotion_imports_src_layout_helpers_explicitly(self) -> None:
        content = self._workflow("release.yml")
        final = content.split("  promotion-complete-and-publish-release:\n", 1)[1]
        self._assert_src_helper_block(final, "validate_image_identity")
        with self.assertRaises(AssertionError):
            self._assert_src_helper_block(final.replace("PYTHONPATH=src python - <<'PY'", "python - <<'PY'"), "validate_image_identity")
        with self.assertRaises(AssertionError):
            self._assert_src_helper_block(final.replace("from aiworkstation_osi.release_promotion import validate_image_identity", ""), "validate_image_identity")

    def test_release_helper_imports_in_clean_src_layout(self) -> None:
        with tempfile.TemporaryDirectory() as working:
            env = {key: value for key, value in os.environ.items() if key not in {"PYTHONHOME", "PYTHONPATH"}}
            command = [sys.executable, "-S", "-c", "from aiworkstation_osi.release_promotion import validate_image_identity"]
            missing = subprocess.run(command, cwd=working, env=env, check=False, capture_output=True)
            self.assertNotEqual(missing.returncode, 0)
            env["PYTHONPATH"] = str(self.ROOT / "src")
            imported = subprocess.run(command, cwd=working, env=env, check=False, capture_output=True)
            self.assertEqual(imported.returncode, 0, imported.stderr.decode())

    def test_uninstalled_release_jobs_bind_every_source_import(self) -> None:
        content = self._workflow("release.yml")
        job_names = (
            "pypi-validate",
            "pypi-publish-and-verify",
            "ghcr-publish-and-verify",
            "promotion-complete-and-publish-release",
        )
        for index, job_name in enumerate(job_names):
            start = content.index(f"  {job_name}:\n")
            end = content.index(f"  {job_names[index + 1]}:\n") if index + 1 < len(job_names) else len(content)
            lines = content[start:end].splitlines()
            for line_number, line in enumerate(lines):
                if "from aiworkstation_osi" not in line and "import aiworkstation_osi" not in line:
                    continue
                command = next((candidate for candidate in reversed(lines[:line_number]) if "<<'PY'" in candidate), "")
                installed_wheel_import = "env -u PYTHONPATH -u PYTHONHOME" in command
                self.assertTrue(
                    "PYTHONPATH=src" in command or installed_wheel_import,
                    f"{job_name} source import is not isolated: {line.strip()}",
                )

    def test_release_uses_explicit_tools_and_exact_artifact_paths(self) -> None:
        content = self._workflow("release.yml")
        self.assertIn("python -m pip install build twine ruff -e", content)
        self.assertIn("mapfile -t wheels", content)
        self.assertIn('test "${#wheels[@]}" -eq 1', content)
        self.assertIn('test "${wheels[0]}" = "$WHEEL_NAME"', content)
        self.assertNotIn('wheels=(dist/python/*.whl)', content)
        self.assertIn('find dist/python -maxdepth 1 -type f -name', content)
        self.assertNotIn('cmp -s "$local_path"', content)
        self.assertIn('python - "${expected[@]}"', content)
        self.assertIn('sha256sum "/tmp/final-release-assets/$WHEEL_NAME"', content)

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
            "refs/tags/<tag>",
        ):
            self.assertIn(value, content)


if __name__ == "__main__":
    unittest.main()
