from __future__ import annotations

import json
import re
import unittest
from pathlib import Path

from aiworkstation_osi import __version__


class VersionAlignmentTests(unittest.TestCase):
    ROOT = Path(__file__).resolve().parents[1]

    def test_python_plugin_and_changelog_versions_align(self) -> None:
        plugin = json.loads(
            (self.ROOT / ".codex-plugin" / "plugin.json").read_text(encoding="utf-8")
        )
        pyproject = (self.ROOT / "pyproject.toml").read_text(encoding="utf-8")
        changelog = (self.ROOT / "CHANGELOG.md").read_text(encoding="utf-8")

        python_version = __version__
        plugin_version = plugin["version"]

        self.assertEqual(python_version, plugin_version)
        self.assertIn(f"## [{plugin_version}]", changelog)
        self.assertNotRegex(pyproject, r'(?m)^version\s*=\s*"')

    def test_version_is_plain_semantic_version_for_current_plugin_contract(self) -> None:
        plugin = json.loads(
            (self.ROOT / ".codex-plugin" / "plugin.json").read_text(encoding="utf-8")
        )
        self.assertRegex(plugin["version"], r"^(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)$")


if __name__ == "__main__":
    unittest.main()
