from __future__ import annotations

import asyncio
import unittest

from mcp import Client

from aiworkstation_osi.app import create_default_registry
from aiworkstation_osi.mcp_server import build_mcp_server


class MCPServerTests(unittest.TestCase):
    def test_in_memory_client_lists_and_calls_read_only_tools(self) -> None:
        async def run() -> None:
            server = build_mcp_server(create_default_registry())
            async with Client(server) as client:
                listed = await client.list_tools()
                names = {tool.name for tool in listed.tools}
                self.assertEqual(
                    names,
                    {
                        "search_ai_projects",
                        "get_project_facts",
                        "get_license_evidence",
                        "compare_ai_projects",
                        "find_alternatives",
                        "compose_ai_stack",
                    },
                )
                result = await client.call_tool(
                    "search_ai_projects",
                    {
                        "query": "self-hosted RAG",
                        "constraints": {"docker": "required"},
                        "locale": "en",
                    },
                )
                self.assertFalse(result.is_error)
                self.assertIsNotNone(result.structured_content)
                assert result.structured_content is not None
                self.assertEqual(result.structured_content["tool"], "search_ai_projects")
                self.assertEqual(result.structured_content["schema_version"], "osi.tool-result.v1")

        asyncio.run(run())

    def test_invalid_call_is_returned_as_model_readable_tool_error(self) -> None:
        async def run() -> None:
            server = build_mcp_server(create_default_registry())
            async with Client(server) as client:
                result = await client.call_tool("get_project_facts", {"project_id": ""})
                self.assertTrue(result.is_error)
                self.assertIsNone(result.structured_content)
                rendered = " ".join(getattr(item, "text", "") for item in result.content)
                self.assertIn("INVALID_INPUT", rendered)

        asyncio.run(run())


if __name__ == "__main__":
    unittest.main()
