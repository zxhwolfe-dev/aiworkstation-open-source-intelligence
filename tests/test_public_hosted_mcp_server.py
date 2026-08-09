from __future__ import annotations

import asyncio
import unittest

from mcp import Client

from aiworkstation_osi.app import create_default_registry
from aiworkstation_osi.contracts import TOOL_NAMES
from aiworkstation_osi.hosted_mcp_server import (
    PUBLIC_HOSTED_INSTRUCTIONS,
    build_public_hosted_mcp_server,
)


class PublicHostedMcpServerTests(unittest.TestCase):
    def test_public_hosted_lists_exactly_nine_read_only_tools(self) -> None:
        async def run() -> None:
            server = build_public_hosted_mcp_server(create_default_registry())
            async with Client(server) as client:
                listed = await client.list_tools()
                self.assertEqual({tool.name for tool in listed.tools}, set(TOOL_NAMES))
                self.assertEqual(len(listed.tools), 9)
                self.assertNotIn("deep_research_ai_projects", {tool.name for tool in listed.tools})
                for tool in listed.tools:
                    annotations = tool.annotations
                    self.assertIsNotNone(annotations)
                    assert annotations is not None
                    self.assertIs(annotations.read_only_hint, True)
                    self.assertIs(annotations.destructive_hint, False)
                    self.assertIs(annotations.idempotent_hint, True)
        asyncio.run(run())

    def test_public_hosted_instructions_make_premium_boundary_explicit(self) -> None:
        self.assertIn("nine standard read-only Radar tools", PUBLIC_HOSTED_INSTRUCTIONS)
        self.assertIn("does not expose Premium", PUBLIC_HOSTED_INSTRUCTIONS)
        self.assertIn("without requiring login", PUBLIC_HOSTED_INSTRUCTIONS)


if __name__ == "__main__":
    unittest.main()
