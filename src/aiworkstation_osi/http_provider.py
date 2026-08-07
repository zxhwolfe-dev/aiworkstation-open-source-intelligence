"""Fail-closed HTTP adapter for AI Workstation's public Open Source Radar.

The adapter uses only public read endpoints. It never imports or executes code
from ``akaiagents`` and never calls maintenance or write routes.
"""

from __future__ import annotations

import json
import ssl
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
from typing import Any, Mapping, Protocol, Sequence

from .contracts import Evidence, Recommendation, Risk, VerifiedFact, utc_now_iso
from .errors import ProviderUnavailableError, UpstreamContractError
from .providers import ProviderOutput

DEFAULT_BASE_URL = "https://aiworkstation.cn"
PUBLIC_API_PREFIX = "/api/v1/ai/githubai"


@dataclass(frozen=True, slots=True)
class JsonResponse:
    status: int
    headers: Mapping[str, str]
    payload: Mapping[str, Any]
    url: str
    observed_at: str


class JsonTransport(Protocol):
    def request(
        self,
        method: str,
        path: str,
        *,
        query: Mapping[str, Any] | None = None,
        body: Mapping[str, Any] | None = None,
        timeout: float = 30.0,
    ) -> JsonResponse: ...


class UrllibJsonTransport:
    """Small standard-library JSON transport with conservative limits."""

    def __init__(
        self,
        base_url: str = DEFAULT_BASE_URL,
        *,
        allow_insecure_http: bool = False,
        max_response_bytes: int = 2_000_000,
        user_agent: str = "aiworkstation-open-source-intelligence/0.1",
    ) -> None:
        normalized = base_url.rstrip("/")
        parsed = urllib.parse.urlparse(normalized)
        localhost = parsed.hostname in {"localhost", "127.0.0.1", "::1"}
        if parsed.scheme not in {"https", "http"} or not parsed.netloc:
            raise ValueError("base_url must be an absolute HTTP(S) URL")
        if parsed.scheme != "https" and not (allow_insecure_http or localhost):
            raise ValueError("plain HTTP is allowed only for localhost or explicit test configuration")
        self.base_url = normalized
        self.max_response_bytes = max_response_bytes
        self.user_agent = user_agent
        self._ssl_context = ssl.create_default_context()

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
        headers = {
            "accept": "application/json",
            "user-agent": self.user_agent,
        }
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
            raw_headers = {key.lower(): value for key, value in exc.headers.items()}
            raw = exc.read(self.max_response_bytes + 1)
        except (urllib.error.URLError, TimeoutError, OSError) as exc:
            raise ProviderUnavailableError("AI Workstation public Radar request failed") from exc

        # Availability errors are not response-contract evidence. Reverse proxies commonly
        # render 5xx responses as HTML, so classify them before attempting JSON decoding.
        # The provider-level status check remains as a compatibility guard for custom
        # transports that return a JsonResponse directly.
        if status >= 500:
            raise ProviderUnavailableError("AI Workstation public Radar is temporarily unavailable")
        if len(raw) > self.max_response_bytes:
            raise UpstreamContractError(
                "AI Workstation response exceeded the configured size limit",
                details={"url": url, "max_response_bytes": self.max_response_bytes},
            )
        try:
            decoded = json.loads(raw.decode("utf-8")) if raw else {}
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
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


def _response_time(headers: Mapping[str, str]) -> str:
    date_header = str(headers.get("date") or "").strip()
    if date_header:
        try:
            parsed = parsedate_to_datetime(date_header)
            if parsed.tzinfo is None:
                parsed = parsed.replace(tzinfo=timezone.utc)
            return parsed.astimezone(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")
        except (TypeError, ValueError, OverflowError):
            pass
    return utc_now_iso()


def _non_empty(value: Any) -> bool:
    return value not in (None, "", [], {}, ())


def _first(mapping: Mapping[str, Any], *keys: str) -> Any:
    for key in keys:
        value = mapping.get(key)
        if _non_empty(value):
            return value
    return None


def _project_id(item: Mapping[str, Any]) -> str:
    direct = _first(item, "project_id", "full_name")
    if direct:
        return str(direct).strip().lower()
    owner = str(item.get("owner") or "").strip()
    repo = str(item.get("repo") or "").strip()
    if owner and repo:
        return f"{owner}/{repo}".lower()
    return str(item.get("id") or "").strip().lower()


def _coverage_level(item: Mapping[str, Any]) -> str:
    interpretation = item.get("interpretation") if isinstance(item.get("interpretation"), Mapping) else {}
    return str(
        _first(interpretation, "coverage_level")
        or _first(item, "coverage_level")
        or ""
    )


def _confidence_from_coverage(coverage: str) -> str:
    upper = coverage.upper()
    if upper.endswith("L2"):
        return "high"
    if upper.endswith("L1"):
        return "medium"
    return "low"


def _snapshot_id(payload: Mapping[str, Any], item: Mapping[str, Any] | None = None) -> str:
    candidates: list[Mapping[str, Any]] = [payload]
    for key in ("catalog_status", "retrieval_status", "publication", "release"):
        value = payload.get(key)
        if isinstance(value, Mapping):
            candidates.append(value)
    if item:
        candidates.append(item)
        interpretation = item.get("interpretation")
        if isinstance(interpretation, Mapping):
            candidates.append(interpretation)
            transparency = interpretation.get("transparency")
            if isinstance(transparency, Mapping):
                candidates.append(transparency)
    for candidate in candidates:
        value = _first(candidate, "snapshot_id", "public_snapshot_id", "current_snapshot_id")
        if value:
            return str(value).strip()
    return ""


def _selector_projects(payload: Mapping[str, Any]) -> list[dict[str, Any]]:
    rows: list[Mapping[str, Any]] = []
    if isinstance(payload.get("items"), Sequence) and not isinstance(payload.get("items"), (str, bytes)):
        rows.extend(item for item in payload["items"] if isinstance(item, Mapping))
    verified = payload.get("verified_answer")
    if isinstance(verified, Mapping) and isinstance(verified.get("project"), Mapping):
        rows.append(verified["project"])
    solution = payload.get("solution")
    if isinstance(solution, Mapping):
        for key in ("primary",):
            value = solution.get(key)
            if isinstance(value, Mapping):
                rows.append(value)
        for key in ("alternatives", "complements"):
            value = solution.get(key)
            if isinstance(value, Sequence) and not isinstance(value, (str, bytes)):
                rows.extend(item for item in value if isinstance(item, Mapping))
    roles = payload.get("project_roles")
    if isinstance(roles, Sequence) and not isinstance(roles, (str, bytes)):
        for role in roles:
            if not isinstance(role, Mapping):
                continue
            projects = role.get("projects")
            if isinstance(projects, Sequence) and not isinstance(projects, (str, bytes)):
                rows.extend(item for item in projects if isinstance(item, Mapping))
    deduplicated: dict[str, dict[str, Any]] = {}
    for row in rows:
        project_id = _project_id(row)
        if project_id:
            deduplicated.setdefault(project_id, dict(row))
    return list(deduplicated.values())


_CONSTRAINT_ALIASES = {
    "self_hosted": "local",
    "self-hosted": "local",
    "web_ui": "webui",
    "web-ui": "webui",
}
_QUERY_CONSTRAINTS = {"local", "docker", "webui", "no_code", "privacy", "chinese", "free"}
_FILTER_CONSTRAINTS = {"deployment", "category", "use_case", "resource_type", "license_name", "layer"}


def _constraint_plan(constraints: Mapping[str, Any]) -> tuple[dict[str, Any], list[str], list[str]]:
    """Return public selector filters, query-native IDs, and unsupported required IDs."""
    filters: dict[str, Any] = {}
    query_ids: list[str] = []
    unsupported: list[str] = []
    required_keys: set[str] = set()
    deferred_filters: dict[str, Any] = {}
    for raw_key, raw_value in constraints.items():
        key = _CONSTRAINT_ALIASES.get(str(raw_key).strip().lower(), str(raw_key).strip().lower())
        if isinstance(raw_value, Mapping):
            status = str(raw_value.get("status") or raw_value.get("polarity") or "required").lower()
            value = raw_value.get("value") or raw_value.get("id") or True
        else:
            rendered = str(raw_value).strip().lower()
            if rendered in {"required", "preferred", "not_required", "off", "unspecified"}:
                status, value = rendered, True
            else:
                status, value = "required", raw_value
        if status in {"preferred", "not_required", "off", "unspecified"}:
            continue
        if status != "required":
            continue
        if key in {"local", "self_hosted"}:
            required_keys.add("local")
        elif key == "docker":
            required_keys.add("docker")
        elif key == "deployment":
            deployment = str(value if value is not True else "").strip().lower()
            if deployment in {"self-hosted", "self_hosted", "on-prem", "on_prem"}:
                deployment = "local"
            if deployment in {"local", "docker"}:
                required_keys.add(deployment)
            else:
                unsupported.append(key)
        elif key in _FILTER_CONSTRAINTS:
            if value is not True and str(value).strip():
                deferred_filters[key] = value
            else:
                unsupported.append(key)
        elif key in _QUERY_CONSTRAINTS:
            query_ids.append(key)
        else:
            unsupported.append(key)
    # A single deployment filter is only a narrowing hint. Preserve every
    # canonical hard ID in the deterministic query contract when requirements
    # overlap (e.g. local + docker).
    if "docker" in required_keys:
        filters["deployment"] = "docker"
    elif "local" in required_keys:
        filters["deployment"] = "local"
    query_ids.extend(sorted(required_keys))
    filters.update(deferred_filters)
    return filters, sorted(set(query_ids)), sorted(set(unsupported))


def _constraint_suffix(constraints: Mapping[str, Any], locale: str) -> str:
    filters, query_ids, unsupported = _constraint_plan(constraints)
    if not query_ids and not filters and not unsupported:
        return ""
    labels = {"local": "self-hosted/local", "webui": "web UI", "no_code": "no-code", "privacy": "privacy", "chinese": "Chinese", "free": "free", "docker": "Docker"}
    rendered = ", ".join(labels.get(key, key) for key in query_ids)
    if filters:
        rendered_parts = ([rendered] if rendered else []) + [f"{key}={value}" for key, value in sorted(filters.items())]
        rendered = ", ".join(rendered_parts)
    suffix = ("required constraints: " if locale != "zh" else "必须约束：") + rendered if rendered else ""
    if unsupported:
        marker = ", ".join(unsupported)
        suffix += ("\nUnsupported required constraints: " if locale != "zh" else "\n不支持的必须约束：") + marker
    return "\n" + suffix


class AIWorkstationHttpProvider:
    """Read-only provider backed by the public AI Workstation Radar API."""

    def __init__(
        self,
        base_url: str = DEFAULT_BASE_URL,
        *,
        transport: JsonTransport | None = None,
        timeout: float = 30.0,
        hydrate_limit: int = 5,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.transport = transport or UrllibJsonTransport(self.base_url)
        self.timeout = timeout
        self.hydrate_limit = max(1, min(int(hydrate_limit), 5))

    def _request(
        self,
        method: str,
        path: str,
        *,
        query: Mapping[str, Any] | None = None,
        body: Mapping[str, Any] | None = None,
    ) -> JsonResponse:
        response = self.transport.request(method, path, query=query, body=body, timeout=self.timeout)
        if response.status >= 500:
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
        filters, _query_ids, unsupported = _constraint_plan(constraints)
        if unsupported:
            raise UpstreamContractError(
                "Unsupported required constraint(s)",
                details={"unsupported_constraints": unsupported},
            )
        response = self._request(
            "POST",
            f"{PUBLIC_API_PREFIX}/selector",
            body={
                "query": query + _constraint_suffix(constraints, locale),
                "filters": filters,
                "lang": locale,
                "use_model": False,
                "client_id": "aiworkstation-osi-mcp-alpha",
            },
        )
        payload = response.payload
        evidence_status = str(payload.get("evidence_status") or "").strip()
        if evidence_status not in {"available", "partial"}:
            raise UpstreamContractError(
                "Selector evidence index is not available",
                details={"evidence_status": evidence_status or "missing"},
            )
        if evidence_status == "partial" and not str(payload.get("notice") or "").strip():
            raise UpstreamContractError("Partial selector evidence is missing a public notice")
        return response

    def _resolve_project(self, requested_id: str, locale: str) -> tuple[str, str]:
        listing = self._request(
            "GET",
            f"{PUBLIC_API_PREFIX}/projects",
            query={"lang": locale, "q": requested_id, "limit": 20, "offset": 0},
        )
        if listing.status == 404:
            return requested_id, ""
        snapshot = _snapshot_id(listing.payload)
        if not snapshot:
            raise UpstreamContractError("Project listing is missing snapshot_id")
        items = listing.payload.get("items")
        if not isinstance(items, Sequence) or isinstance(items, (str, bytes)):
            raise UpstreamContractError("Project listing is missing items")
        normalized = requested_id.strip().lower()
        for item in items:
            if not isinstance(item, Mapping):
                continue
            aliases = {
                _project_id(item),
                str(item.get("id") or "").strip().lower(),
                str(item.get("repo") or "").strip().lower(),
            }
            if normalized in aliases:
                route_id = str(item.get("id") or _project_id(item)).strip()
                return route_id, snapshot
        return requested_id, snapshot

    def _detail(self, requested_id: str, locale: str) -> ProviderOutput:
        route_id, listing_snapshot = self._resolve_project(requested_id, locale)
        encoded = urllib.parse.quote(route_id, safe="")
        response = self._request(
            "GET",
            f"{PUBLIC_API_PREFIX}/projects/{encoded}",
            query={"lang": locale},
        )
        if response.status == 404:
            return ProviderOutput(
                data={
                    "project_id": requested_id,
                    "found": False,
                    "snapshot_id": listing_snapshot,
                    "source_url": response.url,
                    "observed_at": response.observed_at,
                },
                unknowns=("The requested project is not present in the current public Radar release.",),
            )
        item = response.payload.get("item")
        if not isinstance(item, Mapping) or not item:
            raise UpstreamContractError("Project detail response is missing item")
        snapshot = _snapshot_id(response.payload, item) or listing_snapshot
        if not snapshot:
            raise UpstreamContractError("Project detail response is missing snapshot identity")
        if listing_snapshot and snapshot != listing_snapshot:
            raise UpstreamContractError(
                "Project listing and detail snapshot identities do not match",
                details={"listing_snapshot": listing_snapshot, "detail_snapshot": snapshot},
            )
        project_id = _project_id(item)
        if not project_id:
            raise UpstreamContractError("Project detail is missing a stable project identity")
        coverage = _coverage_level(item)
        confidence = _confidence_from_coverage(coverage)
        evidence = Evidence(
            source_url=response.url,
            observed_at=response.observed_at,
            source_type="aiworkstation_public_release",
            excerpt="Validated public Radar project detail.",
        )
        normalized: dict[str, Any] = {
            "project_id": project_id,
            "name": _first(item, "name", "repo"),
            "summary": _first(item, "summary", "description"),
            "repository_url": _first(item, "html_url", "repository_url", "github_url"),
            "homepage": item.get("homepage"),
            "license": _first(item, "license", "license_name", "license_label"),
            "deployment": _first(item, "deployment", "deployment_modes"),
            "languages": _first(item, "languages", "language"),
            "stars": item.get("stars"),
            "updated_at": _first(item, "updated_at", "pushed_at", "last_updated"),
            "categories": item.get("categories"),
            "use_cases": item.get("use_cases"),
            "archived": bool(item.get("archived")),
        }
        normalized = {key: value for key, value in normalized.items() if _non_empty(value) or key == "archived"}
        verified: list[VerifiedFact] = []
        for field, value in normalized.items():
            if field == "archived" or _non_empty(value):
                verified.append(
                    VerifiedFact(
                        field=field,
                        value=value,
                        confidence=confidence,  # type: ignore[arg-type]
                        evidence=(
                            Evidence(
                                source_url=evidence.source_url,
                                observed_at=evidence.observed_at,
                                source_type=evidence.source_type,
                                excerpt=evidence.excerpt,
                                supports=(field,),
                            ),
                        ),
                    )
                )
        unknowns = tuple(
            message
            for field, message in (
                ("license", "License evidence is not available in the current public detail."),
                ("deployment", "Deployment support is not verified in the current public detail."),
                ("updated_at", "Repository update time is not available in the current public detail."),
            )
            if field not in normalized
        )
        risks: list[Risk] = []
        if normalized.get("archived"):
            risks.append(Risk(code="PROJECT_ARCHIVED", message="The public Radar marks this project as archived.", severity="high"))
        interpretation = item.get("interpretation") if isinstance(item.get("interpretation"), Mapping) else {}
        transparency = interpretation.get("transparency") if isinstance(interpretation, Mapping) else {}
        return ProviderOutput(
            data={
                "project": normalized,
                "found": True,
                "snapshot_id": snapshot,
                "coverage_level": coverage,
                "transparency": dict(transparency) if isinstance(transparency, Mapping) else {},
                "source_url": response.url,
                "observed_at": response.observed_at,
            },
            verified_facts=tuple(verified),
            unknowns=unknowns,
            risks=tuple(risks),
        )

    def _hydrate_candidates(
        self,
        candidates: Sequence[Mapping[str, Any]],
        locale: str,
        *,
        exclude: set[str] | None = None,
    ) -> tuple[list[dict[str, Any]], tuple[VerifiedFact, ...], tuple[str, ...], tuple[Risk, ...], str]:
        exclude_ids = {value.lower() for value in (exclude or set())}
        projects: list[dict[str, Any]] = []
        facts: list[VerifiedFact] = []
        unknowns: list[str] = []
        risks: list[Risk] = []
        snapshots: set[str] = set()
        for candidate in candidates:
            candidate_id = _project_id(candidate)
            if not candidate_id or candidate_id in exclude_ids:
                continue
            detail = self._detail(candidate_id, locale)
            if not detail.data.get("found"):
                unknowns.extend(detail.unknowns)
                continue
            snapshot = str(detail.data.get("snapshot_id") or "")
            if snapshot:
                snapshots.add(snapshot)
            project = detail.data.get("project")
            if isinstance(project, Mapping):
                projects.append(dict(project))
            for fact in detail.verified_facts:
                facts.append(
                    VerifiedFact(
                        field=f"projects.{candidate_id}.{fact.field}",
                        value=fact.value,
                        confidence=fact.confidence,
                        evidence=fact.evidence,
                    )
                )
            unknowns.extend(f"{candidate_id}: {value}" for value in detail.unknowns)
            risks.extend(detail.risks)
            if len(projects) >= self.hydrate_limit:
                break
        if len(snapshots) > 1:
            raise UpstreamContractError(
                "Hydrated project details do not share one public snapshot",
                details={"snapshots": sorted(snapshots)},
            )
        return projects, tuple(facts), tuple(unknowns), tuple(risks), next(iter(snapshots), "")

    def search_projects(self, request: Mapping[str, Any]) -> ProviderOutput:
        locale = str(request.get("locale") or "en")
        response = self._selector(
            str(request.get("query") or ""),
            request.get("constraints") if isinstance(request.get("constraints"), Mapping) else {},
            locale,
        )
        candidates = _selector_projects(response.payload)
        projects, facts, unknowns, risks, snapshot = self._hydrate_candidates(candidates, locale)
        no_match_reason = str(response.payload.get("no_match_reason") or "").strip()
        if not projects and not no_match_reason:
            unknowns += ("No verified candidate was returned and no public no-match reason was provided.",)
        return ProviderOutput(
            data={
                "projects": projects,
                "total": len(projects),
                "result_kind": response.payload.get("result_kind"),
                "evidence_status": response.payload.get("evidence_status"),
                "notice": response.payload.get("notice"),
                "no_match_reason": no_match_reason,
                "near_matches": response.payload.get("near_matches") or [],
                "snapshot_id": snapshot or _snapshot_id(response.payload),
                "selector_url": response.url,
                "observed_at": response.observed_at,
            },
            verified_facts=facts,
            unknowns=unknowns,
            risks=risks,
        )

    def get_project_facts(self, request: Mapping[str, Any]) -> ProviderOutput:
        return self._detail(
            str(request.get("project_id") or ""),
            str(request.get("locale") or "en"),
        )

    def get_license_evidence(self, request: Mapping[str, Any]) -> ProviderOutput:
        detail = self._detail(
            str(request.get("project_id") or ""),
            str(request.get("locale") or "en"),
        )
        license_facts = tuple(fact for fact in detail.verified_facts if fact.field == "license")
        license_value = license_facts[0].value if license_facts else None
        return ProviderOutput(
            data={
                "project_id": str(request.get("project_id") or ""),
                "license": license_value,
                "found": bool(detail.data.get("found")),
                "snapshot_id": detail.data.get("snapshot_id"),
                "source_url": detail.data.get("source_url"),
                "observed_at": detail.data.get("observed_at"),
            },
            verified_facts=license_facts,
            unknowns=detail.unknowns if not license_facts else (),
            risks=detail.risks,
        )

    def compare_projects(self, request: Mapping[str, Any]) -> ProviderOutput:
        locale = str(request.get("locale") or "en")
        details = [self._detail(str(project_id), locale) for project_id in request.get("project_ids") or []]
        snapshots = {
            str(detail.data.get("snapshot_id") or "")
            for detail in details
            if detail.data.get("found") and detail.data.get("snapshot_id")
        }
        if len(snapshots) > 1:
            raise UpstreamContractError(
                "Compared projects do not share one public snapshot",
                details={"snapshots": sorted(snapshots)},
            )
        projects = [dict(detail.data["project"]) for detail in details if isinstance(detail.data.get("project"), Mapping)]
        facts: list[VerifiedFact] = []
        unknowns: list[str] = []
        risks: list[Risk] = []
        for detail in details:
            project = detail.data.get("project")
            project_id = _project_id(project) if isinstance(project, Mapping) else str(detail.data.get("project_id") or "unknown")
            for fact in detail.verified_facts:
                facts.append(
                    VerifiedFact(
                        field=f"projects.{project_id}.{fact.field}",
                        value=fact.value,
                        confidence=fact.confidence,
                        evidence=fact.evidence,
                    )
                )
            unknowns.extend(f"{project_id}: {value}" for value in detail.unknowns)
            risks.extend(detail.risks)
        criteria = list(request.get("criteria") or [])
        matrix = {
            project["project_id"]: {criterion: "requires explicit evaluation" for criterion in criteria}
            for project in projects
            if project.get("project_id")
        }
        return ProviderOutput(
            data={
                "projects": projects,
                "criteria": criteria,
                "comparison_matrix": matrix,
                "snapshot_id": next(iter(snapshots), ""),
            },
            verified_facts=tuple(facts),
            unknowns=tuple(unknowns),
            risks=tuple(risks),
        )

    def find_alternatives(self, request: Mapping[str, Any]) -> ProviderOutput:
        locale = str(request.get("locale") or "en")
        project_id = str(request.get("project_id") or "")
        constraints = request.get("constraints") if isinstance(request.get("constraints"), Mapping) else {}
        query = (
            f"找 {project_id} 的开源替代项目，并保持给定约束。"
            if locale == "zh"
            else f"Find open-source alternatives to {project_id} while preserving the given constraints."
        )
        response = self._selector(query, constraints, locale)
        candidates = _selector_projects(response.payload)
        projects, facts, unknowns, risks, snapshot = self._hydrate_candidates(
            candidates,
            locale,
            exclude={project_id},
        )
        return ProviderOutput(
            data={
                "source_project_id": project_id,
                "alternatives": projects,
                "total": len(projects),
                "no_match_reason": response.payload.get("no_match_reason"),
                "near_matches": response.payload.get("near_matches") or [],
                "snapshot_id": snapshot or _snapshot_id(response.payload),
            },
            verified_facts=facts,
            unknowns=unknowns,
            risks=risks,
        )

    def compose_stack(self, request: Mapping[str, Any]) -> ProviderOutput:
        locale = str(request.get("locale") or "en")
        goal = str(request.get("business_goal") or "")
        constraints = request.get("constraints") if isinstance(request.get("constraints"), Mapping) else {}
        existing = list(request.get("existing_stack") or [])
        query = (
            f"使用开源 AI 项目为以下目标组装可执行技术栈：{goal}"
            if locale == "zh"
            else f"Compose an implementable stack of open-source AI projects for this goal: {goal}"
        )
        if existing:
            query += ("\n现有技术栈：" if locale == "zh" else "\nExisting stack: ") + ", ".join(existing)
        response = self._selector(query, constraints, locale)
        candidates = _selector_projects(response.payload)
        projects, facts, unknowns, risks, snapshot = self._hydrate_candidates(candidates, locale)
        recommendation = Recommendation(
            summary=(
                "该方案来自公开雷达的候选组合，组件间兼容性仍需隔离验证。"
                if locale == "zh"
                else "This is a candidate composition from public Radar results; cross-project compatibility still requires isolated testing."
            ),
            assumptions=("Every component remains available in the same current public snapshot.",),
        )
        return ProviderOutput(
            data={
                "business_goal": goal,
                "components": projects,
                "solution": response.payload.get("solution") or {},
                "solution_blueprint": response.payload.get("solution_blueprint") or {},
                "project_roles": response.payload.get("project_roles") or [],
                "gaps": response.payload.get("gaps") or [],
                "snapshot_id": snapshot or _snapshot_id(response.payload),
            },
            verified_facts=facts,
            recommendations=(recommendation,),
            unknowns=unknowns,
            risks=risks,
        )
