"""Hardened public Radar provider used by application and MCP entrypoints.

This layer adds product-level validation on top of the transport-neutral HTTP
adapter without coupling to private ``akaiagents`` modules.
"""

from __future__ import annotations

import json
import urllib.error
import urllib.parse
import urllib.request
from typing import Any, Mapping, Sequence

from .contracts import Risk, VerifiedFact
from .errors import ProviderUnavailableError, UpstreamContractError
from .http_provider import (
    AIWorkstationHttpProvider as BaseAIWorkstationHttpProvider,
    DEFAULT_BASE_URL,
    JsonResponse,
    JsonTransport,
    UrllibJsonTransport,
    _project_id,
    _response_time,
    _selector_projects,
)
from .providers import ProviderOutput

UNKNOWN_LICENSE_VALUES = {
    "",
    "NONE",
    "NOASSERTION",
    "UNKNOWN",
    "UNLICENSED",
    "NOT FOUND",
    "NOT_FOUND",
    "N/A",
    "NA",
    "NULL",
}
NON_STANDARD_LICENSE_VALUES = {"OTHER", "CUSTOM", "PROPRIETARY"}
RETRYABLE_HTTP_STATUSES = {408, 425, 429}


def normalize_license(value: Any) -> str | None:
    """Return a public license observation or ``None`` for unknown sentinels."""

    if isinstance(value, Mapping):
        value = next(
            (
                value.get(key)
                for key in ("spdx_id", "spdx", "key", "name", "label")
                if value.get(key) not in (None, "")
            ),
            None,
        )
    if value is None:
        return None
    rendered = str(value).strip()
    if rendered.upper() in UNKNOWN_LICENSE_VALUES:
        return None
    return rendered or None


class SafeUrllibJsonTransport(UrllibJsonTransport):
    """Standard-library transport with safe HTTP-error and 404 handling."""

    def request(
        self,
        method: str,
        path: str,
        *,
        query: Mapping[str, Any] | None = None,
        body: Mapping[str, Any] | None = None,
        timeout: float = 30.0,
    ) -> JsonResponse:
        encoded_query = urllib.parse.urlencode(
            [(key, value) for key, value in (query or {}).items() if value is not None],
            doseq=True,
        )
        url = self.base_url + "/" + path.lstrip("/")
        if encoded_query:
            url += "?" + encoded_query
        data = json.dumps(body, ensure_ascii=False).encode("utf-8") if body is not None else None
        headers = {"accept": "application/json", "user-agent": self.user_agent}
        if data is not None:
            headers["content-type"] = "application/json"
        request = urllib.request.Request(url, data=data, method=method.upper(), headers=headers)

        try:
            response = urllib.request.urlopen(
                request,
                timeout=timeout,
                context=self._ssl_context if url.startswith("https://") else None,
            )
            status = int(response.status)
            raw_headers = {key.lower(): value for key, value in response.headers.items()}
            raw = response.read(self.max_response_bytes + 1)
        except urllib.error.HTTPError as exc:
            status = int(exc.code)
            raw_headers = {
                key.lower(): value
                for key, value in (exc.headers.items() if exc.headers is not None else [])
            }
            raw = exc.read(self.max_response_bytes + 1)
        except (urllib.error.URLError, TimeoutError, OSError) as exc:
            raise ProviderUnavailableError("AI Workstation public Radar request failed") from exc

        if len(raw) > self.max_response_bytes:
            raise UpstreamContractError(
                "AI Workstation response exceeded the configured size limit",
                details={"url": url, "max_response_bytes": self.max_response_bytes},
            )

        try:
            decoded = json.loads(raw.decode("utf-8")) if raw else {}
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            if status == 404:
                decoded = {}
            else:
                raise UpstreamContractError(
                    "AI Workstation returned invalid JSON",
                    details={"url": url, "status": status},
                ) from exc
        if not isinstance(decoded, Mapping):
            raise UpstreamContractError(
                "AI Workstation returned a non-object JSON payload",
                details={"url": url, "status": status},
            )
        return JsonResponse(
            status=status,
            headers=raw_headers,
            payload=dict(decoded),
            url=url,
            observed_at=_response_time(raw_headers),
        )


class AIWorkstationHttpProvider(BaseAIWorkstationHttpProvider):
    """Fail-closed provider with strict selector and license boundaries."""

    def __init__(
        self,
        base_url: str = DEFAULT_BASE_URL,
        *,
        transport: JsonTransport | None = None,
        timeout: float = 30.0,
        hydrate_limit: int = 5,
    ) -> None:
        if timeout <= 0 or timeout > 240:
            raise ValueError("timeout must be greater than 0 and no more than 240 seconds")
        if hydrate_limit < 1 or hydrate_limit > 5:
            raise ValueError("hydrate_limit must be between 1 and 5")
        super().__init__(
            base_url,
            transport=transport or SafeUrllibJsonTransport(base_url),
            timeout=timeout,
            hydrate_limit=hydrate_limit,
        )

    def _request(
        self,
        method: str,
        path: str,
        *,
        query: Mapping[str, Any] | None = None,
        body: Mapping[str, Any] | None = None,
    ) -> JsonResponse:
        response = self.transport.request(method, path, query=query, body=body, timeout=self.timeout)
        if response.status in RETRYABLE_HTTP_STATUSES or response.status >= 500:
            raise ProviderUnavailableError("AI Workstation public Radar is temporarily unavailable")
        if response.status >= 400 and response.status != 404:
            raise UpstreamContractError(
                "AI Workstation rejected the public Radar request",
                details={"status": response.status, "url": response.url},
            )
        return response

    def _selector(
        self,
        query: str,
        constraints: Mapping[str, Any],
        locale: str,
    ) -> JsonResponse:
        response = super()._selector(query, constraints, locale)
        payload = response.payload
        near_matches = payload.get("near_matches") or []
        if not isinstance(near_matches, Sequence) or isinstance(near_matches, (str, bytes)):
            raise UpstreamContractError("Selector near_matches must be an array")
        if len(near_matches) > 3:
            raise UpstreamContractError("Selector returned more than three near matches")

        formal_ids = {_project_id(item) for item in _selector_projects(payload) if _project_id(item)}
        near_ids: set[str] = set()
        for row in near_matches:
            if not isinstance(row, Mapping) or row.get("status") != "near_match":
                raise UpstreamContractError("Selector returned a malformed near match")
            project = row.get("project")
            blockers = row.get("blocking_constraints")
            if not isinstance(project, Mapping):
                raise UpstreamContractError("Selector near match is missing a project")
            if not isinstance(blockers, Sequence) or isinstance(blockers, (str, bytes)) or len(blockers) != 1:
                raise UpstreamContractError("Selector near match must have exactly one blocker")
            blocker = blockers[0]
            if not isinstance(blocker, Mapping) or blocker.get("status") not in {"conflict", "unverified"}:
                raise UpstreamContractError("Selector near-match blocker is invalid")
            candidate_id = _project_id(project)
            if not candidate_id:
                raise UpstreamContractError("Selector near match is missing a stable project ID")
            near_ids.add(candidate_id)
        overlap = sorted(formal_ids.intersection(near_ids))
        if overlap:
            raise UpstreamContractError(
                "Selector mixed near matches with formal recommendations",
                details={"project_ids": overlap},
            )
        return response

    def _detail(self, requested_id: str, locale: str) -> ProviderOutput:
        output = super()._detail(requested_id, locale)
        project = output.data.get("project")
        if not output.data.get("found") or not isinstance(project, Mapping):
            return output

        normalized_project = dict(project)
        raw_license = normalized_project.get("license")
        normalized_license = normalize_license(raw_license)
        facts: list[VerifiedFact] = []
        for fact in output.verified_facts:
            if fact.field != "license":
                facts.append(fact)
            elif normalized_license is not None:
                facts.append(
                    VerifiedFact(
                        field="license",
                        value=normalized_license,
                        confidence=fact.confidence,
                        evidence=fact.evidence,
                    )
                )

        unknowns = list(output.unknowns)
        risks = list(output.risks)
        if normalized_license is None:
            normalized_project.pop("license", None)
            message = "License evidence is unavailable or explicitly marked unknown in the current public detail."
            if message not in unknowns:
                unknowns.append(message)
            risks.append(
                Risk(
                    code="LICENSE_UNVERIFIED",
                    message="Do not infer permission to use or redistribute this project without license evidence.",
                    severity="high",
                )
            )
        else:
            normalized_project["license"] = normalized_license
            if normalized_license.upper() in NON_STANDARD_LICENSE_VALUES:
                risks.append(
                    Risk(
                        code="NON_STANDARD_LICENSE",
                        message="The observed license label is non-standard and requires manual review.",
                        severity="high",
                    )
                )

        data = dict(output.data)
        data["project"] = normalized_project
        return ProviderOutput(
            data=data,
            verified_facts=tuple(facts),
            recommendations=output.recommendations,
            unknowns=tuple(dict.fromkeys(unknowns)),
            risks=tuple(risks),
        )
