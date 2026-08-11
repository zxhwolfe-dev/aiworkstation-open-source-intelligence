from __future__ import annotations

import unittest

from aiworkstation_osi.release_promotion import (
    ReleasePromotionError,
    decide_ghcr_promotion,
    decide_pypi_promotion,
    flatten_releases,
    locate_draft,
    locate_release,
    merge_release_states,
    parse_checksum_manifest,
    promotion_decision,
    validate_asset_ids,
    validate_bundle_report,
    validate_image_identity,
    validate_preflight_release,
    validate_release,
    validate_repo_digest,
    validate_sdist_metadata,
    validate_wheel_metadata,
    verify_checksum_manifest,
)

COMMIT = "a" * 40
ASSETS = ["skills.zip", "SHA256SUMS", "bundle-report.json", "wheel.whl", "source.tar.gz", "PYTHON-DISTS-SHA256SUMS"]


def release(*, draft: bool, commit: str = COMMIT, release_id: int = 7, prerelease: bool = True) -> dict:
    return {
        "id": release_id,
        "tag_name": "v0.3.0",
        "target_commitish": commit,
        "draft": draft,
        "prerelease": prerelease,
        "assets": [{"id": index + 1, "name": name} for index, name in enumerate(ASSETS)],
    }


class ReleasePromotionTests(unittest.TestCase):
    def test_public_release_state_is_sticky_and_regressions_fail_closed(self) -> None:
        self.assertEqual(merge_release_states(["draft", "draft"]), "draft")
        self.assertEqual(merge_release_states(["draft", "public"]), "public")
        self.assertEqual(merge_release_states(["public", "public"]), "public")
        for sequence in (("draft", "public", "draft"), ("public", "draft")):
            with self.assertRaises(ReleasePromotionError):
                merge_release_states(sequence)

    def test_repo_digest_requires_exact_repository_and_lowercase_sha256(self) -> None:
        repository = "ghcr.io/example/repo"
        valid = f"{repository}@sha256:{'a' * 64}"
        self.assertEqual(validate_repo_digest(valid, repository), valid)
        for value in (
            "",
            f"{repository}@sha256:{'a' * 63}",
            f"{repository}@sha256:{'g' * 64}",
            f"ghcr.io/other/repo@sha256:{'a' * 64}",
            f"{repository}@sha256:{'A' * 64}",
            f"{repository}@sha256:{'a' * 64}:extra",
        ):
            with self.assertRaises(ReleasePromotionError):
                validate_repo_digest(value, repository)

    def test_image_identity_requires_exact_metadata_and_digest(self) -> None:
        repository = "ghcr.io/example/repo"
        digest = f"{repository}@sha256:{'a' * 64}"
        payload = [{"Config": {"Labels": {"org.opencontainers.image.revision": COMMIT}, "Env": [f"OSI_IMAGE_COMMIT={COMMIT}"]}, "RepoDigests": [digest]}]
        self.assertEqual(validate_image_identity(payload, commit=COMMIT, repository=repository, expected_digest=digest), digest)
        for bad in (
            "",
            f"{repository}@sha256:{'a' * 63}",
            f"{repository}@sha256:{'g' * 64}",
            f"ghcr.io/other/repo@sha256:{'a' * 64}",
        ):
            with self.assertRaises(ReleasePromotionError):
                validate_image_identity([{**payload[0], "RepoDigests": [bad]}], commit=COMMIT, repository=repository)
        with self.assertRaises(ReleasePromotionError):
            validate_image_identity(payload, commit="b" * 40, repository=repository)
        with self.assertRaises(ReleasePromotionError):
            validate_image_identity(payload, commit=COMMIT, repository=repository, expected_digest=f"{repository}@sha256:{'b' * 64}")
        wrong_env = [{"Config": {"Labels": {"org.opencontainers.image.revision": COMMIT}, "Env": [f"OSI_IMAGE_COMMIT={'b' * 40}"]}, "RepoDigests": [digest]}]
        with self.assertRaises(ReleasePromotionError):
            validate_image_identity(wrong_env, commit=COMMIT, repository=repository)
        duplicate_env = [{"Config": {"Labels": {"org.opencontainers.image.revision": COMMIT}, "Env": [f"OSI_IMAGE_COMMIT={COMMIT}", f"OSI_IMAGE_COMMIT={COMMIT}"]}, "RepoDigests": [digest]}]
        with self.assertRaises(ReleasePromotionError):
            validate_image_identity(duplicate_env, commit=COMMIT, repository=repository)

    def test_release_asset_ids_are_stable(self) -> None:
        payload = release(draft=True)
        expected = {name: index + 1 for index, name in enumerate(ASSETS)}
        self.assertEqual(validate_asset_ids(payload, expected_assets=ASSETS, expected_asset_ids=expected), expected)
        replaced = release(draft=True)
        replaced["assets"][0]["id"] = 99
        with self.assertRaises(ReleasePromotionError):
            validate_asset_ids(replaced, expected_assets=ASSETS, expected_asset_ids=expected)
        removed = release(draft=True)
        removed["assets"] = removed["assets"][:-1]
        with self.assertRaises(ReleasePromotionError):
            validate_asset_ids(removed, expected_assets=ASSETS, expected_asset_ids=expected)
        extra = release(draft=True)
        extra["assets"].append({"id": 99, "name": "extra"})
        with self.assertRaises(ReleasePromotionError):
            validate_asset_ids(extra, expected_assets=ASSETS, expected_asset_ids=expected)
        duplicate = release(draft=True)
        duplicate["assets"].append({"id": 99, "name": ASSETS[0]})
        with self.assertRaises(ReleasePromotionError):
            validate_asset_ids(duplicate, expected_assets=ASSETS, expected_asset_ids=expected)

    def test_downstream_promotion_state_machine_is_fail_closed_for_public_releases(self) -> None:
        expected = {"wheel.whl": "a" * 64, "source.tar.gz": "b" * 64}
        self.assertEqual(decide_pypi_promotion("draft", expected_hashes=expected, actual_hashes={"wheel.whl": expected["wheel.whl"]}), "upload_missing")
        self.assertEqual(decide_pypi_promotion("public", expected_hashes=expected, actual_hashes=expected), "verify_only")
        for actual in (
            {"wheel.whl": expected["wheel.whl"]},
            {"source.tar.gz": expected["source.tar.gz"]},
            {**expected, "extra.whl": "c" * 64},
            {"wheel.whl": "c" * 64, "source.tar.gz": expected["source.tar.gz"]},
        ):
            with self.assertRaises(ReleasePromotionError):
                decide_pypi_promotion("public", expected_hashes=expected, actual_hashes=actual)
        self.assertEqual(decide_ghcr_promotion("draft", image_exists=False, commit=COMMIT), "build_push")
        self.assertEqual(decide_ghcr_promotion("public", image_exists=True, commit=COMMIT, revision=COMMIT, image_commit=COMMIT, repo_digest="ghcr.io/example/repo@sha256:" + "d" * 64, repository="ghcr.io/example/repo"), "verify_only")
        with self.assertRaises(ReleasePromotionError):
            decide_ghcr_promotion("public", image_exists=False, commit=COMMIT)
        with self.assertRaises(ReleasePromotionError):
            decide_ghcr_promotion("public", image_exists=True, commit=COMMIT, revision="b" * 40, image_commit=COMMIT, repo_digest="ghcr.io/example/repo@sha256:" + "d" * 64, repository="ghcr.io/example/repo")

    def test_checksum_manifest_requires_exact_safe_set_and_hashes(self) -> None:
        data = b"skills"
        digest = __import__("hashlib").sha256(data).hexdigest()
        self.assertEqual(parse_checksum_manifest(f"{digest}  skills.zip\n", ["skills.zip"]), {"skills.zip": digest})
        self.assertEqual(verify_checksum_manifest(f"{digest}  skills.zip\n", ["skills.zip"], {"skills.zip": data})["skills.zip"], digest)
        invalid = (
            f"{digest}  skills.zip\n{digest}  extra.zip\n",
            f"{digest}  skills.zip\n{digest}  skills.zip\n",
            f"{'a' * 63}  skills.zip\n",
            f"{digest}  /tmp/skills.zip\n",
            f"{digest}  ../skills.zip\n",
            f"{digest} *skills.zip\n",
            f"{digest}  dir/skills.zip\n",
            f"{digest}  dir\\skills.zip\n",
            f"{digest}  skills..zip\n",
        )
        for content in invalid:
            with self.assertRaises(ReleasePromotionError):
                parse_checksum_manifest(content, ["skills.zip"])
        with self.assertRaises(ReleasePromotionError):
            parse_checksum_manifest(f"{digest}  skills.zip\n", ["skills.zip", "other.zip"])
        with self.assertRaises(ReleasePromotionError):
            verify_checksum_manifest(f"{'0' * 64}  skills.zip\n", ["skills.zip"], {"skills.zip": data})

    def test_package_metadata_helpers_validate_name_and_version(self) -> None:
        import io
        import tarfile
        import zipfile

        wheel = io.BytesIO()
        with zipfile.ZipFile(wheel, "w") as archive:
            archive.writestr("pkg-0.3.0.dist-info/METADATA", "Name: aiworkstation-open-source-intelligence\nVersion: 0.3.0\n")
        validate_wheel_metadata(wheel.getvalue(), "aiworkstation-open-source-intelligence", "0.3.0")
        with self.assertRaises(ReleasePromotionError):
            validate_wheel_metadata(wheel.getvalue(), "wrong-distribution", "0.3.0")
        sdist = io.BytesIO()
        with tarfile.open(fileobj=sdist, mode="w:gz") as archive:
            info = tarfile.TarInfo("pkg-0.3.0/PKG-INFO")
            payload = b"Name: aiworkstation-open-source-intelligence\nVersion: 0.3.0\n"
            info.size = len(payload)
            archive.addfile(info, io.BytesIO(payload))
        validate_sdist_metadata(sdist.getvalue(), "aiworkstation-open-source-intelligence", "0.3.0")
        with self.assertRaises(ReleasePromotionError):
            validate_sdist_metadata(sdist.getvalue(), "aiworkstation-open-source-intelligence", "0.2.0")

    def test_bundle_report_is_validated_without_absolute_path_identity(self) -> None:
        import io
        import json
        import zipfile

        files = {"README.md": b"readme", "config.json": b"{}"}
        embedded = {
            "schema_version": "osi.alpha-bundle.v1",
            "name": "aiworkstation-open-source-intelligence",
            "version": "0.3.0",
            "distribution_mode": "skills-only",
            "live_mcp_bundled": False,
            "files": [
                {"path": name, "size": len(data), "sha256": __import__("hashlib").sha256(data).hexdigest()}
                for name, data in files.items()
            ],
        }
        archive_io = io.BytesIO()
        with zipfile.ZipFile(archive_io, "w") as bundle:
            bundle.writestr("BUNDLE-MANIFEST.json", json.dumps(embedded))
            for name, data in files.items():
                bundle.writestr(name, data)
        archive = archive_io.getvalue()
        report = {
            "ok": True,
            "schema_version": "osi.alpha-bundle.v1",
            "name": "aiworkstation-open-source-intelligence",
            "version": "0.3.0",
            "archive": "/different/runner/dist/skills.zip",
            "archive_sha256": __import__("hashlib").sha256(archive).hexdigest(),
            "checksum_file": "/different/runner/dist/SHA256SUMS",
            "file_count": 2,
            "distribution_mode": "skills-only",
            "live_mcp_bundled": False,
        }
        content = json.dumps(report).encode()
        validate_bundle_report(
            content,
            expected_name="aiworkstation-open-source-intelligence",
            expected_version="0.3.0",
            expected_archive_name="skills.zip",
            archive_bytes=archive,
        )
        report["archive_sha256"] = "0" * 64
        with self.assertRaises(ReleasePromotionError):
            validate_bundle_report(
                json.dumps(report).encode(),
                expected_name="aiworkstation-open-source-intelligence",
                expected_version="0.3.0",
                expected_archive_name="skills.zip",
                archive_bytes=archive,
            )
        for bad_count in (1, True):
            report["archive_sha256"] = __import__("hashlib").sha256(archive).hexdigest()
            report["file_count"] = bad_count
            with self.assertRaises(ReleasePromotionError):
                validate_bundle_report(
                    json.dumps(report).encode(),
                    expected_name="aiworkstation-open-source-intelligence",
                    expected_version="0.3.0",
                    expected_archive_name="skills.zip",
                    archive_bytes=archive,
                )
        embedded["files"][0]["size"] += 1
        tampered_manifest_io = io.BytesIO()
        with zipfile.ZipFile(tampered_manifest_io, "w") as bundle:
            bundle.writestr("BUNDLE-MANIFEST.json", json.dumps(embedded))
            for name, data in files.items():
                bundle.writestr(name, data)
        report["file_count"] = 2
        report["archive_sha256"] = __import__("hashlib").sha256(tampered_manifest_io.getvalue()).hexdigest()
        with self.assertRaises(ReleasePromotionError):
            validate_bundle_report(
                json.dumps(report).encode(),
                expected_name="aiworkstation-open-source-intelligence",
                expected_version="0.3.0",
                expected_archive_name="skills.zip",
                archive_bytes=tampered_manifest_io.getvalue(),
            )

    def test_bundle_report_rejects_manifest_identity_paths_and_digest_errors(self) -> None:
        import hashlib
        import io
        import json
        import zipfile

        def make_archive(entries, *, manifest_overrides=None, duplicate_manifest=False):
            manifest = {
                "schema_version": "osi.alpha-bundle.v1", "name": "aiworkstation-open-source-intelligence", "version": "0.3.0",
                "distribution_mode": "skills-only", "live_mcp_bundled": False, "files": [
                    {"path": name, "size": len(data), "sha256": hashlib.sha256(data).hexdigest()} for name, data in entries.items()
                ],
            }
            if manifest_overrides: manifest.update(manifest_overrides)
            stream = io.BytesIO()
            with zipfile.ZipFile(stream, "w") as archive:
                archive.writestr("BUNDLE-MANIFEST.json", json.dumps(manifest))
                if duplicate_manifest: archive.writestr("BUNDLE-MANIFEST.json", json.dumps(manifest))
                for name, data in entries.items(): archive.writestr(name, data)
            return stream.getvalue()

        def report(archive):
            return json.dumps({"ok": True, "schema_version": "osi.alpha-bundle.v1", "name": "aiworkstation-open-source-intelligence", "version": "0.3.0", "archive": "/runner/skills.zip", "archive_sha256": hashlib.sha256(archive).hexdigest(), "checksum_file": "/runner/SHA256SUMS", "file_count": 1, "distribution_mode": "skills-only", "live_mcp_bundled": False}).encode()

        valid = make_archive({"nested/readme.md": b"ok"})
        valid_report = json.loads(report(valid))
        valid_report["file_count"] = 1
        validate_bundle_report(json.dumps(valid_report).encode(), expected_name="aiworkstation-open-source-intelligence", expected_version="0.3.0", expected_archive_name="skills.zip", archive_bytes=valid)
        cases = [
            make_archive({"file.txt": b"x"}, manifest_overrides={"schema_version": "wrong"}),
            make_archive({"file.txt": b"x"}, manifest_overrides={"name": "wrong"}),
            make_archive({"file.txt": b"x"}, manifest_overrides={"version": "0.2.0"}),
            make_archive({"../file.txt": b"x"}),
            make_archive({"/absolute.txt": b"x"}),
            make_archive({"dir\\file.txt": b"x"}),
            make_archive({"file.txt": b"x"}, manifest_overrides={"files": [{"path": "file.txt", "size": 1, "sha256": "0" * 64}]}),
            make_archive({"file.txt": b"x"}, manifest_overrides={"files": [{"path": "file.txt", "size": 1, "sha256": hashlib.sha256(b"x").hexdigest()}, {"path": "file.txt", "size": 1, "sha256": hashlib.sha256(b"x").hexdigest()}]}),
            make_archive({"file.txt": b"x", "extra.txt": b"y"}, manifest_overrides={"files": [{"path": "file.txt", "size": 1, "sha256": hashlib.sha256(b"x").hexdigest()}]}),
            make_archive({"file.txt": b"x"}, manifest_overrides={"files": [{"path": "file.txt", "size": 1, "sha256": hashlib.sha256(b"x").hexdigest()}, {"path": "missing.txt", "size": 0, "sha256": "0" * 64}]}),
        ]
        for archive in cases:
            with self.assertRaises(ReleasePromotionError):
                validate_bundle_report(report(archive), expected_name="aiworkstation-open-source-intelligence", expected_version="0.3.0", expected_archive_name="skills.zip", archive_bytes=archive)
        duplicate = make_archive({"file.txt": b"x"}, duplicate_manifest=True)
        with self.assertRaises(ReleasePromotionError):
            validate_bundle_report(report(duplicate), expected_name="aiworkstation-open-source-intelligence", expected_version="0.3.0", expected_archive_name="skills.zip", archive_bytes=duplicate)
        missing_manifest = io.BytesIO()
        with zipfile.ZipFile(missing_manifest, "w") as archive: archive.writestr("file.txt", b"x")
        with self.assertRaises(ReleasePromotionError):
            validate_bundle_report(report(missing_manifest.getvalue()), expected_name="aiworkstation-open-source-intelligence", expected_version="0.3.0", expected_archive_name="skills.zip", archive_bytes=missing_manifest.getvalue())

    def test_draft_is_validated_by_release_id_target_and_asset_ids(self) -> None:
        identity = validate_release(release(draft=True), tag="v0.3.0", commit=COMMIT, expected_assets=ASSETS, draft=True)
        self.assertEqual(identity.release_id, 7)
        self.assertEqual(identity.asset_ids["wheel.whl"], 4)

    def test_locate_draft_requires_one_matching_api_object(self) -> None:
        self.assertEqual(locate_draft([release(draft=True)], tag="v0.3.0", commit=COMMIT, expected_assets=ASSETS).release_id, 7)  # type: ignore[union-attr]
        with self.assertRaises(ReleasePromotionError):
            locate_draft([release(draft=True), release(draft=True, release_id=8)], tag="v0.3.0", commit=COMMIT, expected_assets=ASSETS)
        self.assertIsNone(locate_draft([], tag="v0.3.0", commit=COMMIT, expected_assets=ASSETS))

    def test_draft_does_not_require_a_tag_ref(self) -> None:
        identity = locate_draft([release(draft=True)], tag="v0.3.0", commit=COMMIT, expected_assets=ASSETS)
        self.assertIsNotNone(identity)

    def test_final_state_machine_publishes_draft_or_accepts_matching_public(self) -> None:
        self.assertEqual(promotion_decision(release(draft=True), tag="v0.3.0", commit=COMMIT, expected_assets=ASSETS, release_id=7, prerelease=True, tag_commit=None), "publish")
        self.assertEqual(promotion_decision(release(draft=False), tag="v0.3.0", commit=COMMIT, expected_assets=ASSETS, release_id=7, prerelease=True, tag_commit=COMMIT), "already_public")

    def test_final_state_machine_rejects_public_identity_mismatch(self) -> None:
        with self.assertRaises(ReleasePromotionError):
            promotion_decision(release(draft=False, commit="b" * 40), tag="v0.3.0", commit=COMMIT, expected_assets=ASSETS, release_id=7, prerelease=True, tag_commit=COMMIT)
        with self.assertRaises(ReleasePromotionError):
            promotion_decision(release(draft=False, release_id=8), tag="v0.3.0", commit=COMMIT, expected_assets=ASSETS, release_id=7, prerelease=True, tag_commit=COMMIT)
        with self.assertRaises(ReleasePromotionError):
            promotion_decision(release(draft=False, prerelease=False), tag="v0.3.0", commit=COMMIT, expected_assets=ASSETS, release_id=7, prerelease=True, tag_commit=COMMIT)

    def test_public_preflight_requires_real_tag_commit_and_draft_requires_absence(self) -> None:
        validate_preflight_release(
            release(draft=True), tag="v0.3.0", commit=COMMIT, expected_assets=ASSETS,
            release_id=7, prerelease=True, tag_commit=None,
        )
        validate_preflight_release(
            release(draft=False), tag="v0.3.0", commit=COMMIT, expected_assets=ASSETS,
            release_id=7, prerelease=True, tag_commit=COMMIT,
        )
        with self.assertRaises(ReleasePromotionError):
            validate_preflight_release(
                release(draft=True), tag="v0.3.0", commit=COMMIT, expected_assets=ASSETS,
                release_id=7, prerelease=True, tag_commit=COMMIT,
            )
        with self.assertRaises(ReleasePromotionError):
            validate_preflight_release(
                release(draft=False), tag="v0.3.0", commit=COMMIT, expected_assets=ASSETS,
                release_id=7, prerelease=True, tag_commit="b" * 40,
            )

    def test_public_release_can_be_located_for_safe_final_rerun(self) -> None:
        identity = locate_release([release(draft=False)], tag="v0.3.0", commit=COMMIT, expected_assets=ASSETS)
        self.assertIsNotNone(identity)
        self.assertFalse(identity.draft)  # type: ignore[union-attr]
        with self.assertRaises(ReleasePromotionError):
            locate_release([release(draft=False), release(draft=True, release_id=8)], tag="v0.3.0", commit=COMMIT, expected_assets=ASSETS)

    def test_draft_and_public_release_with_same_tag_is_ambiguous(self) -> None:
        with self.assertRaises(ReleasePromotionError):
            locate_draft(
                [release(draft=True), release(draft=False, release_id=8)],
                tag="v0.3.0",
                commit=COMMIT,
                expected_assets=ASSETS,
            )

    def test_flatten_paginated_release_response(self) -> None:
        self.assertEqual(len(flatten_releases([[release(draft=True)], [release(draft=False)]])), 2)


if __name__ == "__main__":
    unittest.main()
