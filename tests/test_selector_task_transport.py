from __future__ import annotations

import unittest
from typing import Any, Mapping

from aiworkstation_osi.errors import ProviderUnavailableError, UpstreamContractError
from aiworkstation_osi.errors import ProviderOverloadedError
from aiworkstation_osi.http_provider import JsonResponse, PUBLIC_API_PREFIX
from aiworkstation_osi.selector_task_transport import SelectorTaskJsonTransport


class FakeTransport:
    def __init__(self, handler) -> None:
        self.handler = handler
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
                "method": method.upper(),
                "path": path,
                "query": dict(query or {}),
                "body": dict(body or {}),
                "timeout": timeout,
            }
        )
        status, payload = self.handler(method.upper(), path, dict(query or {}), dict(body or {}))
        return JsonResponse(
            status=status,
            headers={"content-type": "application/json"},
            payload=dict(payload),
            url="https://example.test" + path,
            observed_at="2026-08-09T00:00:00Z",
        )


class SelectorTaskTransportTests(unittest.TestCase):
    def test_selector_call_creates_polls_and_returns_completed_result(self) -> None:
        polls = 0
        result = {
            "evidence_status": "available",
            "result_kind": "project_list",
            "items": [],
            "no_match_reason": "No match.",
        }

        def handler(method: str, path: str, query: dict[str, Any], body: dict[str, Any]):
            nonlocal polls
            if method == "POST" and path.endswith("/selector/tasks"):
                self.assertEqual(body["use_model"], False)
                return 202, {"task_id": "abc123", "status": "queued"}
            if method == "GET" and path.endswith("/selector/tasks/abc123"):
                polls += 1
                if polls == 1:
                    return 200, {"task_id": "abc123", "status": "running"}
                return 200, {"task_id": "abc123", "status": "completed", "result": result}
            raise AssertionError((method, path, query, body))

        delegate = FakeTransport(handler)
        transport = SelectorTaskJsonTransport(delegate, poll_interval=0)
        response = transport.request(
            "POST",
            f"{PUBLIC_API_PREFIX}/selector",
            body={"query": "RAG", "use_model": False},
            timeout=30,
        )

        self.assertEqual(response.payload, result)
        self.assertEqual(response.status, 200)
        self.assertEqual(response.url, f"https://example.test{PUBLIC_API_PREFIX}/selector/tasks")
        self.assertNotIn("abc123", response.url)
        self.assertEqual([call["method"] for call in delegate.calls], ["POST", "GET", "GET"])
        self.assertLessEqual(max(call["timeout"] for call in delegate.calls), 10.0)

    def test_non_selector_requests_are_delegated_unchanged(self) -> None:
        def handler(method: str, path: str, query: dict[str, Any], body: dict[str, Any]):
            return 200, {"ok": True}

        delegate = FakeTransport(handler)
        transport = SelectorTaskJsonTransport(delegate)
        response = transport.request(
            "GET",
            f"{PUBLIC_API_PREFIX}/overview",
            query={"lang": "en"},
            timeout=17,
        )
        self.assertEqual(response.payload, {"ok": True})
        self.assertEqual(delegate.calls[0]["timeout"], 17)
        self.assertEqual(delegate.calls[0]["query"], {"lang": "en"})

    def test_terminal_failure_states_fail_as_provider_unavailable(self) -> None:
        for state in ("failed", "cancelled", "interrupted"):
            with self.subTest(state=state):
                def handler(method: str, path: str, _query: dict[str, Any], _body: dict[str, Any]):
                    if method == "POST":
                        return 202, {"task_id": "task1", "status": "queued"}
                    return 200, {"task_id": "task1", "status": state, "error": "private"}

                transport = SelectorTaskJsonTransport(FakeTransport(handler), poll_interval=0)
                with self.assertRaises(ProviderUnavailableError) as raised:
                    transport.request(
                        "POST",
                        f"{PUBLIC_API_PREFIX}/selector",
                        body={"query": "RAG"},
                    )
                self.assertNotIn("private", str(raised.exception))
                self.assertNotIn("task1", str(raised.exception))

    def test_bad_task_identity_and_unknown_status_fail_contract(self) -> None:
        for task_id in ("", "../secret", "bad/task"):
            with self.subTest(task_id=task_id):
                delegate = FakeTransport(
                    lambda *_args: (202, {"task_id": task_id, "status": "queued"})
                )
                transport = SelectorTaskJsonTransport(delegate, poll_interval=0)
                with self.assertRaises(UpstreamContractError):
                    transport.request(
                        "POST",
                        f"{PUBLIC_API_PREFIX}/selector",
                        body={"query": "RAG"},
                    )

        def unknown_handler(method: str, _path: str, _query: dict[str, Any], _body: dict[str, Any]):
            if method == "POST":
                return 202, {"task_id": "task1", "status": "queued"}
            return 200, {"task_id": "task1", "status": "mystery"}

        with self.assertRaises(UpstreamContractError):
            SelectorTaskJsonTransport(FakeTransport(unknown_handler), poll_interval=0).request(
                "POST",
                f"{PUBLIC_API_PREFIX}/selector",
                body={"query": "RAG"},
            )

    def test_task_timeout_attempts_cancellation_without_exposing_task_id(self) -> None:
        now = [0.0]

        def clock() -> float:
            return now[0]

        def sleeper(seconds: float) -> None:
            now[0] += seconds

        def handler(method: str, path: str, _query: dict[str, Any], _body: dict[str, Any]):
            if method == "POST":
                return 202, {"task_id": "task-timeout", "status": "queued"}
            if method == "GET":
                return 200, {"task_id": "task-timeout", "status": "running"}
            if method == "DELETE":
                return 202, {"ok": True, "status": "cancelling"}
            raise AssertionError((method, path))

        delegate = FakeTransport(handler)
        transport = SelectorTaskJsonTransport(
            delegate,
            task_timeout=2,
            poll_interval=1,
            clock=clock,
            sleeper=sleeper,
        )
        with self.assertRaises(ProviderUnavailableError) as raised:
            transport.request(
                "POST",
                f"{PUBLIC_API_PREFIX}/selector",
                body={"query": "RAG"},
                timeout=30,
            )
        self.assertTrue(any(call["method"] == "DELETE" for call in delegate.calls))
        self.assertNotIn("task-timeout", str(raised.exception))

    def test_completed_task_requires_result_object(self) -> None:
        def handler(method: str, _path: str, _query: dict[str, Any], _body: dict[str, Any]):
            if method == "POST":
                return 202, {"task_id": "task1", "status": "queued"}
            return 200, {"task_id": "task1", "status": "completed", "result": None}

        with self.assertRaises(UpstreamContractError):
            SelectorTaskJsonTransport(FakeTransport(handler), poll_interval=0).request(
                "POST",
                f"{PUBLIC_API_PREFIX}/selector",
                body={"query": "RAG"},
            )

    def test_capacity_exhaustion_is_retryable_overload(self) -> None:
        transport = SelectorTaskJsonTransport(
            FakeTransport(lambda *_args: (200, {})),
            max_concurrent=1,
            queue_timeout=0,
        )
        self.assertTrue(transport._capacity.acquire(blocking=False))
        try:
            with self.assertRaises(ProviderOverloadedError) as raised:
                transport.request(
                    "POST",
                    f"{PUBLIC_API_PREFIX}/selector",
                    body={"query": "RAG"},
                )
            self.assertTrue(raised.exception.retryable)
            self.assertEqual(raised.exception.details["retry_after_seconds"], 1)
        finally:
            transport._capacity.release()


if __name__ == "__main__":
    unittest.main()
