from __future__ import annotations

import json
import os
import re
import subprocess
import sys
import tempfile
import textwrap
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
        self.assertIn('print(f"{name}\\t{assets[name]}")', content)
        asset_endpoint = '"repos/${GITHUB_REPOSITORY}/releases/assets/$asset_id"'
        self.assertEqual(content.count(asset_endpoint), 3)
        self.assertIn(f'{asset_endpoint} > "tmp/release-assets/$name"', content)
        self.assertNotIn("releases/$RELEASE_ID/assets/$asset_id", content)
        self.assertNotIn("releases/$release_id/assets/$asset_id", content)
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
        self.assertIn(
            'retry_gh_api_to_file "tmp/staged-assets/$name" "Draft Release asset $name"',
            content,
        )
        self.assertLess(content.index("test -n \"${{ needs.pypi-publish-and-verify.outputs.wheel_sha }}\""), content.index("-F draft=false"))
        self.assertLess(content.index("-F draft=false"), content.rindex("published tag ref does not resolve to input"))

    def test_new_draft_visibility_uses_bounded_retry(self) -> None:
        content = self._workflow("release.yml")
        creation = content.split('gh release create "$TAG" --draft', 1)[1].split('release_id="${release_record', 1)[0]
        self.assertIn("for attempt in 1 2 3 4 5; do", creation)
        self.assertIn("if gh api --paginate --slurp", creation)
        self.assertIn("rm -f tmp/releases-after-create.json tmp/release-id-state", creation)
        self.assertIn("if [ -s tmp/release-id-state ]; then break; fi", creation)
        self.assertIn('if [ "$attempt" -eq 5 ]; then', creation)
        self.assertIn("created Draft Release did not become visible after bounded retries", creation)
        self.assertIn("sleep 2", creation)

    def test_fresh_release_api_reads_recover_from_transient_404_and_stay_bounded(self) -> None:
        content = self._workflow("release.yml")
        marker = "          retry_gh_api_to_file() {\n"
        helper = marker + content.split(marker, 1)[1].split(
            "          archive_path=", 1
        )[0]
        script = "set -euo pipefail\n" + textwrap.dedent(helper)
        self.assertIn(
            'retry_gh_api_to_file tmp/draft.json "Draft Release details"', content
        )
        self.assertIn(
            'retry_gh_api_to_file "tmp/staged-assets/$name" "Draft Release asset $name"',
            content,
        )
        with tempfile.TemporaryDirectory() as working:
            root = Path(working)
            fake_bin = root / "bin"
            fake_bin.mkdir()
            (root / "tmp").mkdir()
            fake_gh = fake_bin / "gh"
            fake_gh.write_text(
                "#!/bin/sh\n"
                "count=0\n"
                "if [ -f \"$GH_COUNT_FILE\" ]; then count=$(cat \"$GH_COUNT_FILE\"); fi\n"
                "count=$((count + 1))\n"
                "printf '%s\\n' \"$count\" > \"$GH_COUNT_FILE\"\n"
                "if [ \"$GH_SUCCEED_AFTER\" -le 0 ] || [ \"$count\" -lt \"$GH_SUCCEED_AFTER\" ]; then\n"
                "  echo 'gh: Not Found (HTTP 404)' >&2\n"
                "  exit 1\n"
                "fi\n"
                "printf '{\"id\":7,\"target_commitish\":\"commit\"}\\n'\n",
                encoding="utf-8",
            )
            fake_gh.chmod(0o755)
            fake_sleep = fake_bin / "sleep"
            fake_sleep.write_text("#!/bin/sh\nexit 0\n", encoding="utf-8")
            fake_sleep.chmod(0o755)
            env = os.environ.copy()
            env.update(
                {
                    "PATH": f"{fake_bin}{os.pathsep}{env['PATH']}",
                    "GITHUB_REPOSITORY": "owner/repository",
                    "GH_COUNT_FILE": str(root / "gh-count"),
                    "GH_SUCCEED_AFTER": "3",
                }
            )
            command = script + (
                '\nretry_gh_api_to_file tmp/result.json "test object" '
                '"repos/owner/repository/releases/7"\n'
            )
            subprocess.run(["bash", "-c", command], cwd=root, env=env, check=True)
            self.assertEqual((root / "gh-count").read_text(encoding="utf-8").strip(), "3")
            self.assertEqual(
                json.loads((root / "tmp/result.json").read_text(encoding="utf-8")),
                {"id": 7, "target_commitish": "commit"},
            )

            (root / "gh-count").unlink()
            (root / "tmp/result.json").unlink()
            env["GH_SUCCEED_AFTER"] = "0"
            failed = subprocess.run(
                ["bash", "-c", command], cwd=root, env=env, text=True, capture_output=True
            )
            self.assertNotEqual(failed.returncode, 0)
            self.assertEqual((root / "gh-count").read_text(encoding="utf-8").strip(), "5")
            self.assertIn("test object did not become readable after bounded retries", failed.stderr)
            self.assertFalse((root / "tmp/result.json").exists())

    def test_release_asset_download_commands_execute_via_stdout(self) -> None:
        content = self._workflow("release.yml")
        self.assertNotRegex(content, r"gh api[^\n]*--output")
        self.assertNotIn("'--output'", content)
        commands = [
            line.strip()
            for line in content.splitlines()
            if line.strip().startswith("gh api -H 'Accept: application/octet-stream'")
            and "/assets/" in line
        ]
        self.assertEqual(len(commands), 2)
        with tempfile.TemporaryDirectory() as working:
            root = Path(working)
            fake_bin = root / "bin"
            fake_bin.mkdir()
            fake_gh = fake_bin / "gh"
            fake_gh.write_text(
                "#!/bin/sh\n"
                "case \" $* \" in *\" --output \"*) exit 97 ;; esac\n"
                "printf 'release-asset-bytes'\n",
                encoding="utf-8",
            )
            fake_gh.chmod(0o755)
            for directory in ("tmp/release-assets", "tmp/final-release-assets"):
                (root / directory).mkdir(parents=True)
            env = os.environ.copy()
            env.update(
                {
                    "PATH": f"{fake_bin}{os.pathsep}{env['PATH']}",
                    "GITHUB_REPOSITORY": "owner/repository",
                    "RELEASE_ID": "7",
                    "release_id": "7",
                    "asset_id": "41",
                    "name": "asset.bin",
                }
            )
            for command in commands:
                command = command.replace("/tmp/final-release-assets/", "tmp/final-release-assets/")
                subprocess.run(["bash", "-c", command], cwd=root, env=env, check=True)
            for path in (
                root / "tmp/release-assets/asset.bin",
                root / "tmp/final-release-assets/asset.bin",
            ):
                self.assertEqual(path.read_bytes(), b"release-asset-bytes")

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

    def test_workflows_install_jq_before_using_release_asset_queries(self) -> None:
        release = self._workflow("release.yml")
        ci = self._workflow("ci.yml")
        install = "sudo apt-get update -qq && sudo apt-get install -y jq"
        self.assertIn(install, release)
        self.assertIn(install, ci)
        build, promotion = release.split("  promotion-complete-and-publish-release:", 1)
        self.assertIn(install, build)
        self.assertLess(build.index(install), build.index("jq -c"))
        self.assertIn(install, promotion)
        self.assertLess(promotion.index(install), promotion.index("jq -r"))

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

    def test_private_draft_consumers_have_required_contents_permission(self) -> None:
        content = self._workflow("release.yml")
        jobs = (
            ("pypi-validate", "pypi-publish-and-verify"),
            ("pypi-publish-and-verify", "ghcr-publish-and-verify"),
            ("ghcr-publish-and-verify", "promotion-complete-and-publish-release"),
        )
        for job_name, next_job in jobs:
            job = content.split(f"  {job_name}:\n", 1)[1].split(f"  {next_job}:\n", 1)[0]
            self.assertIn("    permissions:\n      contents: write\n", job)
            self.assertNotIn("      contents: read\n", job)
        pypi_publish = content.split("  pypi-publish-and-verify:\n", 1)[1].split(
            "  ghcr-publish-and-verify:\n", 1
        )[0]
        self.assertIn("      id-token: write\n", pypi_publish)

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
