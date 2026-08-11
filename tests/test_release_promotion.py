from __future__ import annotations

import unittest

from aiworkstation_osi.release_promotion import (
    ReleasePromotionError,
    flatten_releases,
    locate_draft,
    locate_release,
    promotion_decision,
    validate_release,
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
        self.assertEqual(promotion_decision(release(draft=True), tag="v0.3.0", commit=COMMIT, expected_assets=ASSETS, release_id=7, prerelease=True), "publish")
        self.assertEqual(promotion_decision(release(draft=False), tag="v0.3.0", commit=COMMIT, expected_assets=ASSETS, release_id=7, prerelease=True), "already_public")

    def test_final_state_machine_rejects_public_identity_or_hash_mismatch(self) -> None:
        with self.assertRaises(ReleasePromotionError):
            promotion_decision(release(draft=False, commit="b" * 40), tag="v0.3.0", commit=COMMIT, expected_assets=ASSETS, release_id=7, prerelease=True)
        with self.assertRaises(ReleasePromotionError):
            promotion_decision(release(draft=False, release_id=8), tag="v0.3.0", commit=COMMIT, expected_assets=ASSETS, release_id=7, prerelease=True)

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
