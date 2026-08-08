"""Offline provider matching the expanded public Radar browsing contract."""

from __future__ import annotations

from copy import deepcopy
from typing import Any, Mapping

from .providers import MockProjectIntelligenceProvider, ProviderOutput


class FullMockProjectIntelligenceProvider(MockProjectIntelligenceProvider):
    """Keep local examples deterministic while matching live browse semantics."""

    def browse_radar_projects(self, request: Mapping[str, Any]) -> ProviderOutput:
        # The base mock already supports the core filters used in ordinary tests.
        # Extra public filters are intentionally no-ops unless the fixture carries
        # corresponding metadata; this avoids fabricating ranking/topic facts.
        return super().browse_radar_projects(request)

    def browse_radar_skills(self, request: Mapping[str, Any]) -> ProviderOutput:
        skill_id = str(request.get("skill_id") or "").strip().lower()
        if skill_id:
            item = next(
                (
                    deepcopy(row)
                    for row in self._skills
                    if str(row.get("id") or "").strip().lower() == skill_id
                ),
                None,
            )
            if item is None:
                return ProviderOutput(
                    data={"found": False, "skill_id": request.get("skill_id"), "mock": True},
                    unknowns=("The requested Skill is not present in the deterministic mock library.",),
                )
            return ProviderOutput(data={"found": True, "item": item, "mock": True})

        rows = [deepcopy(item) for item in self._skills]
        query = str(request.get("query") or "").strip().lower()
        category = str(request.get("category") or "").strip().lower()
        kind = str(request.get("kind") or "").strip().lower()
        license_value = str(request.get("license") or "").strip().lower()
        installable = bool(request.get("installable", False))
        if query:
            rows = [row for row in rows if query in " ".join(str(value) for value in row.values()).lower()]
        if category:
            rows = [row for row in rows if str(row.get("category") or "").lower() == category]
        if kind:
            rows = [row for row in rows if str(row.get("kind") or "").lower() == kind]
        if license_value:
            rows = [row for row in rows if str(row.get("license") or "").lower() == license_value]
        if installable:
            rows = [row for row in rows if row.get("installable") is True]
        limit = int(request.get("limit") or 20)
        offset = int(request.get("offset") or 0)
        sliced = rows[offset: offset + limit]
        return ProviderOutput(
            data={
                "items": sliced,
                "total": len(rows),
                "limit": limit,
                "offset": offset,
                "has_more": offset + len(sliced) < len(rows),
                "mock": True,
            }
        )
