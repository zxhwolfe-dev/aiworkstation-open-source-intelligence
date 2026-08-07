from __future__ import annotations

import os
import unittest
from unittest.mock import patch

from aiworkstation_osi.http_server import PUBLIC_BIND_ACK, load_http_server_settings


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
        self.assertTrue(settings.stateless_http)
        self.assertTrue(settings.json_response)

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
                    OSI_PROVIDER="http",
                    AIWORKSTATION_RADAR_BASE_URL=base_url,
                )

    def test_acknowledged_non_loopback_bind_accepts_live_provider(self) -> None:
        settings = self._settings(
            OSI_MCP_HTTP_HOST="0.0.0.0",
            OSI_MCP_HTTP_PUBLIC_BIND_ACK=PUBLIC_BIND_ACK,
            OSI_PROVIDER="http",
            AIWORKSTATION_RADAR_BASE_URL="https://aiworkstation.cn/",
        )
        self.assertTrue(settings.public_bind)
        self.assertEqual(settings.provider, "http")
        self.assertEqual(settings.radar_base_url, "https://aiworkstation.cn")

    def test_fake_auth_acknowledgement_is_rejected(self) -> None:
        with self.assertRaises(ValueError) as context:
            self._settings(OSI_MCP_HTTP_ASSUME_PUBLIC_AUTH="true")
        self.assertIn("not supported", str(context.exception))

    def test_port_is_bounded(self) -> None:
        for value in ("0", "65536", "not-a-port"):
            with self.subTest(value=value), self.assertRaises(ValueError):
                self._settings(OSI_MCP_HTTP_PORT=value)


if __name__ == "__main__":
    unittest.main()
