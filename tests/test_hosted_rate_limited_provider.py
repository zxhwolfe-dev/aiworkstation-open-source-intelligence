from __future__ import annotations

import unittest

from aiworkstation_osi.hosted_rate_limited_provider import HostedRateLimitedProvider
from aiworkstation_osi.providers import ProviderOutput


class Delegate:
    def __init__(self) -> None:
        self.calls = []

    def __getattr__(self, name):
        def call(request):
            self.calls.append((name, dict(request)))
            return ProviderOutput(data={"method": name})
        return call


class Limiter:
    def __init__(self, *, fail: bool = False) -> None:
        self.fail = fail
        self.tools = []

    def check_current(self, tool_name: str) -> None:
        self.tools.append(tool_name)
        if self.fail:
            raise ValueError("RATE_LIMITED")


class HostedRateLimitedProviderTests(unittest.TestCase):
    def test_each_public_provider_method_checks_its_tool_name_before_delegate(self) -> None:
        delegate = Delegate()
        limiter = Limiter()
        provider = HostedRateLimitedProvider(delegate, limiter)
        cases = (
            ("search_projects", "search_ai_projects"),
            ("get_project_facts", "get_project_facts"),
            ("get_license_evidence", "get_license_evidence"),
            ("compare_projects", "compare_ai_projects"),
            ("find_alternatives", "find_alternatives"),
            ("compose_stack", "compose_ai_stack"),
            ("get_radar_overview", "get_radar_overview"),
            ("browse_radar_projects", "browse_radar_projects"),
            ("browse_radar_skills", "browse_radar_skills"),
        )
        for method_name, tool_name in cases:
            with self.subTest(method=method_name):
                output = getattr(provider, method_name)({"locale": "en"})
                self.assertEqual(output.data["method"], method_name)
                self.assertEqual(limiter.tools[-1], tool_name)
                self.assertEqual(delegate.calls[-1][0], method_name)

    def test_rate_limit_failure_prevents_backend_call(self) -> None:
        delegate = Delegate()
        limiter = Limiter(fail=True)
        provider = HostedRateLimitedProvider(delegate, limiter)
        with self.assertRaises(ValueError):
            provider.browse_radar_projects({"locale": "en"})
        self.assertEqual(delegate.calls, [])


if __name__ == "__main__":
    unittest.main()
