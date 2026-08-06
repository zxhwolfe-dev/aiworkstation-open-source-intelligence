from __future__ import annotations

import os
import unittest
from unittest.mock import patch

from aiworkstation_osi.app import create_registry_from_env
from aiworkstation_osi.http_provider import AIWorkstationHttpProvider
from aiworkstation_osi.providers import MockProjectIntelligenceProvider


class ApplicationConfigurationTests(unittest.TestCase):
    def test_default_provider_remains_offline_mock(self) -> None:
        with patch.dict(os.environ, {}, clear=True):
            registry = create_registry_from_env()
        self.assertIsInstance(registry._provider, MockProjectIntelligenceProvider)

    def test_http_provider_requires_explicit_opt_in(self) -> None:
        with patch.dict(
            os.environ,
            {
                "OSI_PROVIDER": "http",
                "AIWORKSTATION_RADAR_BASE_URL": "https://example.test",
                "OSI_HTTP_TIMEOUT_SECONDS": "15",
                "OSI_HYDRATE_LIMIT": "3",
            },
            clear=True,
        ):
            registry = create_registry_from_env()
        self.assertIsInstance(registry._provider, AIWorkstationHttpProvider)
        self.assertEqual(registry._provider.base_url, "https://example.test")
        self.assertEqual(registry._provider.timeout, 15.0)
        self.assertEqual(registry._provider.hydrate_limit, 3)

    def test_invalid_provider_configuration_is_rejected(self) -> None:
        with patch.dict(os.environ, {"OSI_PROVIDER": "database"}, clear=True):
            with self.assertRaises(ValueError):
                create_registry_from_env()
        with patch.dict(
            os.environ,
            {"OSI_PROVIDER": "http", "OSI_HTTP_TIMEOUT_SECONDS": "not-a-number"},
            clear=True,
        ):
            with self.assertRaises(ValueError):
                create_registry_from_env()


if __name__ == "__main__":
    unittest.main()
