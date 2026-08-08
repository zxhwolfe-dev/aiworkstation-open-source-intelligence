"""Expanded public tool registry for the one-install Radar product surface."""

from __future__ import annotations

from typing import Any, Mapping

from .errors import InvalidInputError
from .providers import ProjectIntelligenceProvider
from .tools import (
    ToolRegistry,
    ToolSpec,
    _locale,
    _provider_output,
    _reject_unknown_fields,
)


def _optional_text(
    payload: Mapping[str, Any],
    field: str,
    *,
    max_length: int = 256,
) -> str:
    raw = payload.get(field)
    if raw is None:
        return ""
    if not isinstance(raw, str):
        raise InvalidInputError(f"{field} must be a string", details={"field": field})
    value = raw.strip()
    if len(value) > max_length:
        raise InvalidInputError(
            f"{field} exceeds the maximum length of {max_length}",
            details={"field": field, "max_length": max_length},
        )
    return value


def _bounded_int(
    payload: Mapping[str, Any],
    field: str,
    *,
    default: int,
    minimum: int,
    maximum: int,
) -> int:
    raw = payload.get(field, default)
    if isinstance(raw, bool) or not isinstance(raw, int):
        raise InvalidInputError(f"{field} must be an integer", details={"field": field})
    if raw < minimum or raw > maximum:
        raise InvalidInputError(
            f"{field} must be between {minimum} and {maximum}",
            details={"field": field, "minimum": minimum, "maximum": maximum},
        )
    return int(raw)


class FullToolRegistry(ToolRegistry):
    """The six evidence tools plus three compact Radar browsing tools."""

    def __init__(self, provider: ProjectIntelligenceProvider) -> None:
        super().__init__(provider)
        self._handlers.update(
            {
                "get_radar_overview": self._get_radar_overview,
                "browse_radar_projects": self._browse_radar_projects,
                "browse_radar_skills": self._browse_radar_skills,
            }
        )

    @property
    def specs(self) -> tuple[ToolSpec, ...]:
        return super().specs + (
            ToolSpec(
                "get_radar_overview",
                "List the current Radar navigation dimensions such as rankings, collections, categories and scenarios.",
                (),
            ),
            ToolSpec(
                "browse_radar_projects",
                "Browse Radar projects by ranking, collection, category, scenario, search text and public filters.",
                (),
            ),
            ToolSpec(
                "browse_radar_skills",
                "Browse and search the AI Open Source Radar Skills library.",
                (),
            ),
        )

    def _get_radar_overview(self, payload: Mapping[str, Any]):
        _reject_unknown_fields(payload, {"locale", "request_id"})
        request = {"locale": _locale(payload)}
        output = _provider_output(self._provider.get_radar_overview(request), "get_radar_overview")
        return self._result("get_radar_overview", payload, output)

    def _browse_radar_projects(self, payload: Mapping[str, Any]):
        allowed = {
            "query",
            "ranking",
            "collection",
            "category",
            "scenario",
            "use_case",
            "resource_type",
            "license",
            "deployment",
            "layer",
            "limit",
            "offset",
            "locale",
            "request_id",
        }
        _reject_unknown_fields(payload, allowed)
        request = {
            "query": _optional_text(payload, "query", max_length=1000),
            "ranking": _optional_text(payload, "ranking"),
            "collection": _optional_text(payload, "collection"),
            "category": _optional_text(payload, "category"),
            "scenario": _optional_text(payload, "scenario"),
            "use_case": _optional_text(payload, "use_case"),
            "resource_type": _optional_text(payload, "resource_type"),
            "license": _optional_text(payload, "license"),
            "deployment": _optional_text(payload, "deployment"),
            "layer": _optional_text(payload, "layer"),
            "limit": _bounded_int(payload, "limit", default=20, minimum=1, maximum=50),
            "offset": _bounded_int(payload, "offset", default=0, minimum=0, maximum=10000),
            "locale": _locale(payload),
        }
        output = _provider_output(self._provider.browse_radar_projects(request), "browse_radar_projects")
        return self._result("browse_radar_projects", payload, output)

    def _browse_radar_skills(self, payload: Mapping[str, Any]):
        _reject_unknown_fields(
            payload,
            {"query", "category", "limit", "offset", "locale", "request_id"},
        )
        request = {
            "query": _optional_text(payload, "query", max_length=1000),
            "category": _optional_text(payload, "category"),
            "limit": _bounded_int(payload, "limit", default=20, minimum=1, maximum=50),
            "offset": _bounded_int(payload, "offset", default=0, minimum=0, maximum=10000),
            "locale": _locale(payload),
        }
        output = _provider_output(self._provider.browse_radar_skills(request), "browse_radar_skills")
        return self._result("browse_radar_skills", payload, output)
