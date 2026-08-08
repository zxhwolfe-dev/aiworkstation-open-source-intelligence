"""OAuth-subject rate-limit decorator for hosted Radar providers."""

from __future__ import annotations

from typing import Any, Mapping

from .hosted_rate_limit import HostedRateLimiter
from .providers import ProjectIntelligenceProvider, ProviderResponse


class HostedRateLimitedProvider:
    """Apply one authenticated-user quota check per public Radar tool call."""

    def __init__(self, delegate: ProjectIntelligenceProvider, limiter: HostedRateLimiter) -> None:
        self.delegate = delegate
        self.limiter = limiter

    def _call(self, tool_name: str, method_name: str, request: Mapping[str, Any]) -> ProviderResponse:
        self.limiter.check_current(tool_name)
        method = getattr(self.delegate, method_name)
        return method(request)

    def search_projects(self, request: Mapping[str, Any]) -> ProviderResponse:
        return self._call("search_ai_projects", "search_projects", request)

    def get_project_facts(self, request: Mapping[str, Any]) -> ProviderResponse:
        return self._call("get_project_facts", "get_project_facts", request)

    def get_license_evidence(self, request: Mapping[str, Any]) -> ProviderResponse:
        return self._call("get_license_evidence", "get_license_evidence", request)

    def compare_projects(self, request: Mapping[str, Any]) -> ProviderResponse:
        return self._call("compare_ai_projects", "compare_projects", request)

    def find_alternatives(self, request: Mapping[str, Any]) -> ProviderResponse:
        return self._call("find_alternatives", "find_alternatives", request)

    def compose_stack(self, request: Mapping[str, Any]) -> ProviderResponse:
        return self._call("compose_ai_stack", "compose_stack", request)

    def get_radar_overview(self, request: Mapping[str, Any]) -> ProviderResponse:
        return self._call("get_radar_overview", "get_radar_overview", request)

    def browse_radar_projects(self, request: Mapping[str, Any]) -> ProviderResponse:
        return self._call("browse_radar_projects", "browse_radar_projects", request)

    def browse_radar_skills(self, request: Mapping[str, Any]) -> ProviderResponse:
        return self._call("browse_radar_skills", "browse_radar_skills", request)
