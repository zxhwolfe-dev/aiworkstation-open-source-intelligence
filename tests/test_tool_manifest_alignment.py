from __future__ import annotations

import json
import unittest
from pathlib import Path

from aiworkstation_osi.app import create_default_registry
from aiworkstation_osi.contracts import TOOL_NAMES


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

    def test_hosted_manifest_matches_public_default_and_optional_oauth_surface(self) -> None:
        hosted = json.loads(
            (self.ROOT / "schemas" / "hosted-tool-manifest.json").read_text(encoding="utf-8")
        )
        self.assertEqual(hosted["default_access_mode"], "public")
        public = hosted["access_modes"]["public"]
        oauth = hosted["access_modes"]["oauth"]
        self.assertIs(public["authentication_required"], False)
        self.assertEqual(public["tool_count"], 9)
        self.assertIs(public["premium_enabled"], False)
        self.assertIs(oauth["authentication_required"], True)
        self.assertEqual(oauth["required_scopes"], [])
        self.assertEqual(oauth["tool_count"], 10)
        self.assertEqual(hosted["base_tools"], list(TOOL_NAMES))
        hosted_names = [str(row["name"]) for row in hosted["hosted_only_tools"]]
        self.assertEqual(hosted_names, ["deep_research_ai_projects"])
        self.assertEqual(hosted["hosted_only_tools"][0]["enabled_in_modes"], ["oauth"])
        membership = hosted["membership_policy"]
        self.assertEqual(membership["source_of_truth"], "AI Workstation membership")
        self.assertIs(membership["separate_osi_subscription_system"], False)
        self.assertIs(membership["invite_or_activation_code_may_be_mcp_bearer_token"], False)


if __name__ == "__main__":
    unittest.main()
