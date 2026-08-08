from __future__ import annotations

import unittest
from typing import Any, Mapping

from aiworkstation_osi.full_radar_provider import FullRadarHttpProvider
from aiworkstation_osi.http_provider import JsonResponse
from aiworkstation_osi.tools import ToolRegistry


class RecordingTransport:
    def __init__(self) -> None:
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
        method_upper = method.upper()
        query_dict = dict(query or {})
        body_dict = dict(body or {})
        self.calls.append((method_upper, path, query_dict, body_dict))
        status = 200
        if method_upper == "POST" and path.endswith("/selector/tasks"):
            self.assert_selector_body(body_dict)
            status = 202
            payload: dict[str, Any] = {"task_id": "task123", "status": "queued"}
        elif method_upper == "GET" and path.endswith("/selector/tasks/task123"):
            payload = {
                "task_id": "task123",
                "status": "completed",
                "result": {
                    "evidence_status": "available",
                    "result_kind": "project_list",
                    "items": [
                        {
                            "id": "ragflow",
                            "owner": "infiniflow",
                            "repo": "ragflow",
                            "full_name": "infiniflow/ragflow",
                        }
                    ],
                    "near_matches": [],
                },
            }
        elif method_upper == "GET" and path.endswith("/projects"):
            payload = {
                "snapshot_id": "snapshot-1",
                "items": [
                    {
                        "id": "ragflow",
                        "owner": "infiniflow",
                        "repo": "ragflow",
                        "full_name": "infiniflow/ragflow",
                    }
                ],
            }
        elif method_upper == "GET" and path.endswith("/projects/ragflow"):
            payload = {
                "snapshot_id": "snapshot-1",
                "item": {
                    "id": "ragflow",
                    "owner": "infiniflow",
                    "repo": "ragflow",
                    "full_name": "infiniflow/ragflow",
                    "name": "RAGFlow",
                    "stars": 100,
                    "updated_at": "2026-08-08T00:00:00Z",
                    "archived": False,
                    "interpretation": {
                        "coverage_level": "EN_L2",
                        "transparency": {},
                    },
                },
            }
        else:
            raise AssertionError((method, path, query_dict, body_dict, timeout))
        return JsonResponse(
            status=status,
            headers={"content-type": "application/json"},
            payload=payload,
            url="https://example.test" + path,
            observed_at="2026-08-09T00:00:00Z",
        )

    @staticmethod
    def assert_selector_body(body: Mapping[str, Any]) -> None:
        if body.get("use_model") is not False:
            raise AssertionError("selector must keep publisher model disabled")
        if not str(body.get("query") or "").strip():
            raise AssertionError("selector query is required")


class FullRadarSelectorTaskTests(unittest.TestCase):
    def test_search_uses_task_api_and_hides_ephemeral_task_id(self) -> None:
        transport = RecordingTransport()
        provider = FullRadarHttpProvider(
            "https://example.test",
            transport=transport,
            timeout=30,
            hydrate_limit=3,
        )
        result = ToolRegistry(provider).invoke(
            "search_ai_projects",
            {"query": "Find RAG", "constraints": {}, "locale": "en"},
        )

        paths = [path for _method, path, _query, _body in transport.calls]
        self.assertIn("/api/v1/ai/githubai/selector/tasks", paths)
        self.assertIn("/api/v1/ai/githubai/selector/tasks/task123", paths)
        self.assertNotIn("/api/v1/ai/githubai/selector", paths)
        self.assertEqual(result.data["total"], 1)
        self.assertEqual(result.data["projects"][0]["project_id"], "infiniflow/ragflow")
        self.assertEqual(
            result.data["selector_url"],
            "https://example.test/api/v1/ai/githubai/selector/tasks",
        )
        self.assertNotIn("task123", result.data["selector_url"])


if __name__ == "__main__":
    unittest.main()
