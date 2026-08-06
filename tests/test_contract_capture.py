from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path
from typing import Any, Mapping

from aiworkstation_osi.contract_capture import (
    MAX_STRING_LENGTH,
    REMOVED_KEYS,
    capture_public_contracts,
    sanitize_public_value,
)
from aiworkstation_osi.http_provider import JsonResponse


class FixtureTransport:
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
                "snapshot_id": "snapshot-1",
                "query": "must not be recorded",
                "source_hash": "internal",
                "items": [
                    {
                        "id": "ragflow",
                        "owner": "infiniflow",
                        "repo": "ragflow",
                        "full_name": "infiniflow/ragflow",
                    }
                ],
            }
        elif path.endswith("/projects/ragflow"):
            payload = {
                "snapshot_id": "snapshot-1",
                "item": {
                    "full_name": "infiniflow/ragflow",
                    "summary": "x" * (MAX_STRING_LENGTH + 25),
                    "license": "Apache-2.0",
                    "publication_version": "internal",
                    "interpretation": {
                        "transparency": {
                            "source_count": 2,
                            "evidence_ids": ["private-id"],
                        }
                    },
                },
            }
        elif path.endswith("/selector"):
            payload = {
                "evidence_status": "available",
                "query": body.get("query") if body else "",
                "client_id": body.get("client_id") if body else "",
                "items": [],
                "no_match_reason": "No exact match." if "cloud-only" in str(body) else "",
                "claim_refs": ["internal"],
            }
        else:
            raise AssertionError((method, path, query, body, timeout))
        return JsonResponse(
            status=200,
            headers={
                "content-type": "application/json",
                "etag": '"fixture"',
                "authorization": "should-not-be-saved",
            },
            payload=payload,
            url="https://example.test" + path,
            observed_at="2026-08-06T14:00:00Z",
        )


def collect_keys(value: Any) -> set[str]:
    if isinstance(value, dict):
        keys = {str(key).lower() for key in value}
        for child in value.values():
            keys.update(collect_keys(child))
        return keys
    if isinstance(value, list):
        keys: set[str] = set()
        for child in value:
            keys.update(collect_keys(child))
        return keys
    return set()


class ContractCaptureTests(unittest.TestCase):
    def test_sanitizer_removes_internal_fields_and_bounds_content(self) -> None:
        value = {
            "query": "private query",
            "nested": {
                "source_hash": "internal",
                "safe": "a" * (MAX_STRING_LENGTH + 10),
            },
            "rows": list(range(30)),
        }
        sanitized = sanitize_public_value(value)
        keys = collect_keys(sanitized)
        self.assertFalse(keys.intersection(REMOVED_KEYS))
        self.assertIn("<truncated", sanitized["nested"]["safe"])
        self.assertLessEqual(len(sanitized["rows"]), 21)

    def test_capture_writes_four_fixtures_and_manifest_without_queries(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            output_dir = Path(temp_dir)
            manifest = capture_public_contracts(
                transport=FixtureTransport(),
                output_dir=output_dir,
                locale="en",
                project_id="infiniflow/ragflow",
                formal_query="Find a self-hosted RAG project.",
                no_match_query="Find a cloud-only and fully offline project.",
            )

            self.assertEqual(manifest["schema_version"], "osi.public-contract-capture.v1")
            self.assertEqual(len(manifest["fixture_files"]), 4)
            self.assertTrue((output_dir / "manifest.json").exists())

            for filename in manifest["fixture_files"]:
                payload = json.loads((output_dir / filename).read_text(encoding="utf-8"))
                keys = collect_keys(payload)
                self.assertFalse(keys.intersection(REMOVED_KEYS), filename)
                rendered = json.dumps(payload, ensure_ascii=False)
                self.assertNotIn("Find a self-hosted RAG project", rendered)
                self.assertNotIn("client_id", rendered)
                self.assertNotIn("source_hash", rendered)
                self.assertEqual(payload["headers"], {"content-type": "application/json", "etag": '"fixture"'})

            detail = json.loads((output_dir / "project-detail.json").read_text(encoding="utf-8"))
            self.assertIn("<truncated", detail["payload"]["item"]["summary"])
            formal = json.loads((output_dir / "selector-formal.json").read_text(encoding="utf-8"))
            self.assertTrue(formal["request_fingerprint"].startswith("sha256:"))


if __name__ == "__main__":
    unittest.main()
