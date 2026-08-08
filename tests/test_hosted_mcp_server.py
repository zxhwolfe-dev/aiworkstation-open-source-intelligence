from __future__ import annotations

import asyncio
import unittest
from unittest.mock import patch

from mcp import Client
from mcp.server.auth.provider import AccessToken, TokenVerifier

from aiworkstation_osi.app import create_default_registry
from aiworkstation_osi.contracts import HOSTED_TOOL_NAMES, TOOL_NAMES
from aiworkstation_osi.hosted_auth import HostedOAuthConfig, hosted_auth_settings
from aiworkstation_osi.hosted_backend import HostedBackendError
from aiworkstation_osi.hosted_mcp_server import HOSTED_INSTRUCTIONS, build_hosted_mcp_server
from aiworkstation_osi.hosted_rate_limit import HostedRateLimitConfig, HostedRateLimiter


class DummyVerifier(TokenVerifier):
    async def verify_token(self, token: str):
        return AccessToken(
            token=token,
            client_id="client",
            scopes=["osi:use"],
            expires_at=4_000_000_000,
            resource="https://mcp.example.com/mcp",
            subject="user",
            claims={"iss": "https://auth.example.com"},
        )


class FakeBackend:
    def __init__(self, *, upgrade: bool = False):
        self.upgrade = upgrade
        self.premium_calls = []
        self.checkout_calls = []

    def premium_research(self, subject, **kwargs):
        self.premium_calls.append((subject, kwargs))
        if self.upgrade:
            raise HostedBackendError(
                "UPGRADE_REQUIRED",
                "upgrade",
                status=402,
                details={"entitlement": {"trial_available": False, "ai_credits": 0}},
            )
        return {
            "selection": {"snapshot_id": "sha256:test", "projects": []},
            "premium": {
                "analysis": "Evidence-backed premium analysis",
                "focus": kwargs["focus"],
                "snapshot_id": "sha256:test",
                "provider_model": "server-model",
                "credit_source": "free_trial",
                "entitlement": {"trial_available": False, "ai_credits": 0},
            },
        }

    def create_checkout(self, subject):
        self.checkout_calls.append(subject)
        return {
            "provider": "paddle",
            "checkout_url": "https://checkout.example/txn",
            "monthly_ai_credits": 50,
        }


class HostedMcpServerTests(unittest.TestCase):
    def _build(self, backend):
        config = HostedOAuthConfig(
            issuer_url="https://auth.example.com",
            introspection_url="https://auth.example.com/introspect",
            client_id="client",
            client_secret="secret",
            resource_url="https://mcp.example.com/mcp",
            required_scopes=("osi:use",),
        )
        limiter = HostedRateLimiter(
            HostedRateLimitConfig(per_minute=20, per_hour=100, premium_per_minute=5, max_subjects=100)
        )
        return build_hosted_mcp_server(
            create_default_registry(),
            token_verifier=DummyVerifier(),
            auth=hosted_auth_settings(config),
            backend=backend,
            rate_limiter=limiter,
        )

    def test_hosted_server_lists_nine_read_only_tools_plus_one_premium_tool(self) -> None:
        async def run():
            server = self._build(FakeBackend())
            async with Client(server) as client:
                listed = await client.list_tools()
                self.assertEqual({tool.name for tool in listed.tools}, set(HOSTED_TOOL_NAMES))
                self.assertEqual(len(listed.tools), 10)
                by_name = {tool.name: tool for tool in listed.tools}
                for name in TOOL_NAMES:
                    annotations = by_name[name].annotations
                    self.assertIsNotNone(annotations)
                    assert annotations is not None
                    self.assertIs(annotations.read_only_hint, True)
                    self.assertIs(annotations.destructive_hint, False)
                    self.assertIs(annotations.idempotent_hint, True)
                premium = by_name["deep_research_ai_projects"].annotations
                self.assertIsNotNone(premium)
                assert premium is not None
                self.assertIs(premium.read_only_hint, False)
                self.assertIs(premium.destructive_hint, False)
                self.assertIs(premium.idempotent_hint, False)
        asyncio.run(run())

    def test_hosted_instructions_do_not_claim_entire_server_is_read_only(self) -> None:
        self.assertIn("nine Radar data/research tools are read-only", HOSTED_INSTRUCTIONS)
        self.assertIn("premium", HOSTED_INSTRUCTIONS.lower())
        self.assertIn("free premium trial or AI credits", HOSTED_INSTRUCTIONS)

    def test_premium_success_uses_only_opaque_entitlement_subject(self) -> None:
        async def run():
            backend = FakeBackend()
            server = self._build(backend)
            with patch(
                "aiworkstation_osi.hosted_mcp_server.current_entitlement_subject",
                return_value="oidc_opaque",
            ):
                async with Client(server) as client:
                    result = await client.call_tool(
                        "deep_research_ai_projects",
                        {"query": "Compare RAG platforms", "focus": "comparison", "locale": "en"},
                    )
            self.assertFalse(result.is_error)
            self.assertEqual(backend.premium_calls[0][0], "oidc_opaque")
            payload = result.structured_content
            self.assertIsNotNone(payload)
            assert payload is not None
            self.assertEqual(payload["data"]["status"], "completed")
            self.assertEqual(payload["data"]["credit_source"], "free_trial")
            self.assertEqual(payload["recommendations"][0]["summary"], "Evidence-backed premium analysis")
        asyncio.run(run())

    def test_upgrade_state_returns_checkout_without_tool_error(self) -> None:
        async def run():
            backend = FakeBackend(upgrade=True)
            server = self._build(backend)
            with patch(
                "aiworkstation_osi.hosted_mcp_server.current_entitlement_subject",
                return_value="oidc_opaque",
            ):
                async with Client(server) as client:
                    result = await client.call_tool(
                        "deep_research_ai_projects",
                        {"query": "Deep research", "locale": "en"},
                    )
            self.assertFalse(result.is_error)
            payload = result.structured_content
            self.assertIsNotNone(payload)
            assert payload is not None
            self.assertEqual(payload["data"]["status"], "upgrade_required")
            self.assertEqual(payload["data"]["checkout"]["provider"], "paddle")
            self.assertEqual(payload["data"]["checkout"]["checkout_url"], "https://checkout.example/txn")
            self.assertEqual(backend.checkout_calls, ["oidc_opaque"])
        asyncio.run(run())


if __name__ == "__main__":
    unittest.main()
