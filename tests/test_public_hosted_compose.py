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

    def test_oauth_and_backend_secrets_are_required_from_environment(self) -> None:
        for name in (
            "OSI_OAUTH_ISSUER_URL",
            "OSI_OAUTH_INTROSPECTION_URL",
            "OSI_OAUTH_CLIENT_ID",
            "OSI_OAUTH_CLIENT_SECRET",
            "OSI_BACKEND_SERVICE_TOKEN",
        ):
            self.assertIn(f"${{{name}:?required}}", self.content)
        self.assertNotIn("PADDLE_API_KEY", self.content)
        self.assertNotIn("PADDLE_WEBHOOK_SECRET", self.content)

    def test_public_resource_is_https_mcp_and_provider_is_live(self) -> None:
        self.assertIn("OSI_PROVIDER: http", self.content)
        self.assertIn("AIWORKSTATION_RADAR_BASE_URL: https://aiworkstation.cn", self.content)
        self.assertIn("OSI_OAUTH_RESOURCE_URL: https://mcp.aiworkstation.cn/mcp", self.content)
        self.assertIn('OSI_OAUTH_REQUIRED_SCOPES: "${OSI_OAUTH_REQUIRED_SCOPES:-}"', self.content)
        self.assertNotIn("OSI_OAUTH_REQUIRED_SCOPES: osi:use", self.content)
        self.assertIn("OSI_MCP_HTTP_PUBLIC_BIND_ACK: reverse-proxy-or-private-network", self.content)

    def test_user_and_premium_rate_limits_are_explicit(self) -> None:
        self.assertIn('OSI_RATE_LIMIT_PER_MINUTE: "60"', self.content)
        self.assertIn('OSI_RATE_LIMIT_PER_HOUR: "300"', self.content)
        self.assertIn('OSI_PREMIUM_RATE_LIMIT_PER_MINUTE: "5"', self.content)


if __name__ == "__main__":
    unittest.main()
