from __future__ import annotations

import unittest
from unittest.mock import patch

from aiworkstation_osi import __version__
from aiworkstation_osi.release_identity import (
    hosted_server_version,
    load_release_commit,
    normalize_release_commit,
    release_commit_from_server_version,
)


class ReleaseIdentityTests(unittest.TestCase):
    def test_commit_is_normalized_and_round_trips_through_server_version(self) -> None:
        commit = "A" * 40
        normalized = normalize_release_commit(commit)
        self.assertEqual(normalized, "a" * 40)
        version = hosted_server_version(commit)
        self.assertEqual(version, f"{__version__}+git.{'a' * 40}")
        self.assertEqual(release_commit_from_server_version(version), "a" * 40)

    def test_invalid_release_commit_fails_closed(self) -> None:
        for value in ("", "abc", "g" * 40, "a" * 39, "a" * 41, "a" * 40 + " "):
            with self.subTest(value=value), self.assertRaises(ValueError):
                normalize_release_commit(value)

    def test_environment_is_required_for_hosted_runtime(self) -> None:
        with patch.dict("os.environ", {}, clear=True):
            with self.assertRaises(ValueError):
                load_release_commit(required=True)
            self.assertEqual(load_release_commit(required=False), "")

    def test_invalid_server_version_does_not_create_identity(self) -> None:
        for version in ("", __version__, f"{__version__}+git.abc", "other+git." + "a" * 39):
            with self.subTest(version=version):
                self.assertEqual(release_commit_from_server_version(version), "")


if __name__ == "__main__":
    unittest.main()
