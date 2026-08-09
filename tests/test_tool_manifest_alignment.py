from __future__ import annotations

import json
import unittest
from pathlib import Path

from aiworkstation_osi.app import create_default_registry
from aiworkstation_osi.contracts import HOSTED_TOOL_NAMES, TOOL_NAMES


class ToolManifestAlignmentTests(unittest.TestCase):
    ROOT = Path(__file__).resolve().parents[1]

    def test_manifest_matches_registry_and_contract_tool_order(self) -> None:
        manifest = json.loads((self.ROOT / "schemas" / "tool-manifest.json").read_text(encoding="utf-8"))
        manifest_names = [str(row["name"]) for row in manifest["tools"]]
        registry_names = [spec.name for spec in create_default_registry().specs]
        self.assertEqual(manifest_names, list(TOOL_NAMES))
        self.assertEqual(registry_names, list(TOOL_NAMES))
        self.assertEqual(len(TOOL_NAMES), 9)

    def test_manifest_tools_are_read_only_with_explicit_input_fields(self) -> None:
        manifest = json.loads((self.ROOT / "schemas" / "tool-manifest.json").read_text(encoding="utf-8"))
        for row in manifest["tools"]:
            with self.subTest(tool=row["name"]):
                self.assertIs(row["read_only"], True)
                self.assertIn("additionalProperties", row["input_schema"])
                self.assertIs(row["input_schema"]["additionalProperties"], False)

    def test_browse_tool_pagination_limits_match_runtime(self) -> None:
        manifest = json.loads((self.ROOT / "schemas" / "tool-manifest.json").read_text(encoding="utf-8"))
        by_name = {row["name"]: row for row in manifest["tools"]}
        for name in ("browse_radar_projects", "browse_radar_skills"):
            properties = by_name[name]["input_schema"]["properties"]
            self.assertEqual(properties["limit"]["minimum"], 1)
            self.assertEqual(properties["limit"]["maximum"], 50)
            self.assertEqual(properties["offset"]["minimum"], 0)
            self.assertEqual(properties["offset"]["maximum"], 10000)

    def test_hosted_manifest_is_exactly_nine_tool_data_only_surface(self) -> None:
        hosted = json.loads(
            (self.ROOT / "schemas" / "hosted-tool-manifest.json").read_text(encoding="utf-8")
        )
        self.assertEqual(hosted["status"], "hosted-public-data-only")
        self.assertIs(hosted["authentication"]["required"], False)
        self.assertEqual(hosted["authentication"]["scheme"], "none")
        self.assertIs(hosted["server_model_execution"], False)
        self.assertEqual(hosted["base_tools"], list(TOOL_NAMES))
        self.assertEqual(list(HOSTED_TOOL_NAMES), list(TOOL_NAMES))
        self.assertEqual(hosted["hosted_only_tools"], [])
        resources = hosted["official_resources"]
        self.assertEqual(resources["website"], "https://aiworkstation.cn/")
        self.assertEqual(resources["radar"], "https://aiworkstation.cn/githubai/")


if __name__ == "__main__":
    unittest.main()
