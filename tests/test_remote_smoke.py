from __future__ import annotations

import unittest
from types import SimpleNamespace

from aiworkstation_osi.hosted_remote_evidence import HOSTED_PREMIUM_TOOL
from aiworkstation_osi.remote_smoke import (
    _expected_tool_names,
    _tool_annotations_ok,
    _validate_endpoint,
)


class RemoteSmokeEndpointTests(unittest.TestCase):
    def test_https_remote_endpoint_is_allowed(self) -> None:
        self.assertEqual(
            _validate_endpoint(
                "https://mcp.example.com/mcp",
                allow_http_localhost=True,
            ),
            "https://mcp.example.com/mcp",
        )

    def test_localhost_http_is_allowed_for_development(self) -> None:
        for url in (
            "http://localhost:8000/mcp",
            "http://127.0.0.1:8000/mcp",
            "http://[::1]:8000/mcp",
        ):
            with self.subTest(url=url):
                self.assertEqual(_validate_endpoint(url, allow_http_localhost=True), url)

    def test_remote_plain_http_is_rejected(self) -> None:
        with self.assertRaises(ValueError):
            _validate_endpoint("http://mcp.example.com/mcp", allow_http_localhost=True)

    def test_canonical_mcp_path_is_required(self) -> None:
        for url in (
            "https://mcp.example.com",
            "https://mcp.example.com/",
            "https://mcp.example.com/api/mcp",
            "https://mcp.example.com/sse",
        ):
            with self.subTest(url=url), self.assertRaises(ValueError):
                _validate_endpoint(url, allow_http_localhost=True)

    def test_credentials_query_fragment_invalid_port_and_non_http_schemes_are_rejected(self) -> None:
        for url in (
            "https://user:pass@mcp.example.com/mcp",
            "https://mcp.example.com/mcp?token=secret",
            "https://mcp.example.com/mcp#fragment",
            "https://mcp.example.com:99999/mcp",
            "file:///tmp/mcp",
        ):
            with self.subTest(url=url), self.assertRaises(ValueError):
                _validate_endpoint(url, allow_http_localhost=True)

    def test_public_hosted_profile_is_exactly_the_standard_nine_tools(self) -> None:
        standard = _expected_tool_names("standard")
        public_hosted = _expected_tool_names("hosted-public")
        self.assertEqual(public_hosted, standard)
        self.assertNotIn(HOSTED_PREMIUM_TOOL, public_hosted)

    def test_oauth_hosted_profiles_expect_standard_tools_plus_premium(self) -> None:
        standard = _expected_tool_names("standard")
        for profile in ("hosted", "hosted-oauth"):
            with self.subTest(profile=profile):
                hosted = _expected_tool_names(profile)
                self.assertEqual(len(hosted), len(standard) + 1)
                self.assertEqual(hosted[-1], HOSTED_PREMIUM_TOOL)

    def test_premium_annotation_contract_is_only_valid_for_oauth_hosted(self) -> None:
        premium = SimpleNamespace(
            name=HOSTED_PREMIUM_TOOL,
            annotations=SimpleNamespace(
                read_only_hint=False,
                destructive_hint=False,
                idempotent_hint=False,
                open_world_hint=True,
            ),
        )
        standard = SimpleNamespace(
            name="search_ai_projects",
            annotations=SimpleNamespace(
                read_only_hint=True,
                destructive_hint=False,
                idempotent_hint=True,
                open_world_hint=True,
            ),
        )
        self.assertTrue(_tool_annotations_ok(premium, "hosted"))
        self.assertTrue(_tool_annotations_ok(premium, "hosted-oauth"))
        self.assertTrue(_tool_annotations_ok(standard, "hosted-public"))
        self.assertFalse(_tool_annotations_ok(premium, "hosted-public"))
        self.assertFalse(_tool_annotations_ok(premium, "standard"))


if __name__ == "__main__":
    unittest.main()
