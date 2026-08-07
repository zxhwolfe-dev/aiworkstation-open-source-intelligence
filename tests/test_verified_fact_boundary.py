from __future__ import annotations

import unittest
from typing import Any, Mapping

from aiworkstation_osi.http_provider import JsonResponse
from aiworkstation_osi.strict_http_provider import AIWorkstationHttpProvider


class FactBoundaryTransport:
    def request(
        self,
        method: str,
        path: str,
        *,
        query: Mapping[str, Any] | None = None,
        body: Mapping[str, Any] | None = None,
        timeout: float = 30.0,
    ) -> JsonResponse:
        if path.endswith("/projects"):
            payload: dict[str, Any] = {
                "snapshot_id": "snapshot-boundary",
                "items": [
                    {
                        "id": "sample",
                        "owner": "owner",
                        "repo": "sample",
                        "full_name": "owner/sample",
                    }
                ],
            }
        elif path.endswith("/projects/sample"):
            payload = {
                "snapshot_id": "snapshot-boundary",
                "item": {
                    "owner": "owner",
                    "repo": "sample",
                    "full_name": "owner/sample",
                    "name": "Sample",
                    "summary": "Editorial summary from the public projection.",
                    "html_url": "https://github.com/owner/sample",
                    "homepage": "https://sample.example",
                    "license": "Apache-2.0",
                    "deployment": ["docker", "self-hosted"],
                    "languages": ["Python"],
                    "stars": 1234,
                    "updated_at": "2026-08-05T00:00:00Z",
                    "categories": ["RAG"],
                    "use_cases": ["knowledge-base"],
                    "archived": False,
                    "interpretation": {
                        "coverage_level": "EN_L2",
                        "transparency": {
                            "source_updated_at": "2026-08-05T09:30:00Z",
                            "sources": [
                                {
                                    "source_label": "README",
                                    "source_path": "README.md",
                                    "section_heading": "Deployment",
                                    "excerpt": "Run with Docker.",
                                },
                                {
                                    "source_label": "License",
                                    "source_path": "LICENSE",
                                    "section_heading": "License",
                                    "excerpt": "Licensed under Apache-2.0.",
                                },
                            ],
                        },
                    },
                },
            }
        else:
            raise AssertionError((method, path, query, body, timeout))
        return JsonResponse(
            status=200,
            headers={},
            payload=payload,
            url="https://example.test" + path,
            observed_at="2026-08-06T14:00:00Z",
        )


class VerifiedFactBoundaryTests(unittest.TestCase):
    def setUp(self) -> None:
        self.provider = AIWorkstationHttpProvider(
            "https://example.test",
            transport=FactBoundaryTransport(),
        )

    def test_repository_metadata_and_direct_license_are_verified(self) -> None:
        output = self.provider.get_project_facts(
            {"project_id": "owner/sample", "locale": "en"}
        )
        fields = {fact.field for fact in output.verified_facts}

        self.assertTrue(
            {
                "project_id",
                "name",
                "repository_url",
                "homepage",
                "languages",
                "stars",
                "updated_at",
                "archived",
                "license",
            }.issubset(fields)
        )
        self.assertEqual(
            output.data["field_evidence_status"]["license"],
            "verified_direct_evidence",
        )
        self.assertEqual(
            output.data["field_evidence_status"]["updated_at"],
            "verified_public_metadata",
        )

    def test_analysis_projection_fields_are_not_promoted_to_verified_facts(self) -> None:
        output = self.provider.get_project_facts(
            {"project_id": "owner/sample", "locale": "en"}
        )
        fields = {fact.field for fact in output.verified_facts}

        for field in ("summary", "deployment", "categories", "use_cases"):
            with self.subTest(field=field):
                self.assertIn(field, output.data["project"])
                self.assertNotIn(field, fields)
                self.assertEqual(
                    output.data["field_evidence_status"][field],
                    "public_projection_only",
                )

    def test_search_hydration_inherits_the_same_fact_boundary(self) -> None:
        class SearchTransport(FactBoundaryTransport):
            def request(self, method, path, *, query=None, body=None, timeout=30.0):
                if path.endswith("/selector"):
                    return JsonResponse(
                        status=200,
                        headers={},
                        payload={
                            "evidence_status": "available",
                            "items": [
                                {
                                    "owner": "owner",
                                    "repo": "sample",
                                    "full_name": "owner/sample",
                                }
                            ],
                        },
                        url="https://example.test" + path,
                        observed_at="2026-08-06T14:00:00Z",
                    )
                return super().request(method, path, query=query, body=body, timeout=timeout)

        provider = AIWorkstationHttpProvider(
            "https://example.test",
            transport=SearchTransport(),
        )
        output = provider.search_projects(
            {"query": "RAG", "constraints": {}, "locale": "en"}
        )
        fields = {fact.field for fact in output.verified_facts}

        self.assertIn("projects.owner/sample.updated_at", fields)
        self.assertIn("projects.owner/sample.license", fields)
        self.assertNotIn("projects.owner/sample.deployment", fields)
        self.assertNotIn("projects.owner/sample.categories", fields)


if __name__ == "__main__":
    unittest.main()
