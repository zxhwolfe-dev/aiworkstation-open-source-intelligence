from __future__ import annotations

import unittest
from unittest.mock import patch

from aiworkstation_osi import __version__
from aiworkstation_osi.release_identity import (
    hosted_server_version,
    load_image_commit,
    load_release_commit,
    normalize_image_commit,
    normalize_release_commit,
    release_commit_from_server_version,
    validate_hosted_deployment_identity,
)


class ReleaseIdentityTests(unittest.TestCase):
    def test_commit_is_normalized_and_round_trips_through_server_version(self) -> None:
        commit = "A" * 40
        normalized = normalize_release_commit(commit)
        self.assertEqual(normalized, "a" * 40)
        self.assertEqual(normalize_image_commit(commit), "a" * 40)
        version = hosted_server_version(commit)
        self.assertEqual(version, f"{__version__}+git.{'a' * 40}")
        self.assertEqual(release_commit_from_server_version(version), "a" * 40)

    def test_surrounding_environment_whitespace_is_normalized(self) -> None:
        commit = "a" * 40
        self.assertEqual(normalize_release_commit(f"  {commit}\n"), commit)
        self.assertEqual(normalize_image_commit(f"  {commit}\n"), commit)

    def test_invalid_release_or_image_commit_fails_closed(self) -> None:
        for value in ("", "abc", "g" * 40, "a" * 39, "a" * 41):
            with self.subTest(value=value), self.assertRaises(ValueError):
                normalize_release_commit(value)
            with self.subTest(image_value=value), self.assertRaises(ValueError):
                normalize_image_commit(value)

    def test_environment_is_required_for_hosted_runtime(self) -> None:
        with patch.dict("os.environ", {}, clear=True):
            with self.assertRaises(ValueError):
                load_release_commit(required=True)
            with self.assertRaises(ValueError):
                load_image_commit(required=True)
            self.assertEqual(load_release_commit(required=False), "")
            self.assertEqual(load_image_commit(required=False), "")

    def test_runtime_and_baked_image_commit_must_match(self) -> None:
        commit = "a" * 40
        with patch.dict(
            "os.environ",
            {"OSI_RELEASE_COMMIT": commit, "OSI_IMAGE_COMMIT": commit},
            clear=True,
        ):
            self.assertEqual(validate_hosted_deployment_identity(), commit)

        with patch.dict(
            "os.environ",
            {"OSI_RELEASE_COMMIT": commit, "OSI_IMAGE_COMMIT": "b" * 40},
            clear=True,
        ), self.assertRaises(ValueError) as context:
            validate_hosted_deployment_identity()
        self.assertIn("does not match", str(context.exception))

    def test_missing_baked_image_identity_fails_even_when_runtime_sha_exists(self) -> None:
        with patch.dict(
            "os.environ",
            {"OSI_RELEASE_COMMIT": "a" * 40},
            clear=True,
        ), self.assertRaises(ValueError) as context:
            validate_hosted_deployment_identity()
        self.assertIn("OSI_IMAGE_COMMIT", str(context.exception))

    def test_invalid_server_version_does_not_create_identity(self) -> None:
        for version in ("", __version__, f"{__version__}+git.abc", "other+git." + "a" * 39):
            with self.subTest(version=version):
                self.assertEqual(release_commit_from_server_version(version), "")


if __name__ == "__main__":
    unittest.main()
