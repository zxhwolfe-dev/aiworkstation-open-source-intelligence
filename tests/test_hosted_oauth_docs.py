from __future__ import annotations

import unittest
from pathlib import Path


class HostedOAuthDocumentationTests(unittest.TestCase):
    ROOT = Path(__file__).resolve().parents[1]

    def test_oauth_document_is_explicitly_disabled_for_current_product(self) -> None:
        hosted = (self.ROOT / "docs" / "HOSTED-OAUTH.md").read_text(encoding="utf-8")
        compose = (self.ROOT / "compose.public-hosted.example.yml").read_text(encoding="utf-8")

        self.assertIn("Disabled in the current product", hosted)
        self.assertIn("OSI_HOSTED_ACCESS_MODE=oauth", hosted)
        self.assertIn("must fail closed", hosted)
        self.assertIn("use_model=false", hosted)
        self.assertIn("new reviewed product version", hosted)

        self.assertIn("OSI_HOSTED_ACCESS_MODE: public", compose)
        self.assertNotIn("OSI_OAUTH_", compose)
        self.assertNotIn("OSI_BACKEND_SERVICE_TOKEN", compose)
        self.assertNotIn("OSI_PREMIUM_RATE_LIMIT", compose)

    def test_candidate_release_identity_remains_mandatory(self) -> None:
        hosted = (self.ROOT / "docs" / "HOSTED-OAUTH.md").read_text(encoding="utf-8")
        dockerfile = (self.ROOT / "Dockerfile").read_text(encoding="utf-8")
        compose = (self.ROOT / "compose.public-hosted.example.yml").read_text(encoding="utf-8")

        self.assertIn("OSI_RELEASE_COMMIT=<exact-40-character-hosted-candidate-sha>", hosted)
        self.assertIn("OSI_IMAGE_COMMIT=<same-exact-candidate-sha>", hosted)
        self.assertIn('ARG OSI_IMAGE_COMMIT=""', dockerfile)
        self.assertIn("OSI_IMAGE_COMMIT=${OSI_IMAGE_COMMIT}", dockerfile)
        self.assertIn("org.opencontainers.image.revision=${OSI_IMAGE_COMMIT}", dockerfile)
        self.assertIn("OSI_IMAGE_COMMIT: ${OSI_RELEASE_COMMIT:?required}", compose)
        self.assertIn("OSI_RELEASE_COMMIT: ${OSI_RELEASE_COMMIT:?required}", compose)

    def test_current_public_nginx_has_no_oauth_metadata_routes(self) -> None:
        nginx = (
            self.ROOT / "deploy" / "nginx" / "mcp.aiworkstation.cn.conf.example"
        ).read_text(encoding="utf-8")
        self.assertNotIn("oauth-protected-resource", nginx)
        self.assertNotIn("proxy_set_header Authorization", nginx)
        self.assertIn("proxy_pass http://127.0.0.1:8001/mcp;", nginx)


if __name__ == "__main__":
    unittest.main()
