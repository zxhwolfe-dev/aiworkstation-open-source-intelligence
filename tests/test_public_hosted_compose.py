from __future__ import annotations

import unittest
from pathlib import Path


class PublicHostedComposeTests(unittest.TestCase):
    ROOT = Path(__file__).resolve().parents[1]

    @classmethod
    def setUpClass(cls) -> None:
        cls.content = (cls.ROOT / "compose.public-hosted.example.yml").read_text(encoding="utf-8")

    def test_host_port_is_loopback_only_and_hosted_command_is_explicit(self) -> None:
        self.assertIn('127.0.0.1:8001:8000', self.content)
        self.assertIn('command: ["osi-mcp-hosted"]', self.content)
        self.assertNotIn('0.0.0.0:8001:8000', self.content)

    def test_container_keeps_existing_hardening(self) -> None:
        self.assertIn("read_only: true", self.content)
        self.assertIn('cap_drop: ["ALL"]', self.content)
        self.assertIn("no-new-privileges:true", self.content)
        self.assertIn("tmpfs:", self.content)
        self.assertIn("resources:", self.content)

    def test_container_logs_are_bounded(self) -> None:
        self.assertIn("logging:", self.content)
        self.assertIn("driver: json-file", self.content)
        self.assertIn('max-size: "10m"', self.content)
        self.assertIn('max-file: "5"', self.content)

    def test_hosted_mode_is_fixed_to_public_data_only(self) -> None:
        self.assertIn("OSI_HOSTED_ACCESS_MODE: public", self.content)
        self.assertNotIn("${OSI_HOSTED_ACCESS_MODE", self.content)
        for forbidden in (
            "OSI_OAUTH_",
            "OSI_BACKEND_SERVICE_TOKEN",
            "OSI_PREMIUM_RATE_LIMIT",
            "PADDLE_",
        ):
            self.assertNotIn(forbidden, self.content)

    def test_provider_is_live_public_radar_and_release_identity_is_required(self) -> None:
        self.assertIn("OSI_PROVIDER: http", self.content)
        self.assertIn("AIWORKSTATION_RADAR_BASE_URL: https://aiworkstation.cn", self.content)
        self.assertIn("OSI_RELEASE_COMMIT: ${OSI_RELEASE_COMMIT:?required}", self.content)
        self.assertIn("OSI_MCP_HTTP_PUBLIC_BIND_ACK: reverse-proxy-or-private-network", self.content)
        self.assertIn('OSI_MCP_HTTP_MAX_REQUEST_BODY_BYTES: "262144"', self.content)
        self.assertNotIn("OSI_MCP_HTTP_BODY_LIMIT_BYTES", self.content)


if __name__ == "__main__":
    unittest.main()
