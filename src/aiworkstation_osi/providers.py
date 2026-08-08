"""Provider boundary between the public tool layer and Radar data sources."""

from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass, field
from typing import Any, Mapping, Protocol, Sequence

from .contracts import Recommendation, Risk, VerifiedFact


@dataclass(frozen=True, slots=True)
class ProviderOutput:
    """Validated provider output before it enters the public tool envelope."""

    data: Mapping[str, Any] = field(default_factory=dict)
    verified_facts: tuple[VerifiedFact, ...] = ()
    recommendations: tuple[Recommendation, ...] = ()
    unknowns: tuple[str, ...] = ()
    risks: tuple[Risk, ...] = ()


ProviderResponse = ProviderOutput | Mapping[str, Any]


class ProjectIntelligenceProvider(Protocol):
    """Read-only capabilities required by the public product tools."""

    def search_projects(self, request: Mapping[str, Any]) -> ProviderResponse: ...

    def get_project_facts(self, request: Mapping[str, Any]) -> ProviderResponse: ...

    def get_license_evidence(self, request: Mapping[str, Any]) -> ProviderResponse: ...

    def compare_projects(self, request: Mapping[str, Any]) -> ProviderResponse: ...

    def find_alternatives(self, request: Mapping[str, Any]) -> ProviderResponse: ...

    def compose_stack(self, request: Mapping[str, Any]) -> ProviderResponse: ...

    def get_radar_overview(self, request: Mapping[str, Any]) -> ProviderResponse: ...

    def browse_radar_projects(self, request: Mapping[str, Any]) -> ProviderResponse: ...

    def browse_radar_skills(self, request: Mapping[str, Any]) -> ProviderResponse: ...


class MockProjectIntelligenceProvider:
    """Deterministic provider used for contract tests and local examples.

    It intentionally contains no network access and does not represent live
    project intelligence. Production integration uses an explicit HTTP adapter
    over AI Workstation's current healthy public Radar release.
    """

    def __init__(self, projects: Sequence[Mapping[str, Any]] | None = None) -> None:
        default_projects: tuple[Mapping[str, Any], ...] = (
            {
                "project_id": "langgenius/dify",
                "name": "Dify",
                "summary": "Example workflow platform record for M0 tests.",
                "license": "OTHER",
                "deployment": ["self-hosted", "docker"],
                "capabilities": ["workflow", "rag", "web-ui"],
                "categories": ["agent-platform", "rag"],
                "use_cases": ["knowledge-base", "workflow-automation"],
                "collections": ["self-hosted-ai"],
                "verified_at": "2026-08-01T00:00:00Z",
            },
            {
                "project_id": "infiniflow/ragflow",
                "name": "RAGFlow",
                "summary": "Example RAG platform record for M0 tests.",
                "license": "Apache-2.0",
                "deployment": ["self-hosted", "docker"],
                "capabilities": ["rag", "document-processing", "web-ui"],
                "categories": ["rag", "document-ai"],
                "use_cases": ["knowledge-base", "document-qa"],
                "collections": ["self-hosted-ai", "rag-platforms"],
                "verified_at": "2026-08-01T00:00:00Z",
            },
        )
        self._projects = [dict(item) for item in (projects or default_projects)]
        self._skills = [
            {
                "id": "open-source-project-research",
                "name": "Open Source Project Research",
                "category": "research",
                "summary": "Example Skill record for offline tests.",
            },
            {
                "id": "open-source-project-comparison",
                "name": "Open Source Project Comparison",
                "category": "decision-support",
                "summary": "Example Skill record for offline tests.",
            },
        ]

    def _project(self, project_id: str) -> dict[str, Any] | None:
        normalized = project_id.strip().lower()
        return next(
            (deepcopy(item) for item in self._projects if str(item.get("project_id", "")).lower() == normalized),
            None,
        )

    def search_projects(self, request: Mapping[str, Any]) -> ProviderOutput:
        query = str(request.get("query") or "").lower()
        tokens = {token for token in query.replace("-", " ").split() if len(token) > 1}
        rows = []
        for project in self._projects:
            haystack = " ".join(
                [
                    str(project.get("name") or ""),
                    str(project.get("summary") or ""),
                    " ".join(project.get("capabilities") or []),
                    " ".join(project.get("deployment") or []),
                ]
            ).lower()
            if not tokens or any(token in haystack for token in tokens):
                rows.append(deepcopy(project))
        return ProviderOutput(data={"projects": rows, "total": len(rows), "mock": True})

    def get_project_facts(self, request: Mapping[str, Any]) -> ProviderOutput:
        project = self._project(str(request.get("project_id") or ""))
        return ProviderOutput(data={"project": project, "found": project is not None, "mock": True})

    def get_license_evidence(self, request: Mapping[str, Any]) -> ProviderOutput:
        project = self._project(str(request.get("project_id") or ""))
        if project is None:
            return ProviderOutput(
                data={"project_id": request.get("project_id"), "license": None, "found": False, "mock": True}
            )
        return ProviderOutput(
            data={
                "project_id": project["project_id"],
                "license": project.get("license"),
                "found": True,
                "evidence": [],
                "mock": True,
            }
        )

    def compare_projects(self, request: Mapping[str, Any]) -> ProviderOutput:
        project_ids = request.get("project_ids") or []
        rows = [project for project_id in project_ids if (project := self._project(str(project_id))) is not None]
        return ProviderOutput(
            data={"projects": rows, "criteria": list(request.get("criteria") or []), "mock": True}
        )

    def find_alternatives(self, request: Mapping[str, Any]) -> ProviderOutput:
        project_id = str(request.get("project_id") or "").lower()
        rows = [deepcopy(item) for item in self._projects if str(item.get("project_id") or "").lower() != project_id]
        return ProviderOutput(data={"alternatives": rows, "total": len(rows), "mock": True})

    def compose_stack(self, request: Mapping[str, Any]) -> ProviderOutput:
        return ProviderOutput(
            data={
                "business_goal": request.get("business_goal"),
                "components": [deepcopy(item) for item in self._projects[:2]],
                "implementation_steps": [
                    "Validate requirements and deployment constraints.",
                    "Verify each selected project's current facts and license evidence.",
                    "Build and test a minimal integration in an isolated environment.",
                ],
                "mock": True,
            }
        )

    def get_radar_overview(self, request: Mapping[str, Any]) -> ProviderOutput:
        categories = sorted({value for row in self._projects for value in row.get("categories") or []})
        use_cases = sorted({value for row in self._projects for value in row.get("use_cases") or []})
        collections = sorted({value for row in self._projects for value in row.get("collections") or []})
        return ProviderOutput(
            data={
                "locale": request.get("locale") or "en",
                "snapshot_id": "mock-snapshot",
                "stats": {"public_projects": len(self._projects), "skills": len(self._skills)},
                "rankings": [
                    {"id": "daily", "label": "Daily"},
                    {"id": "weekly", "label": "Weekly"},
                    {"id": "monthly", "label": "Monthly"},
                ],
                "collections": [{"id": value, "label": value} for value in collections],
                "categories": [{"id": value, "label": value} for value in categories],
                "scenarios": [{"id": value, "label": value} for value in use_cases],
                "mock": True,
            }
        )

    def browse_radar_projects(self, request: Mapping[str, Any]) -> ProviderOutput:
        rows = [deepcopy(item) for item in self._projects]
        query = str(request.get("query") or "").strip().lower()
        if query:
            rows = [
                row for row in rows
                if query in " ".join(
                    [str(row.get("project_id") or ""), str(row.get("name") or ""), str(row.get("summary") or "")]
                ).lower()
            ]
        for field, source_key in (
            ("category", "categories"),
            ("scenario", "use_cases"),
            ("use_case", "use_cases"),
            ("collection", "collections"),
        ):
            wanted = str(request.get(field) or "").strip().lower()
            if wanted:
                rows = [row for row in rows if wanted in {str(value).lower() for value in row.get(source_key) or []}]
        deployment = str(request.get("deployment") or "").strip().lower()
        if deployment:
            rows = [row for row in rows if deployment in {str(value).lower() for value in row.get("deployment") or []}]
        license_value = str(request.get("license") or "").strip().lower()
        if license_value:
            rows = [row for row in rows if str(row.get("license") or "").lower() == license_value]
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
                "snapshot_id": "mock-snapshot",
                "ranking": request.get("ranking") or "",
                "mock": True,
            }
        )

    def browse_radar_skills(self, request: Mapping[str, Any]) -> ProviderOutput:
        rows = [deepcopy(item) for item in self._skills]
        query = str(request.get("query") or "").strip().lower()
        category = str(request.get("category") or "").strip().lower()
        if query:
            rows = [row for row in rows if query in " ".join(str(value) for value in row.values()).lower()]
        if category:
            rows = [row for row in rows if str(row.get("category") or "").lower() == category]
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
