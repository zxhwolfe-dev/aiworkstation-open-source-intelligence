from __future__ import annotations

import os
import unittest
from unittest.mock import Mock, patch

from aiworkstation_osi.http_server import (
    DEFAULT_MAX_REQUEST_BODY_BYTES,
    PUBLIC_BIND_ACK,
    load_http_server_settings,
    main,
)


class HttpServerSettingsTests(unittest.TestCase):
    def _settings(self, **values: str):
        environment = {
            "OSI_MCP_HTTP_HOST": "127.0.0.1",
            "OSI_MCP_HTTP_PORT": "8000",
            "OSI_PROVIDER": "mock",
            "AIWORKSTATION_RADAR_BASE_URL": "https://aiworkstation.cn",
        }
        environment.update(values)
        with patch.dict(os.environ, environment, clear=True):
            return load_http_server_settings()

    def test_default_bind_is_local_offline_and_stateless(self) -> None:
        settings = self._settings()
        self.assertEqual(settings.host, "127.0.0.1")
        self.assertEqual(settings.port, 8000)
        self.assertEqual(settings.provider, "mock")
        self.assertFalse(settings.public_bind)
        self.assertEqual(settings.allowed_hosts, ())
        self.assertEqual(settings.allowed_origins, ())
        self.assertEqual(settings.max_request_body_size, DEFAULT_MAX_REQUEST_BODY_BYTES)
        self.assertTrue(settings.stateless_http)
        self.assertTrue(settings.json_response)
        self.assertIsNone(settings.transport_security())

    def test_non_loopback_bind_requires_explicit_acknowledgement(self) -> None:
        with self.assertRaises(ValueError) as context:
            self._settings(
                OSI_MCP_HTTP_HOST="0.0.0.0",
                OSI_PROVIDER="http",
            )
        self.assertIn("PUBLIC_BIND_ACK", str(context.exception))

    def test_non_loopback_bind_rejects_mock_provider(self) -> None:
        with self.assertRaises(ValueError) as context:
            self._settings(
                OSI_MCP_HTTP_HOST="0.0.0.0",
                OSI_MCP_HTTP_PUBLIC_BIND_ACK=PUBLIC_BIND_ACK,
                OSI_PROVIDER="mock",
            )
        self.assertIn("OSI_PROVIDER=http", str(context.exception))

    def test_non_loopback_bind_requires_explicit_allowed_hosts(self) -> None:
        with self.assertRaises(ValueError) as context:
            self._settings(
                OSI_MCP_HTTP_HOST="0.0.0.0",
                OSI_MCP_HTTP_PUBLIC_BIND_ACK=PUBLIC_BIND_ACK,
                OSI_PROVIDER="http",
            )
        self.assertIn("OSI_MCP_HTTP_ALLOWED_HOSTS", str(context.exception))

    def test_non_loopback_bind_requires_allowlisted_https_radar_origin(self) -> None:
        for base_url in (
            "http://aiworkstation.cn",
            "https://example.com",
            "https://aiworkstation.cn/private/path",
            "https://user:pass@aiworkstation.cn",
        ):
            with self.subTest(base_url=base_url), self.assertRaises(ValueError):
                self._settings(
                    OSI_MCP_HTTP_HOST="0.0.0.0",
                    OSI_MCP_HTTP_PUBLIC_BIND_ACK=PUBLIC_BIND_ACK,
                    OSI_MCP_HTTP_ALLOWED_HOSTS="mcp.example.com,mcp.example.com:*",
                    OSI_PROVIDER="http",
                    AIWORKSTATION_RADAR_BASE_URL=base_url,
                )

    def test_non_loopback_host_allowlist_rejects_urls_and_invalid_ports(self) -> None:
        for allowed_hosts in (
            "https://mcp.example.com",
            "mcp.example.com/path",
            "mcp.example.com:70000",
            "mcp.example.com, bad host",
        ):
            with self.subTest(allowed_hosts=allowed_hosts), self.assertRaises(ValueError):
                self._settings(
                    OSI_MCP_HTTP_HOST="0.0.0.0",
                    OSI_MCP_HTTP_PUBLIC_BIND_ACK=PUBLIC_BIND_ACK,
                    OSI_MCP_HTTP_ALLOWED_HOSTS=allowed_hosts,
                    OSI_PROVIDER="http",
                )

    def test_browser_origins_are_https_origins_without_paths(self) -> None:
        for origin in (
            "http://app.example.com",
            "https://user:pass@app.example.com",
            "https://app.example.com/path",
            "https://app.example.com?debug=1",
        ):
            with self.subTest(origin=origin), self.assertRaises(ValueError):
                self._settings(
                    OSI_MCP_HTTP_HOST="0.0.0.0",
                    OSI_MCP_HTTP_PUBLIC_BIND_ACK=PUBLIC_BIND_ACK,
                    OSI_MCP_HTTP_ALLOWED_HOSTS="mcp.example.com",
                    OSI_MCP_HTTP_ALLOWED_ORIGINS=origin,
                    OSI_PROVIDER="http",
                )

    def test_acknowledged_non_loopback_bind_builds_explicit_transport_security(self) -> None:
        settings = self._settings(
            OSI_MCP_HTTP_HOST="0.0.0.0",
            OSI_MCP_HTTP_PUBLIC_BIND_ACK=PUBLIC_BIND_ACK,
            OSI_MCP_HTTP_ALLOWED_HOSTS="mcp.example.com,mcp.example.com:*",
            OSI_MCP_HTTP_ALLOWED_ORIGINS="https://app.example.com/",
            OSI_PROVIDER="http",
            AIWORKSTATION_RADAR_BASE_URL="https://aiworkstation.cn/",
        )
        self.assertTrue(settings.public_bind)
        self.assertEqual(settings.provider, "http")
        self.assertEqual(settings.radar_base_url, "https://aiworkstation.cn")
        self.assertEqual(
            settings.allowed_hosts,
            ("mcp.example.com", "mcp.example.com:*"),
        )
        self.assertEqual(settings.allowed_origins, ("https://app.example.com",))
        security = settings.transport_security()
        self.assertIsNotNone(security)
        assert security is not None
        self.assertEqual(security.allowed_hosts, ["mcp.example.com", "mcp.example.com:*"])
        self.assertEqual(security.allowed_origins, ["https://app.example.com"])

    def test_fake_auth_acknowledgement_is_rejected(self) -> None:
        with self.assertRaises(ValueError) as context:
            self._settings(OSI_MCP_HTTP_ASSUME_PUBLIC_AUTH="true")
        self.assertIn("not supported", str(context.exception))

    def test_port_and_request_body_are_bounded(self) -> None:
        for value in ("0", "65536", "not-a-port"):
            with self.subTest(port=value), self.assertRaises(ValueError):
                self._settings(OSI_MCP_HTTP_PORT=value)
        for value in ("100", "1048577", "not-a-size"):
            with self.subTest(body=value), self.assertRaises(ValueError):
                self._settings(OSI_MCP_HTTP_MAX_REQUEST_BODY_BYTES=value)

    def test_main_runs_streamable_http_stateless_json_without_opening_real_socket(self) -> None:
        fake_server = Mock()
        environment = {
            "OSI_MCP_HTTP_HOST": "127.0.0.1",
            "OSI_MCP_HTTP_PORT": "8123",
            "OSI_PROVIDER": "mock",
            "AIWORKSTATION_RADAR_BASE_URL": "https://aiworkstation.cn",
        }
        with (
            patch.dict(os.environ, environment, clear=True),
            patch("aiworkstation_osi.http_server.build_mcp_server", return_value=fake_server),
        ):
            exit_code = main([])

        self.assertEqual(exit_code, 0)
        fake_server.run.assert_called_once_with(
            transport="streamable-http",
            host="127.0.0.1",
            port=8123,
            stateless_http=True,
            json_response=True,
            max_request_body_size=DEFAULT_MAX_REQUEST_BODY_BYTES,
        )

    def test_nonloopback_main_passes_transport_security_to_sdk(self) -> None:
        fake_server = Mock()
        environment = {
            "OSI_MCP_HTTP_HOST": "0.0.0.0",
            "OSI_MCP_HTTP_PORT": "8000",
            "OSI_MCP_HTTP_PUBLIC_BIND_ACK": PUBLIC_BIND_ACK,
            "OSI_MCP_HTTP_ALLOWED_HOSTS": "mcp.example.com,mcp.example.com:*",
            "OSI_PROVIDER": "http",
            "AIWORKSTATION_RADAR_BASE_URL": "https://aiworkstation.cn",
        }
        with (
            patch.dict(os.environ, environment, clear=True),
            patch("aiworkstation_osi.http_server.build_mcp_server", return_value=fake_server),
        ):
            exit_code = main([])

        self.assertEqual(exit_code, 0)
        call = fake_server.run.call_args
        self.assertIsNotNone(call)
        assert call is not None
        kwargs = call.kwargs
        self.assertEqual(kwargs["transport"], "streamable-http")
        self.assertEqual(kwargs["host"], "0.0.0.0")
        security = kwargs["transport_security"]
        self.assertEqual(security.allowed_hosts, ["mcp.example.com", "mcp.example.com:*"])
        self.assertEqual(security.allowed_origins, [])

    def test_check_config_does_not_build_or_run_server(self) -> None:
        environment = {
            "OSI_MCP_HTTP_HOST": "127.0.0.1",
            "OSI_MCP_HTTP_PORT": "8000",
            "OSI_PROVIDER": "mock",
        }
        with (
            patch.dict(os.environ, environment, clear=True),
            patch("aiworkstation_osi.http_server.build_mcp_server") as builder,
        ):
            exit_code = main(["--check-config"])

        self.assertEqual(exit_code, 0)
        builder.assert_not_called()


if __name__ == "__main__":
    unittest.main()
