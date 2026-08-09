from __future__ import annotations

import unittest
from pathlib import Path


class MembershipDocumentationTests(unittest.TestCase):
    def test_membership_contract_keeps_one_source_of_truth(self) -> None:
        root = Path(__file__).resolve().parents[1]
        content = (root / "docs" / "MEMBERSHIP-AND-MONETIZATION.md").read_text(encoding="utf-8")
        self.assertIn("does **not** own a second independent subscription system", content)
        self.assertIn("AI Workstation membership is the intended source of truth", content)
        self.assertIn("OSI_HOSTED_ACCESS_MODE=public", content)
        self.assertIn("no WorkOS/OAuth dependency", content)
        self.assertIn("Paddle", content)
        self.assertIn("automation adapter", content)

    def test_invite_codes_are_never_mcp_credentials(self) -> None:
        root = Path(__file__).resolve().parents[1]
        content = (root / "docs" / "MEMBERSHIP-AND-MONETIZATION.md").read_text(encoding="utf-8")
        self.assertIn("must **never** be used directly", content)
        self.assertIn("an MCP bearer token", content)
        self.assertIn("a normal MCP tool argument", content)
        self.assertIn("first-party AI Workstation web surface", content)


if __name__ == "__main__":
    unittest.main()
