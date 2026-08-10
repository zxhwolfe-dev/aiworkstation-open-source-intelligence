from __future__ import annotations

import io
import unittest
import urllib.error
from typing import Any, Callable, Mapping
from unittest.mock import patch

from aiworkstation_osi.errors import ProviderUnavailableError, UpstreamContractError
from aiworkstation_osi.http_provider import (
    AIWorkstationHttpProvider,
    JsonResponse,
    UrllibJsonTransport,
)
from aiworkstation_osi.tools import ToolRegistry


class RouterTransport:
    def __init__(
        self,
        handler: Callable[[str, str, Mapping[str, Any], Mapping[str, Any]], tuple[int, Mapping[str, Any]]],
    ) -> None:
        self.handler = handler
        self.calls: list[tuple[str, str, dict[str, Any], dict[str, Any]]] = []

    def request(
        self,
        method: str,
        path: str,
        *,
        query: Mapping[str, Any] | None = None,
        body: Mapping[str, Any] | None = None,
        timeout: float = 30.0,
    ) -> JsonResponse:
        query_dict = dict(query or {})
        body_dict = dict(body or {})
        self.calls.append((method, path, query_dict, body_dict))
        status, payload = self.handler(method, path, query_dict, body_dict)
        return JsonResponse(
            status=status,
            headers={"date": "Thu, 06 Aug 2026 14:00:00 GMT"},
            payload=dict(payload),
            url="https://example.test" + path,
            observed_at="2026-08-06T14:00:00Z",
        )


def project_card(project_id: str, route_id: str) -> dict[str, Any]:
    owner, repo = project_id.split("/", 1)
    return {
        "id": route_id,
        "owner": owner,
        "repo": repo,
        "full_name": project_id,
        "name": repo,
    }


def project_detail(project_id: str, *, license_name: str = "Apache-2.0") -> dict[str, Any]:
    owner, repo = project_id.split("/", 1)
    return {
        "full_name": project_id,
        "owner": owner,
        "repo": repo,
        "name": repo,
        "summary": f"Public summary for {repo}",
        "license": license_name,
        "deployment": ["self-hosted", "docker"],
        "languages": ["Python"],
        "stars": 123,
        "updated_at": "2026-08-05T00:00:00Z",
        "categories": ["rag"],
        "use_cases": ["knowledge-base"],
        "archived": False,
        "interpretation": {
            "coverage_level": "EN_L2",
            "transparency": {"source_count": 3},
        },
    }


class HttpProviderTests(unittest.TestCase):
    def test_plain_http_is_rejected_for_non_localhost(self) -> None:
        with self.assertRaises(ValueError):
            UrllibJsonTransport("http://example.com")
        UrllibJsonTransport("http://127.0.0.1:9010")

    def test_transport_classifies_html_5xx_as_provider_unavailable(self) -> None:
        transport = UrllibJsonTransport("https://example.test")
        failure = urllib.error.HTTPError(
            "https://example.test/api/v1/ai/githubai/selector",
            504,
            "Gateway Timeout",
            {"Content-Type": "text/html"},
            io.BytesIO(b"<html><body>gateway timeout</body></html>"),
        )
        with patch("urllib.request.urlopen", side_effect=failure):
            with self.assertRaises(ProviderUnavailableError):
                transport.request("POST", "/api/v1/ai/githubai/selector", body={"query": "RAG"})

    def test_transport_keeps_success_invalid_json_as_contract_error(self) -> None:
        class FakeResponse:
            status = 200
            headers: Mapping[str, str] = {"Content-Type": "application/json"}

            def read(self, _limit: int) -> bytes:
                return b"not-json"

        transport = UrllibJsonTransport("https://example.test")
        with patch("urllib.request.urlopen", return_value=FakeResponse()):
            with self.assertRaises(UpstreamContractError):
                transport.request("GET", "/api/v1/ai/githubai/projects")

    def test_project_facts_are_promoted_only_with_snapshot_and_public_detail(self) -> None:
        def handler(method: str, path: str, query: Mapping[str, Any], body: Mapping[str, Any]):
            if path.endswith("/projects"):
                return 200, {
                    "snapshot_id": "snapshot-1",
                    "items": [project_card("infiniflow/ragflow", "ragflow")],
                }
            if path.endswith("/projects/ragflow"):
                return 200, {
                    "snapshot_id": "snapshot-1",
                    "item": project_detail("infiniflow/ragflow"),
                }
            raise AssertionError((method, path, query, body))

        provider = AIWorkstationHttpProvider(
            "https://example.test",
            transport=RouterTransport(handler),
        )
        result = ToolRegistry(provider).invoke(
            "get_project_facts",
            {"project_id": "infiniflow/ragflow", "locale": "en"},
        )

        self.assertEqual(result.data["snapshot_id"], "snapshot-1")
        self.assertEqual(result.data["project"]["license"], "Apache-2.0")
        by_field = {fact.field: fact for fact in result.verified_facts}
        self.assertEqual(by_field["license"].confidence, "high")
        self.assertEqual(by_field["license"].evidence[0].source_type, "aiworkstation_public_release")
        self.assertFalse(result.recommendations)

    def test_search_uses_selector_and_hydrates_current_project_details(self) -> None:
        def handler(method: str, path: str, query: Mapping[str, Any], body: Mapping[str, Any]):
            if path.endswith("/selector"):
                self.assertEqual(body["use_model"], False)
                self.assertIn("required", body["query"])
                self.assertEqual(body["filters"], {"deployment": "docker"})
                return 200, {
                    "evidence_status": "available",
                    "result_kind": "projects",
                    "items": [project_card("infiniflow/ragflow", "ragflow")],
                }
            if path.endswith("/projects"):
                return 200, {
                    "snapshot_id": "snapshot-1",
                    "items": [project_card("infiniflow/ragflow", "ragflow")],
                }
            if path.endswith("/projects/ragflow"):
                return 200, {
                    "snapshot_id": "snapshot-1",
                    "item": project_detail("infiniflow/ragflow"),
                }
            raise AssertionError((method, path, query, body))

        provider = AIWorkstationHttpProvider(
            "https://example.test",
            transport=RouterTransport(handler),
        )
        result = ToolRegistry(provider).invoke(
            "search_ai_projects",
            {
                "query": "Find a private RAG service",
                "constraints": [{"id": "docker", "value": True, "polarity": "required"}],
                "locale": "en",
            },
        )

        self.assertEqual(result.data["total"], 1)
        self.assertEqual(result.data["projects"][0]["project_id"], "infiniflow/ragflow")
        self.assertTrue(any(fact.field.endswith(".license") for fact in result.verified_facts))
        self.assertFalse(any(risk.code == "MOCK_DATA" for risk in result.risks))

    def test_structured_required_constraints_use_filters_and_aliases(self) -> None:
        seen: dict[str, Any] = {}
        def handler(method: str, path: str, query: Mapping[str, Any], body: Mapping[str, Any]):
            if path.endswith("/selector"):
                seen.update(body)
                return 200, {"evidence_status": "available", "items": [], "no_match_reason": "No match."}
            raise AssertionError((method, path, query, body))
        provider = AIWorkstationHttpProvider("https://example.test", transport=RouterTransport(handler))
        provider.search_projects({
            "query": "RAG",
            "constraints": [
                {"id": "self_hosted", "value": True, "polarity": "required"}, {"id": "web_ui", "value": True, "polarity": "required"},
                {"id": "docker", "value": True, "polarity": "preferred"}, {"id": "no_code", "value": True, "polarity": "preferred"},
            ],
            "locale": "en",
        })
        self.assertEqual(seen["filters"], {"deployment": "local"})
        self.assertIn("local", seen["query"])
        self.assertIn("web UI", seen["query"])
        self.assertNotIn("Docker", seen["query"])

    def test_multiple_required_constraints_are_order_independent(self) -> None:
        bodies: list[dict[str, Any]] = []
        def handler(method: str, path: str, query: Mapping[str, Any], body: Mapping[str, Any]):
            if path.endswith("/selector"):
                bodies.append(dict(body))
                return 200, {"evidence_status": "available", "items": [], "no_match_reason": "No exact match."}
            raise AssertionError((method, path, query, body))
        provider = AIWorkstationHttpProvider("https://example.test", transport=RouterTransport(handler))
        first = [{"id": x, "value": True, "polarity": "required"} for x in ("self_hosted", "docker", "web_ui")] + [{"id": "no_code", "value": True, "polarity": "preferred"}]
        second = list(reversed(first))
        provider.search_projects({"query": "RAG", "constraints": first, "locale": "en"})
        provider.search_projects({"query": "RAG", "constraints": second, "locale": "en"})
        self.assertEqual(len(bodies), 2)
        for body in bodies:
            self.assertEqual(body["filters"], {"deployment": "docker"})
            query = body["query"].lower()
            self.assertIn("self-hosted/local", query)
            self.assertIn("docker", query)
            self.assertIn("web ui", query)
            self.assertNotIn("no-code", query)
        self.assertEqual(
            bodies[0]["query"].lower().split("\n", 1)[1],
            bodies[1]["query"].lower().split("\n", 1)[1],
        )

    def test_unsupported_required_constraint_fails_explicitly(self) -> None:
        provider = AIWorkstationHttpProvider("https://example.test", transport=RouterTransport(lambda *args: (200, {})))
        with self.assertRaises(UpstreamContractError) as raised:
            provider.search_projects({"query": "RAG", "constraints": [{"id": "cloud_only", "value": True, "polarity": "required"}], "locale": "en"})
        self.assertIn("cloud_only", raised.exception.details["unsupported_constraints"])

    def test_partial_selector_requires_public_notice(self) -> None:
        def handler(method: str, path: str, query: Mapping[str, Any], body: Mapping[str, Any]):
            return 200, {"evidence_status": "partial", "items": []}

        provider = AIWorkstationHttpProvider(
            "https://example.test",
            transport=RouterTransport(handler),
        )
        with self.assertRaises(UpstreamContractError):
            provider.search_projects({"query": "RAG", "constraints": {}, "locale": "en"})

    def test_project_detail_without_snapshot_fails_closed(self) -> None:
        def handler(method: str, path: str, query: Mapping[str, Any], body: Mapping[str, Any]):
            if path.endswith("/projects"):
                return 200, {"items": [project_card("infiniflow/ragflow", "ragflow")]}
            raise AssertionError((method, path, query, body))

        provider = AIWorkstationHttpProvider(
            "https://example.test",
            transport=RouterTransport(handler),
        )
        with self.assertRaises(UpstreamContractError):
            provider.get_project_facts({"project_id": "infiniflow/ragflow", "locale": "en"})

    def test_comparison_rejects_mixed_public_snapshots(self) -> None:
        snapshots = {
            "langgenius/dify": "snapshot-1",
            "infiniflow/ragflow": "snapshot-2",
        }
        routes = {
            "langgenius/dify": "dify",
            "infiniflow/ragflow": "ragflow",
        }

        def handler(method: str, path: str, query: Mapping[str, Any], body: Mapping[str, Any]):
            if path.endswith("/projects"):
                project_id = str(query["q"])
                return 200, {
                    "snapshot_id": snapshots[project_id],
                    "items": [project_card(project_id, routes[project_id])],
                }
            for project_id, route_id in routes.items():
                if path.endswith("/projects/" + route_id):
                    return 200, {
                        "snapshot_id": snapshots[project_id],
                        "item": project_detail(project_id),
                    }
            raise AssertionError((method, path, query, body))

        provider = AIWorkstationHttpProvider(
            "https://example.test",
            transport=RouterTransport(handler),
        )
        with self.assertRaises(UpstreamContractError):
            provider.compare_projects(
                {
                    "project_ids": ["langgenius/dify", "infiniflow/ragflow"],
                    "criteria": ["license"],
                    "locale": "en",
                }
            )


if __name__ == "__main__":
    unittest.main()
