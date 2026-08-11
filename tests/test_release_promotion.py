from __future__ import annotations

import unittest

from aiworkstation_osi.release_promotion import (
    ReleasePromotionError,
    flatten_releases,
    locate_draft,
    locate_release,
    parse_checksum_manifest,
    promotion_decision,
    validate_bundle_report,
    validate_preflight_release,
    validate_release,
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

    def test_final_state_machine_rejects_public_identity_or_hash_mismatch(self) -> None:
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
