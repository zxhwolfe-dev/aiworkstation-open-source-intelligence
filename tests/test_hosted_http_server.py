from __future__ import annotations

import io
import json
import unittest
from contextlib import redirect_stdout
from types import SimpleNamespace
from unittest.mock import Mock, patch

from aiworkstation_osi.hosted_http_server import _validate_hosted_configuration, main


class HostedHttpServerTests(unittest.TestCase):
    def _safe_http(self):
        security = SimpleNamespace(
            allowed_hosts=["mcp.example.com", "mcp.example.com:*"],
            allowed_origins=["https://chatgpt.com"],
        )
        return SimpleNamespace(
            host="0.0.0.0",
            port=8000,
            provider="http",
            radar_base_url="https://aiworkstation.cn",
            public_bind=True,
            allowed_hosts=("mcp.example.com", "mcp.example.com:*"),
            allowed_origins=("https://chatgpt.com",),
            max_request_body_size=262144,
            stateless_http=True,
            json_response=True,
            transport_security=lambda: security,
        )

    def _oauth(self, resource_url: str = "https://mcp.example.com/mcp"):
        return SimpleNamespace(
            issuer_url="https://auth.example.com",
            resource_url=resource_url,
        )

    def _backend(self):
        return SimpleNamespace(base_url="https://aiworkstation.cn")

    def _limits(self):
        return SimpleNamespace(
            per_minute=60,
            per_hour=300,
            premium_per_minute=5,
            max_subjects=10000,
        )

    def test_hosted_mode_requires_live_http_provider_before_other_configuration(self) -> None:
        with patch.dict("os.environ", {"OSI_PROVIDER": "mock"}, clear=True), self.assertRaises(ValueError) as context:
            _validate_hosted_configuration()
        self.assertIn("OSI_PROVIDER=http", str(context.exception))

    def test_hosted_mode_fails_closed_when_public_bind_policy_fails(self) -> None:
        with patch.dict("os.environ", {"OSI_PROVIDER": "http"}, clear=True), patch(
            "aiworkstation_osi.hosted_http_server.load_http_server_settings",
            side_effect=ValueError("public bind acknowledgement is missing"),
        ), self.assertRaises(ValueError) as context:
            _validate_hosted_configuration()
        self.assertIn("acknowledgement", str(context.exception))

    def test_hosted_mode_requires_valid_oauth_and_backend_configuration(self) -> None:
        with patch.dict("os.environ", {"OSI_PROVIDER": "http"}, clear=True), patch(
            "aiworkstation_osi.hosted_http_server.load_http_server_settings",
            return_value=self._safe_http(),
        ), patch(
            "aiworkstation_osi.hosted_http_server.load_hosted_oauth_config",
            side_effect=ValueError("OAuth client secret is missing"),
        ), self.assertRaises(ValueError) as context:
            _validate_hosted_configuration()
        self.assertIn("OAuth", str(context.exception))

        with patch.dict("os.environ", {"OSI_PROVIDER": "http"}, clear=True), patch(
            "aiworkstation_osi.hosted_http_server.load_http_server_settings",
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

    def test_hosted_mode_rejects_invalid_rate_limit_configuration_before_startup(self) -> None:
        with patch.dict("os.environ", {"OSI_PROVIDER": "http"}, clear=True), patch(
            "aiworkstation_osi.hosted_http_server.load_http_server_settings",
            return_value=self._safe_http(),
        ), patch(
            "aiworkstation_osi.hosted_http_server.load_hosted_oauth_config",
            return_value=self._oauth(),
        ), patch(
            "aiworkstation_osi.hosted_http_server.load_hosted_backend_config",
            return_value=self._backend(),
        ), patch(
            "aiworkstation_osi.hosted_http_server.load_hosted_rate_limit_config",
            side_effect=ValueError("rate limit invalid"),
        ), self.assertRaises(ValueError) as context:
            _validate_hosted_configuration()
        self.assertIn("rate limit", str(context.exception).lower())

    def test_oauth_resource_must_be_public_https_mcp_endpoint(self) -> None:
        with patch.dict("os.environ", {"OSI_PROVIDER": "http"}, clear=True), patch(
            "aiworkstation_osi.hosted_http_server.load_http_server_settings",
            return_value=self._safe_http(),
        ), patch(
            "aiworkstation_osi.hosted_http_server.load_hosted_oauth_config",
            return_value=self._oauth("https://mcp.example.com/not-mcp"),
        ), patch(
            "aiworkstation_osi.hosted_http_server.load_hosted_backend_config",
            return_value=self._backend(),
        ), patch(
            "aiworkstation_osi.hosted_http_server.load_hosted_rate_limit_config",
            return_value=self._limits(),
        ), patch(
            "aiworkstation_osi.hosted_http_server.validate_mcp_endpoint",
            return_value="https://mcp.example.com/not-mcp",
        ), self.assertRaises(ValueError) as context:
            _validate_hosted_configuration()
        self.assertIn("/mcp", str(context.exception))

    def test_check_config_reports_only_public_configuration(self) -> None:
        config = self._safe_http()
        buffer = io.StringIO()
        limits = {
            "per_minute": 60,
            "per_hour": 300,
            "premium_per_minute": 5,
            "max_subjects": 10000,
        }
        with patch(
            "aiworkstation_osi.hosted_http_server._validate_hosted_configuration",
            return_value=(
                config,
                "https://auth.example.com",
                "https://mcp.example.com/mcp",
                "https://aiworkstation.cn",
                limits,
            ),
        ), redirect_stdout(buffer):
            rc = main(["--check-config"])
        self.assertEqual(rc, 0)
        payload = json.loads(buffer.getvalue())
        self.assertEqual(payload["mode"], "hosted-oauth")
        self.assertEqual(payload["oauth_resource"], "https://mcp.example.com/mcp")
        self.assertEqual(payload["backend_origin"], "https://aiworkstation.cn")
        self.assertEqual(payload["rate_limits"], limits)
        self.assertEqual(payload["request_body_limit"], 262144)
        self.assertIs(payload["cors_enabled"], True)
        rendered = buffer.getvalue().lower()
        self.assertNotIn("secret", rendered)
        self.assertNotIn("token", rendered)

    def test_runtime_uses_current_http_settings_contract(self) -> None:
        config = self._safe_http()
        fake_server = Mock()
        with patch(
            "aiworkstation_osi.hosted_http_server._validate_hosted_configuration",
            return_value=(
                config,
                "https://auth.example.com",
                "https://mcp.example.com/mcp",
                "https://aiworkstation.cn",
                {
                    "per_minute": 60,
                    "per_hour": 300,
                    "premium_per_minute": 5,
                    "max_subjects": 10000,
                },
            ),
        ), patch(
            "aiworkstation_osi.hosted_http_server.build_hosted_mcp_server",
            return_value=fake_server,
        ), redirect_stdout(io.StringIO()):
            rc = main([])

        self.assertEqual(rc, 0)
        call = fake_server.run.call_args
        self.assertIsNotNone(call)
        assert call is not None
        self.assertEqual(call.kwargs["transport"], "streamable-http")
        self.assertEqual(call.kwargs["host"], "0.0.0.0")
        self.assertEqual(call.kwargs["port"], 8000)
        self.assertEqual(call.kwargs["max_request_body_size"], 262144)
        self.assertTrue(call.kwargs["stateless_http"])
        self.assertTrue(call.kwargs["json_response"])
        self.assertEqual(
            call.kwargs["transport_security"].allowed_hosts,
            ["mcp.example.com", "mcp.example.com:*"],
        )


if __name__ == "__main__":
    unittest.main()
