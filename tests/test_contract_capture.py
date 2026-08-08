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


def selector_result(body: Mapping[str, Any] | None) -> dict[str, Any]:
    request_body = dict(body or {})
    return {
        "evidence_status": "available",
        "query": request_body.get("query") or "",
        "client_id": request_body.get("client_id") or "",
        "items": [],
        "no_match_reason": "No exact match."
        if request_body.get("filters", {}).get("category") == "__osi_contract_no_match_v1__"
        else "",
        "claim_refs": ["internal"],
    }


class FixtureTransport:
    def __init__(self) -> None:
        self._task_results: dict[str, dict[str, Any]] = {}
        self._task_counter = 0

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
        status = 200
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
        elif method_upper == "POST" and path.endswith("/selector/tasks"):
            self._task_counter += 1
            task_id = f"fixture-task-{self._task_counter}"
            self._task_results[task_id] = selector_result(body)
            status = 202
            payload = {"ok": True, "task_id": task_id, "status": "queued"}
        elif method_upper == "GET" and "/selector/tasks/" in path:
            task_id = path.rsplit("/", 1)[-1]
            if task_id not in self._task_results:
                status = 404
                payload = {}
            else:
                payload = {
                    "task_id": task_id,
                    "status": "completed",
                    "error": "",
                    "result": self._task_results[task_id],
                }
        elif method_upper == "DELETE" and "/selector/tasks/" in path:
            status = 202
            payload = {"ok": True, "status": "cancelling"}
        else:
            raise AssertionError((method, path, query, body, timeout))
        return JsonResponse(
            status=status,
            headers={
                "content-type": "application/json",
                "etag": '"fixture"',
                "authorization": "should-not-be-saved",
            },
            payload=payload,
            url="https://example.test" + path,
            observed_at="2026-08-06T14:00:00Z",
        )


class EncodedRouteTransport:
    def __init__(self) -> None:
        self.paths: list[str] = []
        self.task_result: dict[str, Any] = {}

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
        self.paths.append(path)
        status = 200
        if path.endswith("/projects"):
            payload: dict[str, Any] = {
                "snapshot_id": "snapshot-1",
                "items": [
                    {
                        "owner": "owner",
                        "repo": "repo",
                        "full_name": "owner/repo",
                    }
                ],
            }
        elif path.endswith("/projects/owner%2Frepo"):
            payload = {
                "snapshot_id": "snapshot-1",
                "item": {"owner": "owner", "repo": "repo", "full_name": "owner/repo"},
            }
        elif method_upper == "POST" and path.endswith("/selector/tasks"):
            self.task_result = {
                "evidence_status": "available",
                "items": [],
                "no_match_reason": "No exact match.",
            }
            status = 202
            payload = {"task_id": "encoded-task", "status": "queued"}
        elif method_upper == "GET" and path.endswith("/selector/tasks/encoded-task"):
            payload = {
                "task_id": "encoded-task",
                "status": "completed",
                "result": self.task_result,
            }
        elif method_upper == "DELETE" and path.endswith("/selector/tasks/encoded-task"):
            status = 202
            payload = {"ok": True, "status": "cancelling"}
        else:
            raise AssertionError((method, path, query, body, timeout))
        return JsonResponse(
            status=status,
            headers={"content-type": "application/json"},
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
    def test_no_match_capture_sends_structured_filter(self) -> None:
        class RecordingTransport(FixtureTransport):
            def __init__(self) -> None:
                super().__init__()
                self.no_match_body: dict[str, Any] | None = None

            def request(self, method: str, path: str, *, query=None, body=None, timeout=30.0):
                if method.upper() == "POST" and path.endswith("/selector/tasks") and body and body.get("filters"):
                    self.no_match_body = dict(body)
                return super().request(method, path, query=query, body=body, timeout=timeout)

        transport = RecordingTransport()
        with tempfile.TemporaryDirectory() as temp_dir:
            capture_public_contracts(
                transport=transport,
                output_dir=Path(temp_dir),
                locale="en",
                project_id="infiniflow/ragflow",
                formal_query="Find a project.",
                no_match_query="Find an open-source AI project.",
            )
        self.assertIsNotNone(transport.no_match_body)
        self.assertEqual(transport.no_match_body["filters"], {"category": "__osi_contract_no_match_v1__"})

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
            self.assertNotEqual(formal["request_fingerprint"], json.loads((output_dir / "selector-no-match.json").read_text(encoding="utf-8"))["request_fingerprint"])

    def test_full_name_route_is_url_encoded(self) -> None:
        transport = EncodedRouteTransport()
        with tempfile.TemporaryDirectory() as temp_dir:
            capture_public_contracts(
                transport=transport,
                output_dir=Path(temp_dir),
                locale="en",
                project_id="owner/repo",
                formal_query="Find a project.",
                no_match_query="Find an impossible project.",
            )
        self.assertIn("/api/v1/ai/githubai/projects/owner%2Frepo", transport.paths)
        self.assertNotIn("/api/v1/ai/githubai/projects/owner/repo", transport.paths)
        self.assertIn("/api/v1/ai/githubai/selector/tasks", transport.paths)
        self.assertNotIn("/api/v1/ai/githubai/selector", transport.paths)

    def test_capture_rejects_invalid_timeout_and_empty_inputs(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            output_dir = Path(temp_dir)
            with self.assertRaises(ValueError):
                capture_public_contracts(
                    transport=FixtureTransport(),
                    output_dir=output_dir,
                    locale="en",
                    project_id="infiniflow/ragflow",
                    formal_query="Find a project.",
                    no_match_query="Find an impossible project.",
                    timeout=0,
                )
            with self.assertRaises(ValueError):
                capture_public_contracts(
                    transport=FixtureTransport(),
                    output_dir=output_dir,
                    locale="en",
                    project_id="",
                    formal_query="Find a project.",
                    no_match_query="Find an impossible project.",
                )


if __name__ == "__main__":
    unittest.main()
