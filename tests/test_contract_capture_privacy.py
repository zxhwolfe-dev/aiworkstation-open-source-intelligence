from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path
from typing import Any, Mapping

from aiworkstation_osi.contract_capture import (
    REDACTED_QUERY_TEXT,
    REMOVED_KEYS,
    SELECTOR_REMOVED_KEYS,
    capture_public_contracts,
    sanitize_public_value,
)
from aiworkstation_osi.http_provider import JsonResponse


class EchoingSelectorTransport:
    def __init__(self) -> None:
        self._task_results: dict[str, dict[str, Any]] = {}
        self._task_counter = 0

    @staticmethod
    def _selector_result(body: Mapping[str, Any] | None) -> dict[str, Any]:
        request_text = str((body or {}).get("query") or "")
        no_match = bool((body or {}).get("filters"))
        return {
            "snapshot_id": "snapshot-1",
            "evidence_status": "available",
            "items": [],
            "no_match_reason": "No match." if no_match else "",
            "requirement_token": "opaque-but-query-bearing-token",
            "requirement_spec": {
                "goal": request_text,
                "search_queries": {"en": [request_text]},
            },
            "query_analysis": {
                "goal": request_text,
                "search_queries": {"en": [f"paraphrase of {request_text}"]},
            },
            "understanding": f"Paraphrased request about {request_text}",
            "notice": f"Safe retained result can still exactly echo {request_text}",
        }

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
                "items": [{
                    "id": "ragflow",
                    "owner": "infiniflow",
                    "repo": "ragflow",
                    "full_name": "infiniflow/ragflow",
                }],
            }
        elif path.endswith("/projects/ragflow"):
            payload = {
                "snapshot_id": "snapshot-1",
                "item": {
                    "id": "ragflow",
                    "owner": "infiniflow",
                    "repo": "ragflow",
                    "full_name": "infiniflow/ragflow",
                },
            }
        elif method_upper == "POST" and path.endswith("/selector/tasks"):
            self._task_counter += 1
            task_id = f"privacy-task-{self._task_counter}"
            self._task_results[task_id] = self._selector_result(body)
            status = 202
            payload = {"ok": True, "task_id": task_id, "status": "queued"}
        elif method_upper == "GET" and "/selector/tasks/" in path:
            task_id = path.rsplit("/", 1)[-1]
            result = self._task_results.get(task_id)
            if result is None:
                status = 404
                payload = {}
            else:
                payload = {
                    "task_id": task_id,
                    "status": "completed",
                    "error": "",
                    "result": result,
                }
        elif method_upper == "DELETE" and "/selector/tasks/" in path:
            status = 202
            payload = {"ok": True, "status": "cancelling"}
        else:
            raise AssertionError((method, path, query, body, timeout))
        return JsonResponse(
            status=status,
            headers={"content-type": "application/json"},
            payload=payload,
            url="https://example.test" + path,
            observed_at="2026-08-07T00:00:00Z",
        )


class ContractCapturePrivacyTests(unittest.TestCase):
    def test_sanitizer_redacts_exact_query_case_insensitively(self) -> None:
        private_query = "Private Project Need"
        sanitized = sanitize_public_value(
            {
                "goal": private_query,
                "notice": f"You asked for {private_query.lower()} today",
            },
            redact_texts=(private_query,),
        )
        rendered = json.dumps(sanitized, ensure_ascii=False)
        self.assertNotIn(private_query, rendered)
        self.assertNotIn(private_query.lower(), rendered.lower())
        self.assertIn(REDACTED_QUERY_TEXT, rendered)

    def test_capture_removes_selector_query_metadata_and_exact_echoes(self) -> None:
        formal_query = "PRIVATE FORMAL QUERY 7b93"
        no_match_query = "PRIVATE NO MATCH QUERY 82ac"
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            manifest = capture_public_contracts(
                transport=EchoingSelectorTransport(),
                output_dir=root,
                locale="en",
                project_id="infiniflow/ragflow",
                formal_query=formal_query,
                no_match_query=no_match_query,
            )

            for filename, private_text in (
                ("selector-formal.json", formal_query),
                ("selector-no-match.json", no_match_query),
            ):
                rendered = (root / filename).read_text(encoding="utf-8")
                payload = json.loads(rendered)["payload"]
                self.assertNotIn(private_text, rendered)
                for forbidden in (
                    "requirement_token",
                    "requirement_spec",
                    "query_analysis",
                    "understanding",
                ):
                    self.assertNotIn(forbidden, payload)
                # Retained public output is still protected from an exact echo.
                self.assertEqual(payload["notice"], f"Safe retained result can still exactly echo {REDACTED_QUERY_TEXT}")

            self.assertIn("requirement_token", REMOVED_KEYS)
            for key in ("understanding", "query_analysis", "requirement_spec"):
                self.assertIn(key, SELECTOR_REMOVED_KEYS)
            self.assertFalse(manifest["sanitization"]["stores_query_text"])
            self.assertEqual(
                manifest["sanitization"]["query_text_redaction"],
                "selector_metadata_removed_plus_exact_echo_redaction",
            )
            self.assertEqual(
                set(manifest["sanitization"]["selector_removed_keys"]),
                set(SELECTOR_REMOVED_KEYS),
            )


if __name__ == "__main__":
    unittest.main()
