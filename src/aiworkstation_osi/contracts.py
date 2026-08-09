"""Transport-neutral contracts shared by Skills, MCP adapters and tests."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from typing import Any, Final, Literal, Mapping

TOOL_NAMES: Final[tuple[str, ...]] = (
    "search_ai_projects",
    "get_project_facts",
    "get_license_evidence",
    "compare_ai_projects",
    "find_alternatives",
    "compose_ai_stack",
    "get_radar_overview",
    "browse_radar_projects",
    "browse_radar_skills",
)

# Hosted public product deliberately exposes the same nine data/evidence tools.
# No Premium/server-model tool is part of the current product surface.
HOSTED_TOOL_NAMES: Final[tuple[str, ...]] = TOOL_NAMES

Locale = Literal["zh", "en"]
SourceMode = Literal["required", "preferred", "off"]
ConfidenceLevel = Literal["high", "medium", "low", "unknown"]


def utc_now_iso() -> str:
    """Return an RFC 3339 UTC timestamp with second precision."""

    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


@dataclass(frozen=True, slots=True)
class Evidence:
    """One verifiable source supporting a fact.

    ``excerpt`` must remain a short public-safe observation, never a full copied
    document or an instruction that the model should execute.
    """

    source_url: str
    observed_at: str
    source_type: str = "official_repository"
    excerpt: str = ""
    supports: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class VerifiedFact:
    """A fact that is explicitly separated from model analysis."""

    field: str
    value: Any
    confidence: ConfidenceLevel
    evidence: tuple[Evidence, ...] = ()


@dataclass(frozen=True, slots=True)
class Recommendation:
    """A host-model or rules-engine conclusion, not a source fact."""

    summary: str
    rationale: tuple[str, ...] = ()
    assumptions: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class Risk:
    code: str
    message: str
    severity: Literal["low", "medium", "high"] = "medium"


@dataclass(frozen=True, slots=True)
class ToolResult:
    """Envelope returned by every public tool.

    The four product boundaries are first-class fields: verified facts,
    recommendations, unknowns and risks. Tool-specific structured data belongs
    in ``data`` and must not blur those boundaries.
    """

    tool: str
    data: Mapping[str, Any] = field(default_factory=dict)
    verified_facts: tuple[VerifiedFact, ...] = ()
    recommendations: tuple[Recommendation, ...] = ()
    unknowns: tuple[str, ...] = ()
    risks: tuple[Risk, ...] = ()
    generated_at: str = field(default_factory=utc_now_iso)
    request_id: str = ""
    schema_version: str = "osi.tool-result.v1"

    def to_dict(self) -> dict[str, Any]:
        """Return a JSON-serializable representation."""

        payload = asdict(self)
        payload["data"] = dict(self.data)
        return payload
