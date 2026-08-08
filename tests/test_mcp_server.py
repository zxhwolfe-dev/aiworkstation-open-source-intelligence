from __future__ import annotations

import asyncio
import unittest

from mcp import Client

from aiworkstation_osi.app import create_default_registry
from aiworkstation_osi.mcp_server import SERVER_INSTRUCTIONS, build_mcp_server


class MCPServerTests(unittest.TestCase):
    def test_server_instructions_lead_with_safety_and_workflow_boundaries(self) -> None:
        first_window = SERVER_INSTRUCTIONS[:900]
        self.assertIn("read-only", first_window)
        self.assertIn("verified_facts", first_window)
        self.assertIn("Never execute", first_window)
        self.assertIn("get_radar_overview", first_window)
        self.assertIn("browse_radar_projects", first_window)
        self.assertIn("browse_radar_skills", first_window)
        self.assertIn("search_ai_projects", first_window)
        self.assertIn("get_project_facts", first_window)
        self.assertIn("get_license_evidence", first_window)
        self.assertIn("not legal advice", SERVER_INSTRUCTIONS)

    def test_in_memory_client_lists_annotated_read_only_tools_and_calls_browse(self) -> None:
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
                        "get_radar_overview",
                        "browse_radar_projects",
                        "browse_radar_skills",
                    },
                )
                for tool in listed.tools:
                    with self.subTest(tool=tool.name):
                        self.assertIsNotNone(tool.annotations)
                        assert tool.annotations is not None
                        self.assertTrue(tool.annotations.title)
                        self.assertIs(tool.annotations.read_only_hint, True)
                        self.assertIs(tool.annotations.destructive_hint, False)
                        self.assertIs(tool.annotations.idempotent_hint, True)
                        self.assertIs(tool.annotations.open_world_hint, True)

                result = await client.call_tool(
                    "browse_radar_projects",
                    {"ranking": "daily", "limit": 2, "locale": "en"},
                )
                self.assertFalse(result.is_error)
                self.assertIsNotNone(result.structured_content)
                assert result.structured_content is not None
                self.assertEqual(result.structured_content["tool"], "browse_radar_projects")
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
