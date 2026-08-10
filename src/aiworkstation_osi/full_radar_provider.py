"""Full public Radar provider used by the one-install product surface.

The evidence-critical project research methods remain implemented by the
hardened provider. This layer adds read-only browsing over the existing public
Radar overview, project-directory and Skills-library endpoints.
"""

from __future__ import annotations

import os
import urllib.parse
from typing import Any, Mapping, Sequence

from .errors import UpstreamContractError
from .http_provider import (
    DEFAULT_BASE_URL,
    PUBLIC_API_PREFIX,
    JsonTransport,
    _snapshot_id,
)
from .providers import ProviderOutput
from .selector_task_transport import SelectorTaskJsonTransport
from .strict_http_provider import (
    AIWorkstationHttpProvider,
    SafeUrllibJsonTransport,
    _find_internal_fields,
)

_PROJECT_FILTER_FIELDS = (
    "ranking",
    "collection",
    "category",
    "scenario",
    "role",
    "topic",
    "github_topic",
    "radar_topic",
    "use_case",
    "resource_type",
    "license",
    "deployment",
    "layer",
)

_SKILL_FILTER_FIELDS = (
    "category",
    "kind",
    "license",
    "sort",
)


def _require_public_payload(payload: Mapping[str, Any], *, surface: str) -> None:
    internal_fields = sorted(_find_internal_fields(payload))
    if internal_fields:
        raise UpstreamContractError(
            f"{surface} response leaks internal publication fields",
            details={"fields": internal_fields},
        )


def _items(payload: Mapping[str, Any], *, surface: str) -> list[dict[str, Any]]:
    rows = payload.get("items")
    if not isinstance(rows, Sequence) or isinstance(rows, (str, bytes, bytearray)):
        raise UpstreamContractError(f"{surface} response is missing items")
    result: list[dict[str, Any]] = []
    for row in rows:
        if not isinstance(row, Mapping):
            raise UpstreamContractError(f"{surface} response contains a non-object item")
        result.append(dict(row))
    return result


def _total(payload: Mapping[str, Any], items: Sequence[Mapping[str, Any]]) -> int:
    raw = payload.get("total")
    return int(raw) if isinstance(raw, int) and raw >= 0 else len(items)


class FullRadarHttpProvider(AIWorkstationHttpProvider):
    """Hardened project intelligence plus the public Radar browsing surfaces."""

    def __init__(
        self,
        base_url: str = DEFAULT_BASE_URL,
        *,
        transport: JsonTransport | None = None,
        timeout: float = 30.0,
        hydrate_limit: int = 5,
    ) -> None:
        delegate = transport or SafeUrllibJsonTransport(base_url)
        # Keep each individual HTTP request bounded by ``timeout`` while allowing
        # the already-public long-running selector task contract enough total
        # time to queue and finish. The wrapper affects only POST /selector;
        # every read-only browse/detail request is delegated unchanged.
        selector_transport = SelectorTaskJsonTransport(
            delegate,
            task_timeout=max(60.0, float(timeout)),
            max_concurrent=int(os.getenv("OSI_SELECTOR_MAX_CONCURRENT", "8")),
            queue_timeout=float(os.getenv("OSI_SELECTOR_QUEUE_TIMEOUT_SECONDS", "2")),
        )
        super().__init__(
            base_url,
            transport=selector_transport,
            timeout=timeout,
            hydrate_limit=hydrate_limit,
        )

    def get_radar_overview(self, request: Mapping[str, Any]) -> ProviderOutput:
        locale = str(request.get("locale") or "en")
        response = self._request(
            "GET",
            f"{PUBLIC_API_PREFIX}/overview",
            query={"lang": locale},
        )
        if response.status == 404:
            raise UpstreamContractError("Radar overview endpoint is unavailable")
        _require_public_payload(response.payload, surface="Radar overview")
        data = dict(response.payload)
        data.update(
            {
                "source_url": response.url,
                "observed_at": response.observed_at,
                "snapshot_id": _snapshot_id(response.payload),
            }
        )
        return ProviderOutput(data=data)

    def browse_radar_projects(self, request: Mapping[str, Any]) -> ProviderOutput:
        locale = str(request.get("locale") or "en")
        limit = int(request.get("limit") or 20)
        offset = int(request.get("offset") or 0)
        query: dict[str, Any] = {
            "lang": locale,
            "limit": limit,
            "offset": offset,
        }
        text_query = str(request.get("query") or "").strip()
        if text_query:
            query["q"] = text_query
        active_filters: dict[str, str] = {}
        for field in _PROJECT_FILTER_FIELDS:
            value = str(request.get(field) or "").strip()
            if value:
                query[field] = value
                active_filters[field] = value

        response = self._request(
            "GET",
            f"{PUBLIC_API_PREFIX}/projects",
            query=query,
        )
        if response.status == 404:
            raise UpstreamContractError("Radar project directory endpoint is unavailable")
        _require_public_payload(response.payload, surface="Radar project directory")
        items = _items(response.payload, surface="Radar project directory")
        snapshot = _snapshot_id(response.payload)
        if not snapshot:
            raise UpstreamContractError("Radar project directory is missing snapshot_id")
        total = _total(response.payload, items)
        return ProviderOutput(
            data={
                "items": items,
                "total": total,
                "limit": limit,
                "offset": offset,
                "has_more": bool(response.payload.get("has_more"))
                if isinstance(response.payload.get("has_more"), bool)
                else offset + len(items) < total,
                "snapshot_id": snapshot,
                "active_filters": active_filters,
                "query": text_query,
                "curated": response.payload.get("curated"),
                "eligible_total": response.payload.get("eligible_total"),
                "capacity": response.payload.get("capacity"),
                "ranking_policy_version": response.payload.get("ranking_policy_version"),
                "ranking_quality": response.payload.get("ranking_quality"),
                "source_url": response.url,
                "observed_at": response.observed_at,
            }
        )

    def browse_radar_skills(self, request: Mapping[str, Any]) -> ProviderOutput:
        locale = str(request.get("locale") or "en")
        skill_id = str(request.get("skill_id") or "").strip()
        if skill_id:
            encoded = urllib.parse.quote(skill_id, safe="")
            response = self._request(
                "GET",
                f"{PUBLIC_API_PREFIX}/skills/{encoded}",
                query={"lang": locale},
            )
            if response.status == 404:
                return ProviderOutput(
                    data={
                        "found": False,
                        "skill_id": skill_id,
                        "source_url": response.url,
                        "observed_at": response.observed_at,
                    },
                    unknowns=("The requested Skill is not present in the current public Radar Skills library.",),
                )
            _require_public_payload(response.payload, surface="Radar Skill detail")
            item = response.payload.get("item")
            if not isinstance(item, Mapping) or not item:
                raise UpstreamContractError("Radar Skill detail response is missing item")
            return ProviderOutput(
                data={
                    "found": True,
                    "item": dict(item),
                    "source_url": response.url,
                    "observed_at": response.observed_at,
                }
            )

        limit = int(request.get("limit") or 20)
        offset = int(request.get("offset") or 0)
        query: dict[str, Any] = {
            "lang": locale,
            "limit": limit,
            "offset": offset,
            "installable": bool(request.get("installable", False)),
        }
        text_query = str(request.get("query") or "").strip()
        if text_query:
            query["q"] = text_query
        active_filters: dict[str, Any] = {}
        for field in _SKILL_FILTER_FIELDS:
            value = str(request.get(field) or "").strip()
            if value:
                query[field] = value
                active_filters[field] = value
        if request.get("installable") is True:
            active_filters["installable"] = True

        response = self._request(
            "GET",
            f"{PUBLIC_API_PREFIX}/skills",
            query=query,
        )
        if response.status == 404:
            raise UpstreamContractError("Radar Skills library endpoint is unavailable")
        _require_public_payload(response.payload, surface="Radar Skills library")
        items = _items(response.payload, surface="Radar Skills library")
        total = _total(response.payload, items)
        return ProviderOutput(
            data={
                "items": items,
                "total": total,
                "limit": limit,
                "offset": offset,
                "has_more": bool(response.payload.get("has_more"))
                if isinstance(response.payload.get("has_more"), bool)
                else offset + len(items) < total,
                "active_filters": active_filters,
                "query": text_query,
                "source_url": response.url,
                "observed_at": response.observed_at,
            }
        )
