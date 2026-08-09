from __future__ import annotations

import io
import json
import unittest
from contextlib import redirect_stdout
from types import SimpleNamespace
from unittest.mock import Mock, patch

from aiworkstation_osi.hosted_http_server import _validate_hosted_configuration, main

RELEASE_COMMIT = "a" * 40


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

    def test_hosted_mode_requires_live_http_provider_before_other_configuration(self) -> None:
        with patch.dict("os.environ", {"OSI_PROVIDER": "mock"}, clear=True), self.assertRaises(ValueError) as context:
            _validate_hosted_configuration()
        self.assertIn("OSI_PROVIDER=http", str(context.exception))

    def test_public_mode_rejects_oauth_runtime_switch(self) -> None:
        with patch.dict(
            "os.environ",
            {"OSI_PROVIDER": "http", "OSI_HOSTED_ACCESS_MODE": "oauth"},
            clear=True,
        ), patch(
            "aiworkstation_osi.hosted_http_server.load_http_server_settings",
            return_value=self._safe_http(),
        ), self.assertRaises(ValueError) as context:
            _validate_hosted_configuration()
        self.assertIn("disabled", str(context.exception))

    def test_public_mode_never_loads_oauth_or_backend_configuration(self) -> None:
        with patch.dict(
            "os.environ",
            {
                "OSI_PROVIDER": "http",
                "OSI_HOSTED_ACCESS_MODE": "public",
                "OSI_RELEASE_COMMIT": RELEASE_COMMIT,
                "OSI_IMAGE_COMMIT": RELEASE_COMMIT,
            },
            clear=True,
        ), patch(
            "aiworkstation_osi.hosted_http_server.load_http_server_settings",
            return_value=self._safe_http(),
        ), patch(
            "aiworkstation_osi.hosted_http_server.validate_hosted_deployment_identity",
            return_value=RELEASE_COMMIT,
        ):
            config, access_mode, release_commit = _validate_hosted_configuration()
        self.assertEqual(config.port, 8000)
        self.assertEqual(access_mode, "public")
        self.assertEqual(release_commit, RELEASE_COMMIT)

    def test_check_config_reports_data_only_surface(self) -> None:
        config = self._safe_http()
        buffer = io.StringIO()
        with patch(
            "aiworkstation_osi.hosted_http_server._validate_hosted_configuration",
            return_value=(config, "public", RELEASE_COMMIT),
        ), redirect_stdout(buffer):
            rc = main(["--check-config"])
        self.assertEqual(rc, 0)
        payload = json.loads(buffer.getvalue())
        self.assertEqual(payload["mode"], "hosted-public")
        self.assertEqual(payload["access_mode"], "public")
        self.assertEqual(payload["tool_count"], 9)
        self.assertIs(payload["premium_enabled"], False)
        self.assertIs(payload["server_model_enabled"], False)
        self.assertIs(payload["oauth_enabled"], False)
        self.assertEqual(payload["release_commit"], RELEASE_COMMIT)
        self.assertEqual(payload["gateway_abuse_control"], "required-dual-ip-rate-limit")
        rendered = buffer.getvalue().lower()
        self.assertNotIn("client_secret", rendered)
        self.assertNotIn("backend_service_token", rendered)

    def test_runtime_uses_public_server_builder(self) -> None:
        config = self._safe_http()
        fake_server = Mock()
        with patch(
            "aiworkstation_osi.hosted_http_server._validate_hosted_configuration",
            return_value=(config, "public", RELEASE_COMMIT),
        ), patch(
            "aiworkstation_osi.hosted_http_server.build_public_hosted_mcp_server",
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


if __name__ == "__main__":
    unittest.main()
