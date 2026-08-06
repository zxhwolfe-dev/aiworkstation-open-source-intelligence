from __future__ import annotations

import unittest
from typing import Any, Mapping

from aiworkstation_osi.errors import ProviderUnavailableError, UpstreamContractError
from aiworkstation_osi.tools import ToolRegistry


class NonObjectProvider:
    def search_projects(self, request: Mapping[str, Any]):
        return []

    def get_project_facts(self, request: Mapping[str, Any]):
        return {}

    def get_license_evidence(self, request: Mapping[str, Any]):
        return {}

    def compare_projects(self, request: Mapping[str, Any]):
        return {}

    def find_alternatives(self, request: Mapping[str, Any]):
        return {}

    def compose_stack(self, request: Mapping[str, Any]):
        return {}


class FailingProvider(NonObjectProvider):
    def search_projects(self, request: Mapping[str, Any]):
        raise RuntimeError("private upstream detail must not leak")


class ProviderBoundaryTests(unittest.TestCase):
    def test_non_object_provider_payload_is_rejected_as_contract_error(self) -> None:
        registry = ToolRegistry(NonObjectProvider())
        with self.assertRaises(UpstreamContractError) as context:
            registry.invoke("search_ai_projects", {"query": "RAG"})
        self.assertEqual(context.exception.code, "UPSTREAM_CONTRACT_ERROR")

    def test_provider_exception_is_normalized_without_private_message(self) -> None:
        registry = ToolRegistry(FailingProvider())
        with self.assertRaises(ProviderUnavailableError) as context:
            registry.invoke("search_ai_projects", {"query": "RAG"})
        self.assertEqual(context.exception.code, "PROVIDER_UNAVAILABLE")
        self.assertNotIn("private upstream detail", context.exception.message)
        self.assertTrue(context.exception.retryable)


if __name__ == "__main__":
    unittest.main()
