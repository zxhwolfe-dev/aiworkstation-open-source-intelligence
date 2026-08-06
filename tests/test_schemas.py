from __future__ import annotations

import json
import unittest
from pathlib import Path

from aiworkstation_osi.app import invoke_tool
from aiworkstation_osi.contracts import TOOL_NAMES


class MachineReadableSchemaTests(unittest.TestCase):
    ROOT = Path(__file__).resolve().parents[1]

    def test_manifest_matches_runtime_tool_names(self) -> None:
        manifest = json.loads((self.ROOT / "schemas" / "tool-manifest.json").read_text(encoding="utf-8"))
        names = tuple(tool["name"] for tool in manifest["tools"])
        self.assertEqual(names, TOOL_NAMES)
        self.assertTrue(all(tool["read_only"] is True for tool in manifest["tools"]))

    def test_result_schema_required_keys_exist_in_runtime_payload(self) -> None:
        schema = json.loads(
            (self.ROOT / "schemas" / "tool-result.schema.json").read_text(encoding="utf-8")
        )
        payload = invoke_tool("search_ai_projects", {"query": "RAG"})
        self.assertTrue(set(schema["required"]).issubset(payload))
        self.assertEqual(payload["schema_version"], schema["properties"]["schema_version"]["const"])

    def test_every_manifest_tool_has_object_input_schema(self) -> None:
        manifest = json.loads((self.ROOT / "schemas" / "tool-manifest.json").read_text(encoding="utf-8"))
        for tool in manifest["tools"]:
            with self.subTest(tool=tool["name"]):
                self.assertEqual(tool["input_schema"]["type"], "object")
                self.assertFalse(tool["input_schema"]["additionalProperties"])


if __name__ == "__main__":
    unittest.main()
