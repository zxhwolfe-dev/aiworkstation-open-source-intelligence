from __future__ import annotations

import urllib.error
import unittest
from io import BytesIO
from typing import Any, Callable, Mapping
from unittest.mock import patch

from aiworkstation_osi.errors import ProviderUnavailableError, UpstreamContractError
from aiworkstation_osi.http_provider import JsonResponse
from aiworkstation_osi.strict_http_provider import (
    AIWorkstationHttpProvider,
    SafeUrllibJsonTransport,
)


class RouterTransport:
    def __init__(
        self,
        handler: Callable[[str, str, Mapping[str, Any], Mapping[str, Any]], tuple[int, Mapping[str, Any]]],
    ) -> None:
        self.handler = handler

    def request(
        self,
        method: str,
        path: str,
        *,
        query: Mapping[str, Any] | None = None,
        body: Mapping[str, Any] | None = None,
        timeout: float = 30.0,
    ) -> JsonResponse:
        status, payload = self.handler(method, path, dict(query or {}), dict(body or {}))
        return JsonResponse(
            status=status,
            headers={},
            payload=dict(payload),
            url="https://example.test" + path,
            observed_at="2026-08-06T14:00:00Z",
        )


def project_card() -> dict[str, Any]:
    return {
        "id": "sample",
        "owner": "owner",
        "repo": "sample",
        "full_name": "owner/sample",
    }


def project_detail(license_name: Any) -> dict[str, Any]:
    return {
        "owner": "owner",
        "repo": "sample",
        "full_name": "owner/sample",
        "name": "Sample",
        "license": license_name,
        "deployment": ["docker"],
        "updated_at": "2026-08-05T00:00:00Z",
        "archived": False,
        "interpretation": {
            "coverage_level": "EN_L2",
            "transparency": {"source_count": 2},
        },
    }


def detail_handler(license_name: Any):
    def handler(method: str, path: str, query: Mapping[str, Any], body: Mapping[str, Any]):
        if path.endswith("/projects"):
            return 200, {"snapshot_id": "snapshot-1", "items": [project_card()]}
        if path.endswith("/projects/sample"):
            return 200, {
                "snapshot_id": "snapshot-1",
                "item": project_detail(license_name),
            }
        raise AssertionError((method, path, query, body))

    return handler


class StrictHttpProviderTests(unittest.TestCase):
    def test_unknown_license_sentinel_is_not_promoted_to_verified_fact(self) -> None:
        provider = AIWorkstationHttpProvider(
            "https://example.test",
            transport=RouterTransport(detail_handler("NOASSERTION")),
        )
        output = provider.get_license_evidence({"project_id": "owner/sample", "locale": "en"})

        self.assertIsNone(output.data["license"])
        self.assertFalse(output.verified_facts)
        self.assertTrue(any("License evidence" in value for value in output.unknowns))
        self.assertIn("LICENSE_UNVERIFIED", {risk.code for risk in output.risks})

    def test_mapping_license_is_normalized_and_non_standard_label_is_flagged(self) -> None:
        provider = AIWorkstationHttpProvider(
            "https://example.test",
            transport=RouterTransport(detail_handler({"spdx_id": "OTHER", "name": "Custom terms"})),
        )
        output = provider.get_license_evidence({"project_id": "owner/sample", "locale": "en"})

        self.assertEqual(output.data["license"], "OTHER")
        self.assertEqual(output.verified_facts[0].value, "OTHER")
        self.assertIn("NON_STANDARD_LICENSE", {risk.code for risk in output.risks})

    def test_retryable_http_status_is_provider_unavailable(self) -> None:
        provider = AIWorkstationHttpProvider(
            "https://example.test",
            transport=RouterTransport(lambda *_args: (429, {"detail": "rate limited"})),
        )
        with self.assertRaises(ProviderUnavailableError) as context:
            provider.get_project_facts({"project_id": "owner/sample", "locale": "en"})
        self.assertTrue(context.exception.retryable)

    def test_near_match_cannot_coexist_with_formal_recommendation(self) -> None:
        same_project = project_card()

        def handler(method: str, path: str, query: Mapping[str, Any], body: Mapping[str, Any]):
            if path.endswith("/selector"):
                return 200, {
                    "evidence_status": "available",
                    "items": [same_project],
                    "near_matches": [
                        {
                            "status": "near_match",
                            "project": same_project,
                            "blocking_constraints": [
                                {"id": "license", "status": "unverified"}
                            ],
                        }
                    ],
                }
            raise AssertionError((method, path, query, body))

        provider = AIWorkstationHttpProvider(
            "https://example.test",
            transport=RouterTransport(handler),
        )
        with self.assertRaises(UpstreamContractError):
            provider.search_projects({"query": "RAG", "constraints": {}, "locale": "en"})

    def test_selector_internal_publication_fields_fail_closed(self) -> None:
        def handler(method: str, path: str, query: Mapping[str, Any], body: Mapping[str, Any]):
            if path.endswith("/selector"):
                return 200, {
                    "evidence_status": "available",
                    "items": [],
                    "no_match_reason": "No exact match.",
                    "source_hash": "must-not-leak",
                }
            raise AssertionError((method, path, query, body))

        provider = AIWorkstationHttpProvider(
            "https://example.test",
            transport=RouterTransport(handler),
        )
        with self.assertRaises(UpstreamContractError) as context:
            provider.search_projects({"query": "RAG", "constraints": {}, "locale": "en"})
        self.assertIn("source_hash", context.exception.details["fields"])

    def test_alternative_source_alias_is_resolved_before_exclusion(self) -> None:
        alternative_card = {
            "id": "alternative",
            "owner": "owner",
            "repo": "alternative",
            "full_name": "owner/alternative",
        }
        alternative_detail = {
            **project_detail("Apache-2.0"),
            "repo": "alternative",
            "full_name": "owner/alternative",
            "name": "Alternative",
        }

        def handler(method: str, path: str, query: Mapping[str, Any], body: Mapping[str, Any]):
            if path.endswith("/selector"):
                return 200, {
                    "evidence_status": "available",
                    "items": [project_card(), alternative_card],
                }
            if path.endswith("/projects"):
                requested = str(query.get("q") or "")
                if requested in {"sample", "owner/sample"}:
                    return 200, {"snapshot_id": "snapshot-1", "items": [project_card()]}
                if requested == "owner/alternative":
                    return 200, {"snapshot_id": "snapshot-1", "items": [alternative_card]}
            if path.endswith("/projects/sample"):
                return 200, {"snapshot_id": "snapshot-1", "item": project_detail("MIT")}
            if path.endswith("/projects/alternative"):
                return 200, {"snapshot_id": "snapshot-1", "item": alternative_detail}
            raise AssertionError((method, path, query, body))

        provider = AIWorkstationHttpProvider(
            "https://example.test",
            transport=RouterTransport(handler),
        )
        output = provider.find_alternatives(
            {"project_id": "sample", "constraints": {}, "locale": "en"}
        )

        self.assertEqual(output.data["source_project_id"], "owner/sample")
        self.assertEqual(output.data["total"], 1)
        self.assertEqual(output.data["alternatives"][0]["project_id"], "owner/alternative")
        self.assertFalse(
            any(fact.field.startswith("projects.owner/sample.") for fact in output.verified_facts)
        )

    def test_hydration_limit_is_not_silently_clamped(self) -> None:
        with self.assertRaises(ValueError):
            AIWorkstationHttpProvider("https://example.test", hydrate_limit=0)
        with self.assertRaises(ValueError):
            AIWorkstationHttpProvider("https://example.test", hydrate_limit=6)

    def test_html_404_is_normalized_to_empty_not_found_payload(self) -> None:
        error = urllib.error.HTTPError(
            "https://example.test/missing",
            404,
            "Not Found",
            None,
            BytesIO(b"<html>not found</html>"),
        )
        transport = SafeUrllibJsonTransport("https://example.test")
        with patch("aiworkstation_osi.strict_http_provider.urllib.request.urlopen", side_effect=error):
            response = transport.request("GET", "/missing")
        self.assertEqual(response.status, 404)
        self.assertEqual(response.payload, {})


if __name__ == "__main__":
    unittest.main()
