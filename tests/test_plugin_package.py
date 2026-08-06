from __future__ import annotations

import json
import re
import unittest
from pathlib import Path


class PluginPackageTests(unittest.TestCase):
    ROOT = Path(__file__).resolve().parents[1]
    MANIFEST_PATH = ROOT / ".codex-plugin" / "plugin.json"
    MARKETPLACE_PATH = ROOT / ".agents" / "plugins" / "marketplace.json"

    @classmethod
    def setUpClass(cls) -> None:
        cls.manifest = json.loads(cls.MANIFEST_PATH.read_text(encoding="utf-8"))
        cls.marketplace = json.loads(cls.MARKETPLACE_PATH.read_text(encoding="utf-8"))

    def test_plugin_directory_contains_only_manifest(self) -> None:
        entries = sorted(path.name for path in self.MANIFEST_PATH.parent.iterdir())
        self.assertEqual(entries, ["plugin.json"])

    def test_identity_and_version_are_stable(self) -> None:
        self.assertRegex(
            self.manifest["name"],
            r"^[a-z0-9]+(?:-[a-z0-9]+)*$",
        )
        self.assertRegex(
            self.manifest["version"],
            r"^(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)$",
        )
        self.assertTrue(self.manifest["description"].strip())
        self.assertEqual(
            self.manifest["name"],
            "aiworkstation-open-source-intelligence",
        )

    def test_manifest_packages_all_three_skill_directories(self) -> None:
        skills_path = self.manifest["skills"]
        self.assertTrue(skills_path.startswith("./"))
        skills_root = (self.ROOT / skills_path[2:]).resolve()
        self.assertTrue(skills_root.is_dir())
        self.assertTrue(skills_root.is_relative_to(self.ROOT.resolve()))

        skill_directories = {
            path.name
            for path in skills_root.iterdir()
            if path.is_dir() and (path / "SKILL.md").is_file()
        }
        self.assertEqual(
            skill_directories,
            {
                "open-source-project-research",
                "open-source-project-comparison",
                "open-source-stack-planner",
            },
        )

        for skill_name in sorted(skill_directories):
            content = (skills_root / skill_name / "SKILL.md").read_text(encoding="utf-8")
            frontmatter_name = re.search(r"(?m)^name:\s*([^\s]+)\s*$", content)
            description = re.search(r"(?m)^description:\s*(.+?)\s*$", content)
            self.assertIsNotNone(frontmatter_name, skill_name)
            self.assertIsNotNone(description, skill_name)
            assert frontmatter_name is not None
            self.assertEqual(frontmatter_name.group(1), skill_name)

    def test_install_surface_copy_is_complete_and_read_only(self) -> None:
        interface = self.manifest["interface"]
        for field in (
            "displayName",
            "shortDescription",
            "longDescription",
            "developerName",
            "category",
            "websiteURL",
            "defaultPrompt",
            "brandColor",
        ):
            self.assertTrue(interface[field], field)
        self.assertGreaterEqual(len(interface["defaultPrompt"]), 3)
        self.assertIn("Read", interface["capabilities"])
        self.assertNotIn("Write", interface["capabilities"])

    def test_manifest_does_not_claim_ungranted_license_or_unready_mcp_binding(self) -> None:
        self.assertNotIn("license", self.manifest)
        self.assertNotIn("mcpServers", self.manifest)
        self.assertNotIn("apps", self.manifest)
        interface = self.manifest["interface"]
        self.assertNotIn("privacyPolicyURL", interface)
        self.assertNotIn("termsOfServiceURL", interface)

    def test_repo_marketplace_points_to_plugin_root(self) -> None:
        self.assertEqual(self.marketplace["name"], "aiworkstation-local-plugins")
        self.assertTrue(self.marketplace["interface"]["displayName"])
        self.assertEqual(len(self.marketplace["plugins"]), 1)
        entry = self.marketplace["plugins"][0]
        self.assertEqual(entry["name"], self.manifest["name"])
        self.assertEqual(entry["source"], {"source": "local", "path": "./"})
        self.assertEqual(entry["policy"]["installation"], "AVAILABLE")
        self.assertEqual(entry["policy"]["authentication"], "ON_INSTALL")
        self.assertEqual(entry["category"], "Developer Tools")


if __name__ == "__main__":
    unittest.main()
