from __future__ import annotations

import asyncio
import unittest

from mcp import Client

from aiworkstation_osi.app import create_default_registry
from aiworkstation_osi.contracts import HOSTED_TOOL_NAMES, TOOL_NAMES
from aiworkstation_osi.hosted_mcp_server import (
    HOSTED_INSTRUCTIONS,
    PUBLIC_HOSTED_INSTRUCTIONS,
    build_hosted_mcp_server,
    build_public_hosted_mcp_server,
)


class HostedMcpServerTests(unittest.TestCase):
    def test_hosted_contract_is_exactly_nine_standard_tools(self) -> None:
        self.assertEqual(HOSTED_TOOL_NAMES, TOOL_NAMES)
        self.assertEqual(len(HOSTED_TOOL_NAMES), 9)
        self.assertNotIn("deep_research_ai_projects", HOSTED_TOOL_NAMES)

    def test_public_hosted_server_lists_only_nine_read_only_tools(self) -> None:
        async def run():
            server = build_public_hosted_mcp_server(create_default_registry())
            async with Client(server) as client:
                listed = await client.list_tools()
                self.assertEqual({tool.name for tool in listed.tools}, set(TOOL_NAMES))
                self.assertEqual(len(listed.tools), 9)
                for tool in listed.tools:
                    annotations = tool.annotations
                    self.assertIsNotNone(annotations)
                    assert annotations is not None
                    self.assertIs(annotations.read_only_hint, True)
                    self.assertIs(annotations.destructive_hint, False)
                    self.assertIs(annotations.idempotent_hint, True)
        asyncio.run(run())

    def test_hosted_instructions_explicitly_forbid_server_model_execution(self) -> None:
        for instructions in (PUBLIC_HOSTED_INSTRUCTIONS, HOSTED_INSTRUCTIONS):
            lower = instructions.lower()
            self.assertIn("server-side ai", lower)
            self.assertIn("no premium model tool", lower)

    def test_compatibility_builder_has_same_data_only_surface(self) -> None:
        async def run():
            server = build_hosted_mcp_server(create_default_registry())
            async with Client(server) as client:
                listed = await client.list_tools()
                self.assertEqual({tool.name for tool in listed.tools}, set(TOOL_NAMES))
        asyncio.run(run())

    def test_compatibility_builder_rejects_oauth_or_premium_options(self) -> None:
        with self.assertRaises(ValueError) as context:
            build_hosted_mcp_server(create_default_registry(), token_verifier=object())
        self.assertIn("OAuth/Premium Hosted options are disabled", str(context.exception))


if __name__ == "__main__":
    unittest.main()
