from __future__ import annotations

import io
import json
import tempfile
import unittest
import urllib.error
from email.message import Message
from pathlib import Path

from aiworkstation_osi.hosted_remote_evidence import (
    HOSTED_PREMIUM_TOOL,
    HOSTED_REMOTE_SCHEMA,
    expected_hosted_tools,
    inspect_oauth_boundary,
    validate_hosted_remote_evidence,
)


class _JsonResponse:
    def __init__(self, payload: dict, *, status: int = 200) -> None:
        self.status = status
        self.headers = Message()
        self._raw = json.dumps(payload).encode("utf-8")

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False

    def read(self, limit: int = -1) -> bytes:
        return self._raw if limit < 0 else self._raw[:limit]


class _BoundaryOpener:
    def __init__(self, *, metadata_url: str) -> None:
        self.metadata_url = metadata_url
        self.calls = 0

    def open(self, request, timeout=0):  # type: ignore[no-untyped-def]
        self.calls += 1
        if self.calls == 1:
            headers = Message()
            headers["WWW-Authenticate"] = (
                'Bearer resource_metadata="' + self.metadata_url + '"'
            )
            raise urllib.error.HTTPError(
                request.full_url,
                401,
                "Unauthorized",
                headers,
                io.BytesIO(b'{"error":"unauthorized"}'),
            )
        return _JsonResponse(
            {
                "resource": "https://mcp.aiworkstation.cn/mcp",
                "authorization_servers": ["https://auth.example.com"],
                "bearer_methods_supported": ["header"],
            }
        )


class HostedRemoteEvidenceTests(unittest.TestCase):
    def _write_report(self, path: Path, **overrides) -> Path:
        tools = list(expected_hosted_tools())
        payload = {
            "schema_version": HOSTED_REMOTE_SCHEMA,
            "ok": True,
            "commit": "candidate-sha",
            "profile": "hosted",
            "endpoint": "https://mcp.aiworkstation.cn/mcp",
            "protocol_version": "2026-07-28",
            "auth": {"mode": "oauth"},
            "oauth_boundary": {
                "ok": True,
                "challenge_status": 401,
                "resource": "https://mcp.aiworkstation.cn/mcp",
                "authorization_servers": ["https://auth.example.com"],
            },
            "tools": tools,
            "checks": [
                {"id": "tool-set", "ok": True},
                {"id": "tool-annotations", "ok": True},
                {"id": "search-invocation", "ok": True},
            ],
            "search": {
                "is_error": False,
                "tool": "search_ai_projects",
                "schema_version": "osi.tool-result.v1",
            },
        }
        payload.update(overrides)
        path.write_text(json.dumps(payload), encoding="utf-8")
        return path

    def test_oauth_boundary_accepts_same_origin_protected_resource_metadata(self) -> None:
        opener = _BoundaryOpener(
            metadata_url="https://mcp.aiworkstation.cn/.well-known/oauth-protected-resource/mcp"
        )
        result = inspect_oauth_boundary(
            "https://mcp.aiworkstation.cn/mcp",
            expected_issuer="https://auth.example.com",
            opener=opener,
        )

        self.assertTrue(result["ok"])
        self.assertEqual(result["challenge_status"], 401)
        self.assertTrue(result["bearer_challenge"])
        self.assertEqual(result["metadata_status"], 200)
        self.assertEqual(result["resource"], "https://mcp.aiworkstation.cn/mcp")
        self.assertEqual(result["authorization_servers"], ["https://auth.example.com"])
        self.assertEqual(opener.calls, 2)

    def test_oauth_boundary_rejects_cross_origin_metadata_url(self) -> None:
        opener = _BoundaryOpener(
            metadata_url="https://evil.example/.well-known/oauth-protected-resource"
        )
        result = inspect_oauth_boundary(
            "https://mcp.aiworkstation.cn/mcp",
            expected_issuer="https://auth.example.com",
            opener=opener,
        )

        self.assertFalse(result["ok"])
        self.assertIn("same MCP origin", " ".join(result["errors"]))
        self.assertEqual(opener.calls, 1)

    def test_valid_report_is_candidate_and_oauth_bound(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            report = self._write_report(Path(temp_dir) / "hosted.json")
            result = validate_hosted_remote_evidence(
                report,
                candidate_commit="candidate-sha",
                expected_endpoint="https://mcp.aiworkstation.cn/mcp",
                expected_issuer="https://auth.example.com",
            )

        self.assertTrue(result["ok"])
        self.assertTrue(result["oauth_boundary_verified"])
        self.assertTrue(result["search_verified"])
        self.assertIn(HOSTED_PREMIUM_TOOL, result["tools"])
        self.assertEqual(result["errors"], [])

    def test_different_candidate_fails_closed(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            report = self._write_report(Path(temp_dir) / "hosted.json")
            result = validate_hosted_remote_evidence(
                report,
                candidate_commit="newer-sha",
                expected_endpoint="https://mcp.aiworkstation.cn/mcp",
                expected_issuer="https://auth.example.com",
            )

        self.assertFalse(result["ok"])
        self.assertIn("different candidate commit", " ".join(result["errors"]))

    def test_missing_premium_or_authentication_cannot_pass(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "hosted.json"
            report = self._write_report(
                path,
                tools=list(expected_hosted_tools())[:-1],
                auth={"mode": "none"},
            )
            result = validate_hosted_remote_evidence(
                report,
                candidate_commit="candidate-sha",
                expected_endpoint="https://mcp.aiworkstation.cn/mcp",
                expected_issuer="https://auth.example.com",
            )

        self.assertFalse(result["ok"])
        rendered = " ".join(result["errors"])
        self.assertIn("authenticated MCP access", rendered)
        self.assertIn("nine standard tools plus Premium", rendered)

    def test_wrong_issuer_or_failed_search_cannot_pass(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "hosted.json"
            report = self._write_report(
                path,
                oauth_boundary={
                    "ok": True,
                    "challenge_status": 401,
                    "resource": "https://mcp.aiworkstation.cn/mcp",
                    "authorization_servers": ["https://wrong.example.com"],
                },
                checks=[
                    {"id": "tool-set", "ok": True},
                    {"id": "tool-annotations", "ok": True},
                    {"id": "search-invocation", "ok": False},
                ],
                search={"is_error": True, "tool": "search_ai_projects"},
            )
            result = validate_hosted_remote_evidence(
                report,
                candidate_commit="candidate-sha",
                expected_endpoint="https://mcp.aiworkstation.cn/mcp",
                expected_issuer="https://auth.example.com",
            )

        self.assertFalse(result["ok"])
        rendered = " ".join(result["errors"])
        self.assertIn("expected issuer", rendered)
        self.assertIn("search-invocation", rendered)


if __name__ == "__main__":
    unittest.main()
