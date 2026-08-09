from __future__ import annotations

import unittest
from unittest.mock import patch

from aiworkstation_osi.hosted_access import load_hosted_access_mode


class HostedAccessTests(unittest.TestCase):
    def test_public_is_default(self) -> None:
        with patch.dict("os.environ", {}, clear=True):
            self.assertEqual(load_hosted_access_mode(), "public")

    def test_oauth_mode_is_rejected_fail_closed(self) -> None:
        with patch.dict("os.environ", {"OSI_HOSTED_ACCESS_MODE": "oauth"}, clear=True):
            with self.assertRaises(ValueError) as context:
                load_hosted_access_mode()
        self.assertIn("server-model/OAuth Hosted modes are disabled", str(context.exception))

    def test_unknown_mode_fails_closed(self) -> None:
        with patch.dict("os.environ", {"OSI_HOSTED_ACCESS_MODE": "member-ish"}, clear=True):
            with self.assertRaises(ValueError):
                load_hosted_access_mode()


if __name__ == "__main__":
    unittest.main()
