from __future__ import annotations

import unittest
from pathlib import Path


class PublicHostedNginxTests(unittest.TestCase):
    ROOT = Path(__file__).resolve().parents[1]

    def setUp(self) -> None:
        self.content = (
            self.ROOT / "deploy" / "nginx" / "mcp.aiworkstation.cn.conf.example"
        ).read_text(encoding="utf-8")

    def test_public_hostname_proxies_only_mcp_to_loopback(self) -> None:
        self.assertIn("server_name mcp.aiworkstation.cn;", self.content)
        self.assertIn("proxy_pass http://127.0.0.1:8001/mcp;", self.content)
        self.assertNotIn("oauth-protected-resource", self.content)
        self.assertIn("location / {\n        return 404;", self.content)
        self.assertNotIn("proxy_pass http://0.0.0.0", self.content)
        self.assertNotIn("proxy_set_header Authorization", self.content)

    def test_public_mode_has_short_and_sustained_ip_abuse_controls(self) -> None:
        self.assertIn("limit_req_zone $binary_remote_addr zone=osi_mcp_public:10m rate=60r/m;", self.content)
        self.assertIn("limit_req_zone $binary_remote_addr zone=osi_mcp_sustained:10m rate=10r/m;", self.content)
        self.assertIn("limit_conn_zone $binary_remote_addr zone=osi_mcp_conn:10m;", self.content)
        self.assertIn("limit_req zone=osi_mcp_public burst=30 nodelay;", self.content)
        self.assertIn("limit_req zone=osi_mcp_sustained burst=300 nodelay;", self.content)
        self.assertIn("limit_conn osi_mcp_conn 10;", self.content)
        self.assertIn('X-OSI-Hosted-Gateway-Policy "tls-ip-rate-limited"', self.content)
        self.assertIn("limit_req_status 429;", self.content)

    def test_mcp_proxy_preserves_streaming_and_body_boundaries(self) -> None:
        self.assertIn("proxy_buffering off;", self.content)
        self.assertIn("proxy_request_buffering off;", self.content)
        self.assertIn("client_max_body_size 256k;", self.content)
        self.assertIn("proxy_read_timeout 180s;", self.content)

    def test_tls_redirect_and_certificate_are_explicit(self) -> None:
        self.assertIn("return 308 https://$host$request_uri;", self.content)
        self.assertIn("Strict-Transport-Security", self.content)
        self.assertIn(
            "ssl_certificate /etc/letsencrypt/live/mcp.aiworkstation.cn/fullchain.pem;",
            self.content,
        )
        self.assertIn(
            "ssl_certificate_key /etc/letsencrypt/live/mcp.aiworkstation.cn/privkey.pem;",
            self.content,
        )


if __name__ == "__main__":
    unittest.main()
