from __future__ import annotations

import asyncio
import unittest
from unittest.mock import patch

from mcp.server.auth.provider import AccessToken

from aiworkstation_osi.hosted_auth import (
    HostedOAuthConfig,
    IntrospectionTokenVerifier,
    entitlement_subject,
    hosted_auth_settings,
    load_hosted_oauth_config,
)


class HostedAuthTests(unittest.TestCase):
    def setUp(self) -> None:
        self.config = HostedOAuthConfig(
            issuer_url="https://auth.example.com",
            introspection_url="https://auth.example.com/oauth2/introspect",
            client_id="mcp-client",
            client_secret="private-secret",
            resource_url="https://mcp.example.com/mcp",
            required_scopes=("osi:use",),
            introspection_auth="basic",
            timeout_seconds=5,
        )

    def test_entitlement_subject_is_stable_opaque_and_issuer_bound(self) -> None:
        token = AccessToken(
            token="raw-secret-token",
            client_id="client",
            scopes=["osi:use"],
            expires_at=4_000_000_000,
            resource="https://mcp.example.com/mcp",
            subject="real-user-subject",
            claims={"iss": "https://auth.example.com"},
        )
        first = entitlement_subject(token)
        second = entitlement_subject(token)
        other_issuer = AccessToken(
            token="other",
            client_id="client",
            scopes=["osi:use"],
            expires_at=4_000_000_000,
            resource="https://mcp.example.com/mcp",
            subject="real-user-subject",
            claims={"iss": "https://other.example.com"},
        )
        self.assertEqual(first, second)
        self.assertTrue(first.startswith("oidc_"))
        self.assertNotIn("real-user-subject", first)
        self.assertNotIn("raw-secret-token", first)
        self.assertNotEqual(first, entitlement_subject(other_issuer))

    def test_verifier_accepts_active_matching_subject_scope_resource_and_issuer(self) -> None:
        verifier = IntrospectionTokenVerifier(self.config)
        payload = {
            "active": True,
            "client_id": "openai-plugin",
            "sub": "user-1",
            "iss": "https://auth.example.com",
            "scope": "openid osi:use",
            "aud": ["https://mcp.example.com/mcp"],
            "exp": 4_000_000_000,
        }
        with patch.object(verifier, "_introspect", return_value=payload):
            token = asyncio.run(verifier.verify_token("bearer-token"))
        self.assertIsNotNone(token)
        assert token is not None
        self.assertEqual(token.subject, "user-1")
        self.assertEqual(token.client_id, "openai-plugin")
        self.assertEqual(token.resource, "https://mcp.example.com/mcp")
        self.assertIn("osi:use", token.scopes)
        self.assertEqual(token.claims["iss"], "https://auth.example.com")

    def test_verifier_fails_closed_on_inactive_expired_wrong_scope_resource_or_issuer(self) -> None:
        verifier = IntrospectionTokenVerifier(self.config)
        base = {
            "active": True,
            "client_id": "client",
            "sub": "user",
            "iss": "https://auth.example.com",
            "scope": "osi:use",
            "aud": "https://mcp.example.com/mcp",
            "exp": 4_000_000_000,
        }
        variants = [
            {**base, "active": False},
            {**base, "exp": 1},
            {**base, "scope": "openid"},
            {**base, "aud": "https://other.example.com/mcp"},
            {**base, "iss": "https://evil.example.com"},
            {**base, "sub": ""},
            {**base, "client_id": ""},
        ]
        for payload in variants:
            with self.subTest(payload=payload), patch.object(verifier, "_introspect", return_value=payload):
                self.assertIsNone(asyncio.run(verifier.verify_token("token")))

    def test_auth_settings_publish_resource_and_required_scope(self) -> None:
        settings = hosted_auth_settings(self.config)
        self.assertEqual(str(settings.issuer_url).rstrip("/"), "https://auth.example.com")
        self.assertEqual(str(settings.resource_server_url).rstrip("/"), "https://mcp.example.com/mcp")
        self.assertEqual(settings.required_scopes, ["osi:use"])

    def test_env_config_rejects_non_https_urls_or_missing_credentials(self) -> None:
        good = {
            "OSI_OAUTH_ISSUER_URL": "https://auth.example.com",
            "OSI_OAUTH_INTROSPECTION_URL": "https://auth.example.com/introspect",
            "OSI_OAUTH_CLIENT_ID": "client",
            "OSI_OAUTH_CLIENT_SECRET": "secret",
            "OSI_OAUTH_RESOURCE_URL": "https://mcp.example.com/mcp",
        }
        with patch.dict("os.environ", good, clear=True):
            config = load_hosted_oauth_config()
        self.assertEqual(config.required_scopes, ("osi:use",))

        for key, value in (
            ("OSI_OAUTH_ISSUER_URL", "http://auth.example.com"),
            ("OSI_OAUTH_INTROSPECTION_URL", "https://user:pass@auth.example.com/introspect"),
            ("OSI_OAUTH_RESOURCE_URL", "https://mcp.example.com/mcp?token=x"),
        ):
            broken = dict(good)
            broken[key] = value
            with self.subTest(key=key), patch.dict("os.environ", broken, clear=True), self.assertRaises(ValueError):
                load_hosted_oauth_config()


if __name__ == "__main__":
    unittest.main()
