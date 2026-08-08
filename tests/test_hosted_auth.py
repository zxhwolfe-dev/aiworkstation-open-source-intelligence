from __future__ import annotations

import asyncio
import json
import unittest
import urllib.parse
from unittest.mock import patch

from mcp.server.auth.provider import AccessToken

from aiworkstation_osi.hosted_auth import (
    HostedOAuthConfig,
    IntrospectionTokenVerifier,
    entitlement_subject,
    hosted_auth_settings,
    load_hosted_oauth_config,
)


class _FakeResponse:
    status = 200

    def __init__(self, payload: dict[str, object]) -> None:
        self._raw = json.dumps(payload).encode("utf-8")

    def __enter__(self) -> "_FakeResponse":
        return self

    def __exit__(self, exc_type, exc, tb) -> None:  # type: ignore[no-untyped-def]
        return None

    def read(self, _limit: int) -> bytes:
        return self._raw


class _RecordingOpener:
    def __init__(self, payload: dict[str, object]) -> None:
        self.payload = payload
        self.request = None
        self.timeout = None

    def open(self, request, timeout):  # type: ignore[no-untyped-def]
        self.request = request
        self.timeout = timeout
        return _FakeResponse(self.payload)


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
            "token_type": "access_token",
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

    def test_workos_shape_accepts_resource_bound_access_token_without_custom_scope(self) -> None:
        config = HostedOAuthConfig(
            issuer_url="https://auth.example.com",
            introspection_url="https://auth.example.com/oauth2/introspection",
            client_id="resource-server",
            client_secret="secret",
            resource_url="https://mcp.example.com/mcp",
            required_scopes=(),
            introspection_auth="body",
        )
        verifier = IntrospectionTokenVerifier(config)
        payload = {
            "active": True,
            "client_id": "client_01JP8BD0CZ401TDF9X54NT5ZEK",
            "iss": "https://auth.example.com",
            "aud": "https://mcp.example.com/mcp",
            "sub": "user_01JPXN6KA7622KJ4VP83X1NTKX",
            "org_id": "org_01HRDMC6CM357W30QMHMQ96Q0S",
            "sid": "app_consent_01JPXN6KAQW83AMXXY5WX3RHTJ",
            "jti": "01JPXN6KFGZQYW3AM2DEVX84YS",
            "exp": 4_000_000_000,
            "iat": 1_742_604_553,
            "token_type": "access_token",
        }
        with patch.object(verifier, "_introspect", return_value=payload):
            token = asyncio.run(verifier.verify_token("workos-access-token"))
        self.assertIsNotNone(token)
        assert token is not None
        self.assertEqual(token.scopes, [])
        self.assertEqual(token.resource, "https://mcp.example.com/mcp")

    def test_verifier_rejects_refresh_token_even_when_resource_matches(self) -> None:
        config = HostedOAuthConfig(
            issuer_url="https://auth.example.com",
            introspection_url="https://auth.example.com/oauth2/introspection",
            client_id="resource-server",
            client_secret="secret",
            resource_url="https://mcp.example.com/mcp",
            required_scopes=(),
        )
        verifier = IntrospectionTokenVerifier(config)
        payload = {
            "active": True,
            "client_id": "client_01JP8BD0CZ401TDF9X54NT5ZEK",
            "iss": "https://auth.example.com",
            "aud": "https://mcp.example.com/mcp",
            "sub": "user_01JPXN6KA7622KJ4VP83X1NTKX",
            "iat": 1_742_604_553,
            "token_type": "refresh_token",
        }
        with patch.object(verifier, "_introspect", return_value=payload):
            self.assertIsNone(asyncio.run(verifier.verify_token("workos-refresh-token")))

    def test_body_introspection_sends_access_token_hint_and_resource_server_credentials(self) -> None:
        config = HostedOAuthConfig(
            issuer_url="https://auth.example.com",
            introspection_url="https://auth.example.com/oauth2/introspection",
            client_id="resource-server",
            client_secret="secret",
            resource_url="https://mcp.example.com/mcp",
            required_scopes=(),
            introspection_auth="body",
            timeout_seconds=7,
        )
        verifier = IntrospectionTokenVerifier(config)
        opener = _RecordingOpener({"active": False})
        verifier._opener = opener
        self.assertEqual(verifier._introspect("bearer-token"), {"active": False})
        assert opener.request is not None
        form = urllib.parse.parse_qs(opener.request.data.decode("utf-8"))
        self.assertEqual(form["token"], ["bearer-token"])
        self.assertEqual(form["token_type_hint"], ["access_token"])
        self.assertEqual(form["client_id"], ["resource-server"])
        self.assertEqual(form["client_secret"], ["secret"])
        self.assertEqual(opener.timeout, 7)

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
            "token_type": "access_token",
        }
        variants = [
            {**base, "active": False},
            {**base, "exp": 1},
            {**base, "scope": "openid"},
            {**base, "aud": "https://other.example.com/mcp"},
            {**base, "iss": "https://evil.example.com"},
            {**base, "iss": ""},
            {**base, "sub": ""},
            {**base, "client_id": ""},
            {**base, "token_type": "refresh_token"},
        ]
        for payload in variants:
            with self.subTest(payload=payload), patch.object(verifier, "_introspect", return_value=payload):
                self.assertIsNone(asyncio.run(verifier.verify_token("token")))

    def test_auth_settings_publish_resource_and_required_scope(self) -> None:
        settings = hosted_auth_settings(self.config)
        self.assertEqual(str(settings.issuer_url).rstrip("/"), "https://auth.example.com")
        self.assertEqual(str(settings.resource_server_url).rstrip("/"), "https://mcp.example.com/mcp")
        self.assertEqual(settings.required_scopes, ["osi:use"])

    def test_env_config_defaults_to_workos_resource_binding_and_allows_opt_in_scopes(self) -> None:
        good = {
            "OSI_OAUTH_ISSUER_URL": "https://auth.example.com",
            "OSI_OAUTH_INTROSPECTION_URL": "https://auth.example.com/introspect",
            "OSI_OAUTH_CLIENT_ID": "client",
            "OSI_OAUTH_CLIENT_SECRET": "secret",
            "OSI_OAUTH_RESOURCE_URL": "https://mcp.example.com/mcp",
        }
        with patch.dict("os.environ", good, clear=True):
            config = load_hosted_oauth_config()
        self.assertEqual(config.required_scopes, ())
        self.assertEqual(config.introspection_auth, "body")

        scoped = {**good, "OSI_OAUTH_REQUIRED_SCOPES": "osi:use admin"}
        with patch.dict("os.environ", scoped, clear=True):
            config = load_hosted_oauth_config()
        self.assertEqual(config.required_scopes, ("osi:use", "admin"))

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
