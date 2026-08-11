from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from aiworkstation_osi.plugin_validation import validate_plugin_package


class PluginValidationTests(unittest.TestCase):
    ROOT = Path(__file__).resolve().parents[1]

    def test_current_repository_is_local_and_public_metadata_ready(self) -> None:
        report = validate_plugin_package(self.ROOT)

        self.assertTrue(report["local_skills_ready"])
        self.assertTrue(report["mcp_configuration_bundled"])
        self.assertTrue(report["public_submission_ready"])
        self.assertEqual(report["summary"]["errors"], 0)
        rendered = " ".join(report["warnings"])
        self.assertNotIn("software license", rendered)
        self.assertNotIn("privacy policy", rendered)
        self.assertNotIn("terms", rendered)
        self.assertNotIn("Skills-only", rendered)
        self.assertNotIn("separate local workflow", rendered)

    def test_invalid_identity_relative_path_and_missing_marketplace_fail(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            manifest_dir = root / ".codex-plugin"
            manifest_dir.mkdir(parents=True)
            (manifest_dir / "extra.json").write_text("{}", encoding="utf-8")
            (manifest_dir / "plugin.json").write_text(
                json.dumps(
                    {
                        "name": "Invalid Plugin Name",
                        "version": "v1",
                        "description": "test",
                        "skills": "skills/",
                        "interface": {},
                    }
                ),
                encoding="utf-8",
            )
            report = validate_plugin_package(root)

        self.assertFalse(report["local_skills_ready"])
        rendered = " ".join(report["errors"])
        self.assertIn("only plugin.json", rendered)
        self.assertIn("kebab-case", rendered)
        self.assertIn("semantic", rendered)
        self.assertIn("./-prefixed", rendered)
        self.assertIn("marketplace.json", rendered)

    def test_declared_mcp_file_must_exist_at_plugin_root(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            self._write_minimal_package(
                root,
                manifest_overrides={"mcpServers": "./nested/.mcp.json"},
            )
            report = validate_plugin_package(root)

        self.assertFalse(report["local_skills_ready"])
        rendered = " ".join(report["errors"])
        self.assertIn("must point to .mcp.json", rendered)
        self.assertIn("target does not exist", rendered)

    def test_hosted_mcp_configuration_must_match_the_reviewed_public_endpoint(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            self._write_minimal_package(
                root,
                manifest_overrides={"mcpServers": "./.mcp.json"},
            )
            (root / ".mcp.json").write_text(
                json.dumps(
                    {
                        "mcp_servers": {
                            "ai_open_source_intelligence": {
                                "url": "https://example.com/mcp",
                                "enabled": True,
                                "required": False,
                                "default_tools_approval_mode": "auto",
                                "startup_timeout_sec": 20,
                                "tool_timeout_sec": 60,
                            }
                        }
                    }
                ),
                encoding="utf-8",
            )
            report = validate_plugin_package(root)

        self.assertFalse(report["local_skills_ready"])
        self.assertFalse(report["mcp_configuration_bundled"])
        self.assertIn("Hosted MCP URL", " ".join(report["errors"]))

    def test_skill_frontmatter_name_must_match_directory(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            self._write_minimal_package(root, skill_name="different-name")
            report = validate_plugin_package(root)

        self.assertFalse(report["local_skills_ready"])
        self.assertTrue(any("must match directory" in value for value in report["errors"]))

    @staticmethod
    def _write_minimal_package(
        root: Path,
        *,
        manifest_overrides: dict[str, object] | None = None,
        skill_name: str = "directory-name",
    ) -> None:
        (root / ".codex-plugin").mkdir(parents=True)
        (root / ".agents" / "plugins").mkdir(parents=True)
        skill_dir = root / "skills" / "directory-name"
        skill_dir.mkdir(parents=True)
        (skill_dir / "SKILL.md").write_text(
            f"---\nname: {skill_name}\ndescription: Example workflow.\n---\n",
            encoding="utf-8",
        )
        manifest: dict[str, object] = {
            "name": "example-plugin",
            "version": "0.1.0",
            "description": "Example plugin.",
            "skills": "./skills/",
            "interface": {
                "displayName": "Example",
                "shortDescription": "Example",
                "longDescription": "Example plugin description.",
                "developerName": "Example",
                "category": "Developer Tools",
                "capabilities": ["Read"],
                "websiteURL": "https://example.com",
                "defaultPrompt": ["One", "Two", "Three"],
                "brandColor": "#123456",
            },
        }
        manifest.update(manifest_overrides or {})
        (root / ".codex-plugin" / "plugin.json").write_text(
            json.dumps(manifest), encoding="utf-8"
        )
        marketplace = {
            "name": "example-marketplace",
            "interface": {"displayName": "Example"},
            "plugins": [
                {
                    "name": "example-plugin",
                    "source": {"source": "local", "path": "./"},
                    "policy": {
                        "installation": "AVAILABLE",
                        "authentication": "ON_INSTALL",
                    },
                    "category": "Developer Tools",
                }
            ],
        }
        (root / ".agents" / "plugins" / "marketplace.json").write_text(
            json.dumps(marketplace), encoding="utf-8"
        )


if __name__ == "__main__":
    unittest.main()
