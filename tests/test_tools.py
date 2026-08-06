from __future__ import annotations

import unittest

from aiworkstation_osi.app import create_default_registry, invoke_tool
from aiworkstation_osi.errors import InvalidInputError, UnknownToolError
from aiworkstation_osi.tools import (
    MAX_STRUCTURED_CONTAINER_ITEMS,
    MAX_STRUCTURED_DEPTH,
    MAX_STRUCTURED_STRING_LENGTH,
)


class ToolRegistryTests(unittest.TestCase):
    def setUp(self) -> None:
        self.registry = create_default_registry()

    def test_registry_exposes_exact_m0_tool_set(self) -> None:
        self.assertEqual(
            [spec.name for spec in self.registry.specs],
            [
                "search_ai_projects",
                "get_project_facts",
                "get_license_evidence",
                "compare_ai_projects",
                "find_alternatives",
                "compose_ai_stack",
            ],
        )

    def test_search_returns_contract_envelope_and_mock_warning(self) -> None:
        payload = invoke_tool(
            "search_ai_projects",
            {
                "query": "self-hosted RAG with Docker and web UI",
                "constraints": {"deployment": "self-hosted"},
                "request_id": "search-1",
            },
        )

        self.assertEqual(payload["tool"], "search_ai_projects")
        self.assertEqual(payload["request_id"], "search-1")
        self.assertGreaterEqual(payload["data"]["total"], 1)
        self.assertEqual(payload["verified_facts"], ())
        self.assertIn("fixture data", payload["unknowns"][0])
        self.assertEqual(payload["risks"][0]["code"], "MOCK_DATA")

    def test_license_tool_always_marks_legal_boundary(self) -> None:
        payload = invoke_tool(
            "get_license_evidence",
            {"project_id": "infiniflow/ragflow"},
        )

        codes = {risk["code"] for risk in payload["risks"]}
        self.assertIn("NOT_LEGAL_ADVICE", codes)
        self.assertIn("MOCK_DATA", codes)

    def test_comparison_requires_two_unique_projects(self) -> None:
        with self.assertRaises(InvalidInputError):
            self.registry.invoke(
                "compare_ai_projects",
                {"project_ids": ["langgenius/dify", "langgenius/dify"]},
            )

    def test_unknown_tool_is_rejected(self) -> None:
        with self.assertRaises(UnknownToolError):
            self.registry.invoke("delete_repository", {})

    def test_stack_planner_keeps_analysis_out_of_verified_facts(self) -> None:
        payload = invoke_tool(
            "compose_ai_stack",
            {
                "business_goal": "Build an internal document question-answering system",
                "constraints": {"deployment": "self-hosted"},
            },
        )

        self.assertEqual(payload["verified_facts"], ())
        self.assertTrue(payload["recommendations"])
        self.assertIn("INTEGRATION_NOT_VERIFIED", {risk["code"] for risk in payload["risks"]})

    def test_search_rejects_invalid_locale_and_source_mode(self) -> None:
        with self.assertRaises(InvalidInputError):
            self.registry.invoke("search_ai_projects", {"query": "RAG", "locale": "fr"})
        with self.assertRaises(InvalidInputError):
            self.registry.invoke("search_ai_projects", {"query": "RAG", "source_mode": "sometimes"})

    def test_tools_reject_undeclared_fields(self) -> None:
        with self.assertRaises(InvalidInputError) as context:
            self.registry.invoke(
                "get_project_facts",
                {"project_id": "langgenius/dify", "execute_repository": True},
            )
        self.assertIn("execute_repository", context.exception.details["unsupported_fields"])

    def test_arguments_must_be_an_object(self) -> None:
        with self.assertRaises(InvalidInputError):
            self.registry.invoke("search_ai_projects", ["RAG"])  # type: ignore[arg-type]

    def test_request_id_is_not_silently_truncated(self) -> None:
        with self.assertRaises(InvalidInputError):
            self.registry.invoke(
                "search_ai_projects",
                {"query": "RAG", "request_id": "x" * 129},
            )

    def test_nested_json_compatible_constraints_are_accepted(self) -> None:
        result = self.registry.invoke(
            "search_ai_projects",
            {
                "query": "private RAG",
                "constraints": {
                    "deployment": {
                        "required": ["docker", "self-hosted"],
                        "preferred": {"platforms": ["linux", "windows"]},
                    },
                    "budget": 1000,
                    "offline": True,
                    "maximum_latency": 2.5,
                    "notes": None,
                },
            },
        )
        self.assertEqual(result.tool, "search_ai_projects")

    def test_structured_inputs_reject_excessive_depth(self) -> None:
        value: object = "leaf"
        for index in range(MAX_STRUCTURED_DEPTH + 2):
            value = {f"level_{index}": value}
        with self.assertRaises(InvalidInputError) as context:
            self.registry.invoke(
                "search_ai_projects",
                {"query": "RAG", "constraints": value},  # type: ignore[arg-type]
            )
        self.assertIn("nesting depth", context.exception.message)

    def test_structured_inputs_reject_oversized_strings_and_arrays(self) -> None:
        with self.assertRaises(InvalidInputError):
            self.registry.invoke(
                "search_ai_projects",
                {
                    "query": "RAG",
                    "constraints": {"note": "x" * (MAX_STRUCTURED_STRING_LENGTH + 1)},
                },
            )
        with self.assertRaises(InvalidInputError):
            self.registry.invoke(
                "search_ai_projects",
                {
                    "query": "RAG",
                    "constraints": {"targets": list(range(MAX_STRUCTURED_CONTAINER_ITEMS + 1))},
                },
            )

    def test_structured_inputs_reject_non_json_and_non_finite_values(self) -> None:
        with self.assertRaises(InvalidInputError) as non_json:
            self.registry.invoke(
                "compare_ai_projects",
                {
                    "project_ids": ["one/project", "two/project"],
                    "context": {"unsupported": {"set-value"}},
                },
            )
        self.assertIn("JSON-compatible", non_json.exception.message)

        with self.assertRaises(InvalidInputError) as non_finite:
            self.registry.invoke(
                "search_ai_projects",
                {"query": "RAG", "constraints": {"weight": float("nan")}},
            )
        self.assertIn("non-finite", non_finite.exception.message)

    def test_structured_inputs_reject_invalid_keys(self) -> None:
        with self.assertRaises(InvalidInputError):
            self.registry.invoke(
                "search_ai_projects",
                {"query": "RAG", "constraints": {"bad\nkey": "value"}},
            )


if __name__ == "__main__":
    unittest.main()
