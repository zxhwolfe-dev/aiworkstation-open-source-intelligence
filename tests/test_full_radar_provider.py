from __future__ import annotations

import unittest
from typing import Any, Mapping

from aiworkstation_osi.errors import UpstreamContractError
from aiworkstation_osi.full_radar_provider import FullRadarHttpProvider
from aiworkstation_osi.http_provider import JsonResponse


class RecordingTransport:
    def __init__(self, responses: list[JsonResponse]) -> None:
        self.responses = list(responses)
        self.calls: list[dict[str, Any]] = []

    def request(
        self,
        method: str,
        path: str,
        *,
        query: Mapping[str, Any] | None = None,
        body: Mapping[str, Any] | None = None,
        timeout: float = 30.0,
    ) -> JsonResponse:
        self.calls.append(
            {
                "method": method,
                "path": path,
                "query": dict(query or {}),
                "body": dict(body or {}) if body is not None else None,
                "timeout": timeout,
            }
        )
        if not self.responses:
            raise AssertionError("unexpected transport request")
        return self.responses.pop(0)


def response(path: str, payload: Mapping[str, Any], *, status: int = 200) -> JsonResponse:
    return JsonResponse(
        status=status,
        headers={"content-type": "application/json"},
        payload=dict(payload),
        url=f"https://aiworkstation.cn{path}",
        observed_at="2026-08-08T00:00:00Z",
    )


class FullRadarProviderTests(unittest.TestCase):
    def test_overview_returns_public_navigation_payload(self) -> None:
        transport = RecordingTransport(
            [
                response(
                    "/api/v1/ai/githubai/overview",
                    {
                        "ok": True,
                        "lang": "en",
                        "snapshot_id": "sha256:test",
                        "rankings": [{"id": "daily"}],
                        "collections": [{"id": "rag"}],
                        "categories": [{"id": "rag"}],
                        "scenarios": [{"id": "knowledge-base"}],
                    },
                )
            ]
        )
        provider = FullRadarHttpProvider(transport=transport)
        output = provider.get_radar_overview({"locale": "en"})

        self.assertEqual(output.data["snapshot_id"], "sha256:test")
        self.assertEqual(output.data["rankings"][0]["id"], "daily")
        self.assertEqual(transport.calls[0]["query"], {"lang": "en"})

    def test_project_browser_forwards_complete_public_filters_and_requires_snapshot(self) -> None:
        transport = RecordingTransport(
            [
                response(
                    "/api/v1/ai/githubai/projects",
                    {
                        "ok": True,
                        "snapshot_id": "sha256:test",
                        "items": [{"id": "infiniflow/ragflow", "name": "RAGFlow"}],
                        "total": 12,
                        "curated": True,
                        "eligible_total": 42,
                        "capacity": 20,
                        "ranking_policy_version": "ranking-v1",
                    },
                )
            ]
        )
        provider = FullRadarHttpProvider(transport=transport)
        output = provider.browse_radar_projects(
            {
                "locale": "en",
                "query": "RAG",
                "ranking": "monthly",
                "collection": "self-hosted-ai",
                "category": "rag",
                "scenario": "knowledge-base",
                "role": "developer",
                "topic": "agents",
                "github_topic": "rag",
                "radar_topic": "document-ai",
                "deployment": "docker",
                "limit": 10,
                "offset": 20,
            }
        )

        query = transport.calls[0]["query"]
        self.assertEqual(query["q"], "RAG")
        self.assertEqual(query["ranking"], "monthly")
        self.assertEqual(query["collection"], "self-hosted-ai")
        self.assertEqual(query["category"], "rag")
        self.assertEqual(query["scenario"], "knowledge-base")
        self.assertEqual(query["role"], "developer")
        self.assertEqual(query["topic"], "agents")
        self.assertEqual(query["github_topic"], "rag")
        self.assertEqual(query["radar_topic"], "document-ai")
        self.assertEqual(query["deployment"], "docker")
        self.assertEqual(query["limit"], 10)
        self.assertEqual(query["offset"], 20)
        self.assertEqual(output.data["total"], 12)
        self.assertTrue(output.data["has_more"])
        self.assertIs(output.data["curated"], True)
        self.assertEqual(output.data["eligible_total"], 42)
        self.assertEqual(output.data["capacity"], 20)

    def test_project_browser_rejects_missing_snapshot(self) -> None:
        provider = FullRadarHttpProvider(
            transport=RecordingTransport(
                [response("/api/v1/ai/githubai/projects", {"ok": True, "items": []})]
            )
        )
        with self.assertRaises(UpstreamContractError):
            provider.browse_radar_projects({"locale": "en", "limit": 20, "offset": 0})

    def test_skills_browser_forwards_complete_filters_and_pagination(self) -> None:
        transport = RecordingTransport(
            [
                response(
                    "/api/v1/ai/githubai/skills",
                    {
                        "ok": True,
                        "items": [{"id": "code-review", "name": "Code Review"}],
                        "total": 1,
                    },
                )
            ]
        )
        provider = FullRadarHttpProvider(transport=transport)
        output = provider.browse_radar_skills(
            {
                "locale": "en",
                "query": "review",
                "category": "coding",
                "kind": "agent-skill",
                "license": "MIT",
                "installable": True,
                "sort": "trend",
                "limit": 5,
                "offset": 0,
            }
        )

        self.assertEqual(
            transport.calls[0]["query"],
            {
                "lang": "en",
                "limit": 5,
                "offset": 0,
                "installable": True,
                "q": "review",
                "category": "coding",
                "kind": "agent-skill",
                "license": "MIT",
                "sort": "trend",
            },
        )
        self.assertEqual(output.data["items"][0]["id"], "code-review")
        self.assertIs(output.data["active_filters"]["installable"], True)

    def test_skills_browser_can_open_one_skill_detail(self) -> None:
        transport = RecordingTransport(
            [
                response(
                    "/api/v1/ai/githubai/skills/open-source-project-research",
                    {"ok": True, "item": {"id": "open-source-project-research", "name": "Research"}},
                )
            ]
        )
        provider = FullRadarHttpProvider(transport=transport)
        output = provider.browse_radar_skills(
            {"locale": "en", "skill_id": "open-source-project-research"}
        )
        self.assertEqual(
            transport.calls[0]["path"],
            "/api/v1/ai/githubai/skills/open-source-project-research",
        )
        self.assertEqual(transport.calls[0]["query"], {"lang": "en"})
        self.assertIs(output.data["found"], True)
        self.assertEqual(output.data["item"]["id"], "open-source-project-research")

    def test_missing_skill_detail_is_explicit_unknown(self) -> None:
        provider = FullRadarHttpProvider(
            transport=RecordingTransport(
                [response("/api/v1/ai/githubai/skills/missing", {}, status=404)]
            )
        )
        output = provider.browse_radar_skills({"locale": "en", "skill_id": "missing"})
        self.assertIs(output.data["found"], False)
        self.assertTrue(output.unknowns)

    def test_browse_surfaces_reject_internal_publication_fields(self) -> None:
        for path, method in (
            ("/api/v1/ai/githubai/overview", "get_radar_overview"),
            ("/api/v1/ai/githubai/projects", "browse_radar_projects"),
            ("/api/v1/ai/githubai/skills", "browse_radar_skills"),
        ):
            payload: dict[str, Any] = {
                "ok": True,
                "items": [],
                "snapshot_id": "sha256:test",
                "nested": {"source_hash": "private-internal-hash"},
            }
            provider = FullRadarHttpProvider(transport=RecordingTransport([response(path, payload)]))
            request = {"locale": "en", "limit": 20, "offset": 0}
            if method == "get_radar_overview":
                request = {"locale": "en"}
            with self.subTest(method=method), self.assertRaises(UpstreamContractError):
                getattr(provider, method)(request)


if __name__ == "__main__":
    unittest.main()
