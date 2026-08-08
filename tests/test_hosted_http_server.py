from __future__ import annotations

import io
import json
import unittest
from contextlib import redirect_stdout
from types import SimpleNamespace
from unittest.mock import patch

from aiworkstation_osi.hosted_http_server import _validate_hosted_configuration, main


class HostedHttpServerTests(unittest.TestCase):
    def _safe_http(self):
        return SimpleNamespace(
            host="0.0.0.0",
            port=8000,
            allowed_hosts=("mcp.example.com", "mcp.example.com:*"),
            allowed_origins=("https://chatgpt.com",),
            cors_enabled=True,
            request_body_limit=262144,
        )

    def _oauth(self, resource_url: str = "https://mcp.example.com/mcp"):
        return SimpleNamespace(
            issuer_url="https://auth.example.com",
            resource_url=resource_url,
        )

    def _backend(self):
        return SimpleNamespace(base_url="https://aiworkstation.cn")

    def test_hosted_mode_requires_live_http_provider_before_other_configuration(self) -> None:
        with patch.dict("os.environ", {"OSI_PROVIDER": "mock"}, clear=True), self.assertRaises(ValueError) as context:
            _validate_hosted_configuration()
        self.assertIn("OSI_PROVIDER=http", str(context.exception))

    def test_hosted_mode_fails_closed_when_public_bind_policy_fails(self) -> None:
        with patch.dict("os.environ", {"OSI_PROVIDER": "http"}, clear=True), patch(
            "aiworkstation_osi.hosted_http_server.validate_http_configuration",
            side_effect=ValueError("public bind acknowledgement is missing"),
        ), self.assertRaises(ValueError) as context:
            _validate_hosted_configuration()
        self.assertIn("acknowledgement", str(context.exception))

    def test_hosted_mode_requires_valid_oauth_and_backend_configuration(self) -> None:
        with patch.dict("os.environ", {"OSI_PROVIDER": "http"}, clear=True), patch(
            "aiworkstation_osi.hosted_http_server.validate_http_configuration",
            return_value=self._safe_http(),
        ), patch(
            "aiworkstation_osi.hosted_http_server.load_hosted_oauth_config",
            side_effect=ValueError("OAuth client secret is missing"),
        ), self.assertRaises(ValueError) as context:
            _validate_hosted_configuration()
        self.assertIn("OAuth", str(context.exception))

        with patch.dict("os.environ", {"OSI_PROVIDER": "http"}, clear=True), patch(
            "aiworkstation_osi.hosted_http_server.validate_http_configuration",
            return_value=self._safe_http(),
        ), patch(
            "aiworkstation_osi.hosted_http_server.load_hosted_oauth_config",
            return_value=self._oauth(),
        ), patch(
            "aiworkstation_osi.hosted_http_server.load_hosted_backend_config",
            side_effect=ValueError("backend service token is missing"),
        ), self.assertRaises(ValueError) as context:
            _validate_hosted_configuration()
        self.assertIn("backend", str(context.exception).lower())

    def test_oauth_resource_must_be_public_https_mcp_endpoint(self) -> None:
        with patch.dict("os.environ", {"OSI_PROVIDER": "http"}, clear=True), patch(
            "aiworkstation_osi.hosted_http_server.validate_http_configuration",
            return_value=self._safe_http(),
        ), patch(
            "aiworkstation_osi.hosted_http_server.load_hosted_oauth_config",
            return_value=self._oauth("https://mcp.example.com/not-mcp"),
        ), patch(
            "aiworkstation_osi.hosted_http_server.load_hosted_backend_config",
            return_value=self._backend(),
        ), patch(
            "aiworkstation_osi.hosted_http_server.validate_mcp_endpoint",
            return_value="https://mcp.example.com/not-mcp",
        ), self.assertRaises(ValueError) as context:
            _validate_hosted_configuration()
        self.assertIn("/mcp", str(context.exception))

    def test_check_config_reports_only_public_configuration(self) -> None:
        config = self._safe_http()
        buffer = io.StringIO()
        with patch(
            "aiworkstation_osi.hosted_http_server._validate_hosted_configuration",
            return_value=(
                config,
                "https://auth.example.com",
                "https://mcp.example.com/mcp",
                "https://aiworkstation.cn",
            ),
        ), redirect_stdout(buffer):
            rc = main(["--check-config"])
        self.assertEqual(rc, 0)
        payload = json.loads(buffer.getvalue())
        self.assertEqual(payload["mode"], "hosted-oauth")
        self.assertEqual(payload["oauth_resource"], "https://mcp.example.com/mcp")
        self.assertEqual(payload["backend_origin"], "https://aiworkstation.cn")
        rendered = buffer.getvalue().lower()
        self.assertNotIn("secret", rendered)
        self.assertNotIn("token", rendered)


if __name__ == "__main__":
    unittest.main()
