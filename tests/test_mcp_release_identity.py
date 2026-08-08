from __future__ import annotations

import asyncio
import unittest
from unittest.mock import patch

from mcp import Client

from aiworkstation_osi import __version__
from aiworkstation_osi.app import create_default_registry
from aiworkstation_osi.mcp_server import build_mcp_server


class McpReleaseIdentityTests(unittest.TestCase):
    def test_release_commit_is_visible_through_mcp_server_info(self) -> None:
        async def run() -> None:
            commit = "a" * 40
            with patch.dict("os.environ", {"OSI_RELEASE_COMMIT": commit}, clear=False):
                server = build_mcp_server(create_default_registry())
            async with Client(server) as client:
                self.assertIsNotNone(client.server_info)
                assert client.server_info is not None
                self.assertEqual(client.server_info.version, f"{__version__}+git.{commit}")

        asyncio.run(run())


if __name__ == "__main__":
    unittest.main()
