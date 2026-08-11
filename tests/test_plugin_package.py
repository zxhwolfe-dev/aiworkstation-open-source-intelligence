from __future__ import annotations

import json
import re
import unittest
from pathlib import Path


class PluginPackageTests(unittest.TestCase):
    ROOT = Path(__file__).resolve().parents[1]
    MANIFEST_PATH = ROOT / ".codex-plugin" / "plugin.json"
    MCP_PATH = ROOT / ".mcp.json"
    MARKETPLACE_PATH = ROOT / ".agents" / "plugins" / "marketplace.json"

    @classmethod
    def setUpClass(cls) -> None:
        cls.manifest = json.loads(cls.MANIFEST_PATH.read_text(encoding="utf-8"))
        cls.mcp = json.loads(cls.MCP_PATH.read_text(encoding="utf-8"))
        cls.marketplace = json.loads(cls.MARKETPLACE_PATH.read_text(encoding="utf-8"))

    def test_plugin_directory_contains_only_manifest(self) -> None:
        entries = sorted(path.name for path in self.MANIFEST_PATH.parent.iterdir())
        self.assertEqual(entries, ["plugin.json"])

    def test_identity_version_and_license_are_stable(self) -> None:
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
        self.assertEqual(self.manifest["license"], "Apache-2.0")
        self.assertTrue((self.ROOT / "LICENSE").is_file())

    def test_manifest_packages_exactly_one_unified_skill(self) -> None:
        skills_path = self.manifest["skills"]
        self.assertEqual(skills_path, "./product-skills/")
        skills_root = (self.ROOT / skills_path[2:]).resolve()
        self.assertTrue(skills_root.is_dir())
        self.assertTrue(skills_root.is_relative_to(self.ROOT.resolve()))

        skill_directories = {
            path.name
            for path in skills_root.iterdir()
            if path.is_dir() and (path / "SKILL.md").is_file()
        }
        self.assertEqual(skill_directories, {"ai-open-source-intelligence"})

        content = (skills_root / "ai-open-source-intelligence" / "SKILL.md").read_text(
            encoding="utf-8"
        )
        frontmatter_name = re.search(r"(?m)^name:\s*([^\s]+)\s*$", content)
        description = re.search(r"(?m)^description:\s*(.+?)\s*$", content)
        self.assertIsNotNone(frontmatter_name)
        self.assertIsNotNone(description)
        assert frontmatter_name is not None
        self.assertEqual(frontmatter_name.group(1), "ai-open-source-intelligence")

        self.assertFalse((self.ROOT / "skills" / "open-source-project-research" / "SKILL.md").exists())
        self.assertFalse((self.ROOT / "skills" / "open-source-project-comparison" / "SKILL.md").exists())
        self.assertFalse((self.ROOT / "skills" / "open-source-stack-planner" / "SKILL.md").exists())

    def test_install_surface_copy_is_complete_and_read_only(self) -> None:
        interface = self.manifest["interface"]
        for field in (
            "displayName",
            "shortDescription",
            "longDescription",
            "developerName",
            "category",
            "websiteURL",
            "supportURL",
            "privacyPolicyURL",
            "termsOfServiceURL",
            "defaultPrompt",
            "brandColor",
            "composerIcon",
            "logo",
        ):
            self.assertTrue(interface[field], field)
        self.assertGreaterEqual(len(interface["defaultPrompt"]), 1)
        self.assertLessEqual(len(interface["defaultPrompt"]), 3)
        self.assertTrue(all(len(prompt) <= 128 for prompt in interface["defaultPrompt"]))
        self.assertLessEqual(len(interface["displayName"]), 30)
        self.assertLessEqual(len(interface["shortDescription"]), 30)
        self.assertIn("Read", interface["capabilities"])
        self.assertNotIn("Write", interface["capabilities"])
        self.assertIn("host model", interface["longDescription"].lower())
        self.assertIn("must not invoke", interface["longDescription"].lower())

    def test_manifest_uses_ai_workstation_public_site_and_hosted_legal_pages(self) -> None:
        interface = self.manifest["interface"]
        self.assertEqual(interface["websiteURL"], "https://aiworkstation.cn/githubai/")
        self.assertEqual(self.manifest["homepage"], "https://aiworkstation.cn/githubai/")
        self.assertEqual(interface["privacyPolicyURL"], "https://useaistation.com/githubai/privacy/")
        self.assertEqual(interface["termsOfServiceURL"], "https://useaistation.com/terms/")
        self.assertIn("github.com", interface["supportURL"])
        self.assertEqual(self.manifest["mcpServers"], "./.mcp.json")
        self.assertNotIn("apps", self.manifest)
        self.assertEqual(interface["composerIcon"], "./assets/plugin-icon.svg")
        self.assertEqual(interface["logo"], "./assets/plugin-icon.svg")
        self.assertTrue((self.ROOT / "assets" / "plugin-icon.svg").is_file())

    def test_plugin_bundles_the_reviewed_hosted_mcp_connection(self) -> None:
        self.assertEqual(
            self.mcp,
            {
                "mcp_servers": {
                    "ai_open_source_intelligence": {
                        "url": "https://mcp.aiworkstation.cn/mcp",
                        "enabled": True,
                        "required": False,
                        "default_tools_approval_mode": "auto",
                        "startup_timeout_sec": 20,
                        "tool_timeout_sec": 60,
                    }
                }
            },
        )

    def test_repo_marketplace_points_to_plugin_root(self) -> None:
        self.assertEqual(self.marketplace["name"], "aiworkstation-local-plugins")
        self.assertTrue(self.marketplace["interface"]["displayName"])
        self.assertEqual(len(self.marketplace["plugins"]), 1)
        entry = self.marketplace["plugins"][0]
        self.assertEqual(entry["name"], self.manifest["name"])
        self.assertEqual(entry["source"], {"source": "local", "path": "./"})
        self.assertEqual(entry["policy"]["installation"], "AVAILABLE")
        self.assertEqual(entry["policy"]["authentication"], "NONE")
        self.assertEqual(entry["category"], "Developer Tools")


if __name__ == "__main__":
    unittest.main()
