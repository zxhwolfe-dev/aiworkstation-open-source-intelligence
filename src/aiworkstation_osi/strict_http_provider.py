"""Hardened public Radar provider used by application and MCP entrypoints.

This layer adds product-level validation on top of the transport-neutral HTTP
adapter without coupling to private ``akaiagents`` modules.
"""

from __future__ import annotations

import json
import re
import urllib.error
import urllib.parse
import urllib.request
from typing import Any, Mapping, Sequence

from .contracts import Evidence, Risk, VerifiedFact
from .errors import ProviderUnavailableError, UpstreamContractError
from .http_provider import (
    DEFAULT_BASE_URL,
    JsonResponse,
    JsonTransport,
    UrllibJsonTransport,
    _project_id,
    _response_time,
    _selector_projects,
)
from .http_provider import (
    AIWorkstationHttpProvider as BaseAIWorkstationHttpProvider,
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
INTERNAL_PUBLIC_FIELDS = {
    "assignment_version",
    "claim_refs",
    "evidence_ids",
    "prompt_version",
    "publication_version",
    "source_hash",
    "validated_version",
}
PROJECT_ID_PATTERN = re.compile(r"^[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+$")
SAFE_SOURCE_PATH_PATTERN = re.compile(r"^[A-Za-z0-9._/ -]{1,240}$")
LICENSE_SOURCE_LABELS = {"license", "licence"}

# These fields are repository/public-release metadata rather than model/editorial
# conclusions. They may be promoted from a validated same-snapshot public detail
# without claim-specific README evidence. Everything else remains public
# projection data unless a stricter direct-evidence rule promotes it.
VERIFIED_METADATA_FIELDS = {
    "project_id",
    "name",
    "repository_url",
    "homepage",
    "languages",
    "stars",
    "updated_at",
    "archived",
}
ANALYSIS_PROJECTION_FIELDS = {
    "summary",
    "deployment",
    "categories",
    "use_cases",
}


class _NoRedirectHandler(urllib.request.HTTPRedirectHandler):
    """Prevent public Radar requests from leaving the configured origin."""

    def redirect_request(
        self,
        req: urllib.request.Request,
        fp: Any,
        code: int,
        msg: str,
        headers: Any,
        newurl: str,
    ) -> None:
        return None


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


def _find_internal_fields(value: Any) -> set[str]:
    if isinstance(value, Mapping):
        found = {str(key) for key in value if str(key) in INTERNAL_PUBLIC_FIELDS}
        for child in value.values():
            found.update(_find_internal_fields(child))
        return found
    if isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)):
        found: set[str] = set()
        for child in value:
            found.update(_find_internal_fields(child))
        return found
    return set()


def _safe_github_evidence_url(project_id: str, row: Mapping[str, Any]) -> str:
    """Build a public official URL for one already-sanitized evidence row."""

    if not PROJECT_ID_PATTERN.fullmatch(project_id):
        return ""
    repository_url = f"https://github.com/{project_id}"

    explicit_url = str(row.get("source_url") or "").strip()
    if explicit_url:
        parsed = urllib.parse.urlparse(explicit_url)
        if (
            parsed.scheme == "https"
            and parsed.hostname == "github.com"
            and not parsed.username
            and not parsed.password
            and not parsed.query
            and not parsed.fragment
        ):
            return explicit_url

    source_path = str(row.get("source_path") or "").strip().replace("\\", "/")
    safe_path = (
        source_path
        and not source_path.startswith("/")
        and ".." not in source_path.split("/")
        and bool(SAFE_SOURCE_PATH_PATTERN.fullmatch(source_path))
    )
    if safe_path:
        return f"{repository_url}/blob/HEAD/{urllib.parse.quote(source_path, safe='/._-')}"
    return repository_url


def _direct_license_evidence(
    *,
    project_id: str,
    transparency: Mapping[str, Any],
    fallback_observed_at: str,
) -> tuple[Evidence, ...]:
    """Return direct public License evidence only; unrelated sources do not count."""

    rows = transparency.get("sources")
    if not isinstance(rows, Sequence) or isinstance(rows, (str, bytes, bytearray)):
        return ()
    observed_at = str(
        transparency.get("source_updated_at")
        or transparency.get("published_at")
        or fallback_observed_at
        or ""
    ).strip()
    evidence: list[Evidence] = []
    seen: set[tuple[str, str]] = set()
    for row in rows:
        if not isinstance(row, Mapping):
            continue
        source_label = str(row.get("source_label") or "").strip().lower()
        if source_label not in LICENSE_SOURCE_LABELS:
            continue
        excerpt = str(row.get("excerpt") or "").strip()
        if not excerpt:
            continue
        source_url = _safe_github_evidence_url(project_id, row)
        if not source_url:
            continue
        key = (source_url, excerpt)
        if key in seen:
            continue
        seen.add(key)
        evidence.append(
            Evidence(
                source_url=source_url,
                observed_at=observed_at or fallback_observed_at,
                source_type="official_license_source",
                excerpt=excerpt,
                supports=("license",),
            )
        )
    return tuple(evidence)


class SafeUrllibJsonTransport(UrllibJsonTransport):
    """Standard-library transport with safe HTTP-error and redirect handling."""

    def _open(self, request: urllib.request.Request, *, timeout: float) -> Any:
        opener = urllib.request.build_opener(
            _NoRedirectHandler(),
            urllib.request.HTTPSHandler(context=self._ssl_context),
        )
        return opener.open(request, timeout=timeout)

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
            response = self._open(request, timeout=timeout)
            try:
                status = int(response.status)
                raw_headers = {key.lower(): value for key, value in response.headers.items()}
                raw = response.read(self.max_response_bytes + 1)
            finally:
                close = getattr(response, "close", None)
                if callable(close):
                    close()
        except urllib.error.HTTPError as exc:
            status = int(exc.code)
            raw_headers = {
                key.lower(): value
                for key, value in (exc.headers.items() if exc.headers is not None else [])
            }
            try:
                raw = exc.read(self.max_response_bytes + 1)
            finally:
                exc.close()
        except (urllib.error.URLError, TimeoutError, OSError) as exc:
            raise ProviderUnavailableError("AI Workstation public Radar request failed") from exc

        if 300 <= status < 400:
            raise UpstreamContractError(
                "AI Workstation public Radar redirects are not allowed",
                details={
                    "url": url,
                    "status": status,
                    "location_present": bool(raw_headers.get("location")),
                },
            )

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
    """Fail-closed provider with strict selector and field-evidence boundaries."""

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
        if 300 <= response.status < 400:
            raise UpstreamContractError(
                "AI Workstation public Radar redirects are not allowed",
                details={"status": response.status, "url": response.url},
            )
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
        internal_fields = sorted(_find_internal_fields(payload))
        if internal_fields:
            raise UpstreamContractError(
                "Selector response leaks internal publication fields",
                details={"fields": internal_fields},
            )

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
            if candidate_id in near_ids:
                raise UpstreamContractError("Selector returned a duplicate near match")
            near_ids.add(candidate_id)
        if near_matches and formal_ids:
            raise UpstreamContractError(
                "Selector mixed near matches with formal recommendations",
                details={
                    "formal_project_ids": sorted(formal_ids),
                    "near_project_ids": sorted(near_ids),
                },
            )
        return response

    def _detail(self, requested_id: str, locale: str) -> ProviderOutput:
        output = super()._detail(requested_id, locale)
        project = output.data.get("project")
        if not output.data.get("found") or not isinstance(project, Mapping):
            return output

        normalized_project = dict(project)
        stable_project_id = _project_id(normalized_project)
        raw_license = normalized_project.get("license")
        normalized_license = normalize_license(raw_license)
        transparency = (
            output.data.get("transparency")
            if isinstance(output.data.get("transparency"), Mapping)
            else {}
        )
        direct_license_evidence = _direct_license_evidence(
            project_id=stable_project_id,
            transparency=transparency,
            fallback_observed_at=str(output.data.get("observed_at") or ""),
        )

        # The base adapter intentionally mirrors the public detail projection.
        # The hardened layer decides which values cross the stronger
        # ``verified_facts`` boundary. Editorial/classification fields stay in
        # ``data.project`` for workflows to inspect but are not facts by virtue
        # of appearing in that JSON alone.
        facts: list[VerifiedFact] = [
            fact
            for fact in output.verified_facts
            if fact.field in VERIFIED_METADATA_FIELDS
        ]
        base_license_fact = next(
            (fact for fact in output.verified_facts if fact.field == "license"),
            None,
        )
        if (
            base_license_fact is not None
            and normalized_license is not None
            and direct_license_evidence
        ):
            facts.append(
                VerifiedFact(
                    field="license",
                    value=normalized_license,
                    confidence=base_license_fact.confidence,
                    evidence=direct_license_evidence,
                )
            )

        unknowns = list(output.unknowns)
        risks = list(output.risks)
        license_verified = normalized_license is not None and bool(direct_license_evidence)
        if not license_verified:
            normalized_project.pop("license", None)
            if normalized_license is None:
                message = "License evidence is unavailable or explicitly marked unknown in the current public detail."
            else:
                message = (
                    "A license label is present, but the current public transparency payload does not expose direct License evidence."
                )
            if message not in unknowns:
                unknowns.append(message)
            risks.append(
                Risk(
                    code="LICENSE_UNVERIFIED",
                    message="Do not infer permission to use or redistribute this project without direct license evidence.",
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

        field_evidence_status: dict[str, str] = {}
        for field in normalized_project:
            if field in VERIFIED_METADATA_FIELDS:
                field_evidence_status[field] = "verified_public_metadata"
            elif field == "license":
                field_evidence_status[field] = "verified_direct_evidence"
            elif field in ANALYSIS_PROJECTION_FIELDS:
                field_evidence_status[field] = "public_projection_only"
            else:
                field_evidence_status[field] = "public_projection_only"
        if "license" not in normalized_project:
            field_evidence_status["license"] = "unknown"

        data = dict(output.data)
        data["project"] = normalized_project
        data["field_evidence_status"] = field_evidence_status
        data["license_evidence_status"] = "verified" if license_verified else "unknown"
        data["license_evidence_count"] = len(direct_license_evidence)
        return ProviderOutput(
            data=data,
            verified_facts=tuple(facts),
            recommendations=output.recommendations,
            unknowns=tuple(dict.fromkeys(unknowns)),
            risks=tuple(risks),
        )

    def get_license_evidence(self, request: Mapping[str, Any]) -> ProviderOutput:
        """Return only license-specific unknowns/risks and direct public evidence."""

        requested_id = str(request.get("project_id") or "")
        locale = str(request.get("locale") or "en")
        detail = self._detail(requested_id, locale)
        project = detail.data.get("project")
        stable_id = _project_id(project) if isinstance(project, Mapping) else requested_id.strip().lower()
        license_facts = tuple(fact for fact in detail.verified_facts if fact.field == "license")
        license_value = license_facts[0].value if license_facts else None
        license_unknowns = tuple(
            value for value in detail.unknowns if "license" in value.lower()
        )
        license_risks = tuple(
            risk
            for risk in detail.risks
            if risk.code in {"LICENSE_UNVERIFIED", "NON_STANDARD_LICENSE"}
        )
        return ProviderOutput(
            data={
                "project_id": stable_id,
                "license": license_value,
                "found": bool(detail.data.get("found")),
                "snapshot_id": detail.data.get("snapshot_id"),
                "source_url": detail.data.get("source_url"),
                "observed_at": detail.data.get("observed_at"),
                "evidence_status": detail.data.get("license_evidence_status") or "unknown",
                "evidence_count": detail.data.get("license_evidence_count") or 0,
            },
            verified_facts=license_facts,
            unknowns=license_unknowns,
            risks=license_risks,
        )

    def find_alternatives(self, request: Mapping[str, Any]) -> ProviderOutput:
        """Resolve aliases before excluding the source project from alternatives."""

        locale = str(request.get("locale") or "en")
        requested_id = str(request.get("project_id") or "")
        source_detail = self._detail(requested_id, locale)
        source_project = source_detail.data.get("project")
        stable_id = (
            _project_id(source_project)
            if isinstance(source_project, Mapping) and _project_id(source_project)
            else requested_id.strip().lower()
        )
        normalized_request = dict(request)
        normalized_request["project_id"] = stable_id
        output = super().find_alternatives(normalized_request)

        alternatives = output.data.get("alternatives")
        filtered = [
            dict(item)
            for item in alternatives or []
            if isinstance(item, Mapping)
            and _project_id(item) not in {stable_id, requested_id.strip().lower()}
        ]
        facts = tuple(
            fact
            for fact in output.verified_facts
            if not fact.field.startswith(f"projects.{stable_id}.")
        )
        data = dict(output.data)
        data["source_project_id"] = stable_id
        data["alternatives"] = filtered
        data["total"] = len(filtered)
        return ProviderOutput(
            data=data,
            verified_facts=facts,
            recommendations=output.recommendations,
            unknowns=output.unknowns,
            risks=output.risks,
        )
