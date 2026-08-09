from __future__ import annotations

import unittest
from pathlib import Path


class HostedOAuthDocumentationTests(unittest.TestCase):
    def test_oauth_compatibility_contract_remains_documented_but_optional(self) -> None:
        root = Path(__file__).resolve().parents[1]
        hosted = (root / "docs" / "HOSTED-OAUTH.md").read_text(encoding="utf-8")
        compose = (root / "compose.public-hosted.example.yml").read_text(encoding="utf-8")
        dockerfile = (root / "Dockerfile").read_text(encoding="utf-8")

        self.assertIn("OSI_RELEASE_COMMIT=<exact-40-character-hosted-candidate-sha>", hosted)
        self.assertIn("OSI_OAUTH_REQUIRED_SCOPES=", hosted)
        self.assertIn("OSI_OAUTH_INTROSPECTION_AUTH=body", hosted)
        self.assertNotIn("OSI_OAUTH_REQUIRED_SCOPES=osi:use", hosted)
        self.assertNotIn("OSI_OAUTH_INTROSPECTION_AUTH=basic", hosted)

        self.assertIn("OSI_IMAGE_COMMIT: ${OSI_RELEASE_COMMIT:?required}", compose)
        self.assertIn("OSI_RELEASE_COMMIT: ${OSI_RELEASE_COMMIT:?required}", compose)
        self.assertIn("OSI_HOSTED_ACCESS_MODE: ${OSI_HOSTED_ACCESS_MODE:-public}", compose)
        self.assertIn("OSI_OAUTH_CLIENT_SECRET: ${OSI_OAUTH_CLIENT_SECRET:-}", compose)
        self.assertNotIn("OSI_OAUTH_CLIENT_SECRET: ${OSI_OAUTH_CLIENT_SECRET:?required}", compose)
        self.assertIn("OSI_OAUTH_REQUIRED_SCOPES: ${OSI_OAUTH_REQUIRED_SCOPES:-}", compose)
        self.assertIn("OSI_OAUTH_INTROSPECTION_AUTH: ${OSI_OAUTH_INTROSPECTION_AUTH:-body}", compose)
        self.assertIn("OSI_OAUTH_RESOURCE_URL: https://mcp.aiworkstation.cn/mcp", compose)

        self.assertIn('ARG OSI_IMAGE_COMMIT=""', dockerfile)
        self.assertIn("OSI_IMAGE_COMMIT=${OSI_IMAGE_COMMIT}", dockerfile)
        self.assertIn("org.opencontainers.image.revision=${OSI_IMAGE_COMMIT}", dockerfile)

    def test_hosted_runbook_defaults_to_public_candidate_bound_evidence(self) -> None:
        root = Path(__file__).resolve().parents[1]
        runbook = (root / "docs" / "hosted-private-alpha.md").read_text(encoding="utf-8")

        self.assertIn("OSI_RELEASE_COMMIT=<exact-hosted-candidate-sha>", runbook)
        self.assertIn("OSI_HOSTED_ACCESS_MODE=public", runbook)
        self.assertIn("deployment_commit", runbook)
        self.assertIn("deployment-identity", runbook)
        self.assertIn("serverInfo.version", runbook)
        self.assertIn("--profile hosted-public", runbook)
        self.assertIn("--auth-mode none", runbook)
        self.assertIn("--expected-access-mode public", runbook)
        self.assertIn("WorkOS is only one optional provider", runbook)

    def test_public_launch_decision_does_not_reintroduce_mandatory_osi_scope(self) -> None:
        root = Path(__file__).resolve().parents[1]
        decisions = (root / "docs" / "public-launch-decisions.md").read_text(encoding="utf-8")

        self.assertIn("Resource Indicator", decisions)
        self.assertIn("OSI_OAUTH_REQUIRED_SCOPES", decisions)
        self.assertNotIn("resource/audience and `osi:use` scope", decisions)
        self.assertNotIn("correct resource/audience and `osi:use` scope", decisions)


if __name__ == "__main__":
    unittest.main()
