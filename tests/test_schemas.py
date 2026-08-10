from __future__ import annotations

import json
import unittest
from pathlib import Path
from jsonschema import Draft202012Validator, FormatChecker

from aiworkstation_osi.app import invoke_tool
from aiworkstation_osi.errors import InvalidInputError, ProviderOverloadedError
from aiworkstation_osi.contracts import TOOL_NAMES
from aiworkstation_osi.tools import (
    MAX_STRUCTURED_CONTAINER_ITEMS,
    MAX_STRUCTURED_DEPTH,
    MAX_STRUCTURED_KEY_LENGTH,
    MAX_STRUCTURED_NODES,
    MAX_STRUCTURED_STRING_LENGTH,
)


class MachineReadableSchemaTests(unittest.TestCase):
    ROOT = Path(__file__).resolve().parents[1]

    def _manifest(self) -> dict:
        return json.loads(
            (self.ROOT / "schemas" / "tool-manifest.json").read_text(encoding="utf-8")
        )

    def test_manifest_matches_runtime_tool_names(self) -> None:
        manifest = self._manifest()
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

    def test_every_tool_result_validates_against_draft_2020_12(self) -> None:
        schema = json.loads((self.ROOT / "schemas" / "tool-result.schema.json").read_text(encoding="utf-8"))
        Draft202012Validator.check_schema(schema)
        validator = Draft202012Validator(schema, format_checker=FormatChecker())
        arguments = {
            "search_ai_projects": {"query": "RAG"},
            "get_project_facts": {"project_id": "infiniflow/ragflow"},
            "get_license_evidence": {"project_id": "infiniflow/ragflow"},
            "compare_ai_projects": {"project_ids": ["langgenius/dify", "infiniflow/ragflow"]},
            "find_alternatives": {"project_id": "langgenius/dify"},
            "compose_ai_stack": {"business_goal": "Internal document QA"},
            "get_radar_overview": {}, "browse_radar_projects": {}, "browse_radar_skills": {},
        }
        for tool_name, tool_arguments in arguments.items():
            with self.subTest(tool=tool_name):
                validator.validate(invoke_tool(tool_name, tool_arguments))

    def test_public_errors_validate_against_draft_2020_12(self) -> None:
        schema = json.loads((self.ROOT / "schemas" / "error.schema.json").read_text(encoding="utf-8"))
        Draft202012Validator.check_schema(schema)
        validator = Draft202012Validator(schema)
        for error in (InvalidInputError("invalid"), ProviderOverloadedError()):
            with self.subTest(code=error.code):
                validator.validate(error.to_dict())

    def test_every_manifest_tool_has_object_input_schema(self) -> None:
        manifest = self._manifest()
        for tool in manifest["tools"]:
            with self.subTest(tool=tool["name"]):
                self.assertEqual(tool["input_schema"]["type"], "object")
                self.assertFalse(tool["input_schema"]["additionalProperties"])

    def test_runtime_structured_limits_are_published(self) -> None:
        limits = self._manifest()["runtime_limits"]
        self.assertEqual(limits["structured_max_depth"], MAX_STRUCTURED_DEPTH)
        self.assertEqual(limits["structured_max_nodes"], MAX_STRUCTURED_NODES)
        self.assertEqual(
            limits["structured_max_container_items"],
            MAX_STRUCTURED_CONTAINER_ITEMS,
        )
        self.assertEqual(limits["structured_max_key_length"], MAX_STRUCTURED_KEY_LENGTH)
        self.assertEqual(
            limits["structured_max_string_length"],
            MAX_STRUCTURED_STRING_LENGTH,
        )

    def test_structured_properties_publish_recursive_bounds(self) -> None:
        manifest = self._manifest()
        structured_properties = {
            "search_ai_projects": "constraints",
            "compare_ai_projects": "context",
            "find_alternatives": "constraints",
            "compose_ai_stack": "constraints",
        }
        by_name = {tool["name"]: tool for tool in manifest["tools"]}
        for tool_name, property_name in structured_properties.items():
            with self.subTest(tool=tool_name, property=property_name):
                schema = by_name[tool_name]["input_schema"]
                prop = schema["properties"][property_name]
                if property_name == "context":
                    self.assertEqual(prop["type"], "object")
                    self.assertEqual(prop["maxProperties"], MAX_STRUCTURED_CONTAINER_ITEMS)
                else:
                    self.assertEqual(prop["type"], "array")
                    self.assertEqual(prop["maxItems"], MAX_STRUCTURED_CONTAINER_ITEMS)
                    self.assertEqual(prop["items"]["$ref"], "#/$defs/constraint")


if __name__ == "__main__":
    unittest.main()
