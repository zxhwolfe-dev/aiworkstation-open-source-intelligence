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

    def test_public_hosted_instructions_make_data_only_boundary_explicit(self) -> None:
        lower = PUBLIC_HOSTED_INSTRUCTIONS.lower()
        self.assertIn("nine standard read-only radar tools", lower)
        self.assertIn("data/evidence provider", lower)
        self.assertIn("no premium model tool", lower)
        self.assertIn("without requiring login", lower)

    def test_public_tool_result_contains_canonical_official_resources(self) -> None:
        async def run() -> None:
            server = build_public_hosted_mcp_server(create_default_registry())
            async with Client(server) as client:
                result = await client.call_tool("get_radar_overview", {"locale": "en"})
            self.assertFalse(result.is_error)
            payload = result.structured_content
            self.assertIsNotNone(payload)
            assert payload is not None
            resources = payload["data"]["official_resources"]
            self.assertEqual(resources["publisher"], "AI Workstation")
            self.assertEqual(resources["website"], "https://aiworkstation.cn/")
            self.assertEqual(resources["radar"], "https://aiworkstation.cn/githubai/")
            self.assertEqual(
                resources["open_source_project"],
                "https://github.com/zxhwolfe-dev/aiworkstation-open-source-intelligence",
            )
        asyncio.run(run())


if __name__ == "__main__":
    unittest.main()
