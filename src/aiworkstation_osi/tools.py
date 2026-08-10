"""Read-only tool registry and validation for the first capability set."""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Any, Callable, Mapping, Sequence

from .contracts import (
    TOOL_NAMES,
    ExecutionEffects,
    Recommendation,
    Risk,
    ToolResult,
    VerifiedFact,
)
from .errors import (
    InvalidInputError,
    ProviderUnavailableError,
    UnknownToolError,
    UpstreamContractError,
)
from .providers import ProjectIntelligenceProvider, ProviderOutput

ToolHandler = Callable[[Mapping[str, Any]], ToolResult]

MAX_STRUCTURED_DEPTH = 6
MAX_STRUCTURED_NODES = 200
MAX_STRUCTURED_CONTAINER_ITEMS = 50
MAX_STRUCTURED_KEY_LENGTH = 128
MAX_STRUCTURED_STRING_LENGTH = 1_000


def _reject_unknown_fields(payload: Mapping[str, Any], allowed: set[str]) -> None:
    unexpected = sorted(set(payload) - allowed)
    if unexpected:
        raise InvalidInputError(
            "Request contains unsupported fields",
            details={"unsupported_fields": unexpected, "allowed_fields": sorted(allowed)},
        )


def _required_text(payload: Mapping[str, Any], field: str, *, max_length: int = 4_000) -> str:
    raw = payload.get(field)
    if raw is not None and not isinstance(raw, str):
        raise InvalidInputError(f"{field} must be a string", details={"field": field})
    value = str(raw or "").strip()
    if not value:
        raise InvalidInputError(f"{field} is required", details={"field": field})
    if len(value) > max_length:
        raise InvalidInputError(
            f"{field} exceeds the maximum length of {max_length}",
            details={"field": field, "max_length": max_length},
        )
    return value


def _enum_value(
    payload: Mapping[str, Any],
    field: str,
    *,
    allowed: tuple[str, ...],
    default: str,
) -> str:
    raw = payload.get(field, default)
    if not isinstance(raw, str) or raw not in allowed:
        raise InvalidInputError(
            f"{field} must be one of: {', '.join(allowed)}",
            details={"field": field, "allowed": list(allowed)},
        )
    return raw


def _locale(payload: Mapping[str, Any]) -> str:
    return _enum_value(payload, "locale", allowed=("zh", "en"), default="en")


def _string_list(
    payload: Mapping[str, Any],
    field: str,
    *,
    minimum: int = 0,
    maximum: int = 20,
    item_max_length: int = 256,
) -> list[str]:
    raw = payload.get(field)
    if raw is None:
        values: list[str] = []
    elif isinstance(raw, Sequence) and not isinstance(raw, (str, bytes, bytearray)):
        if any(not isinstance(item, str) for item in raw):
            raise InvalidInputError(f"{field} must be an array of strings", details={"field": field})
        values = [item.strip() for item in raw if item.strip()]
    else:
        raise InvalidInputError(f"{field} must be an array of strings", details={"field": field})
    values = list(dict.fromkeys(values))
    if not minimum <= len(values) <= maximum:
        raise InvalidInputError(
            f"{field} must contain between {minimum} and {maximum} unique values",
            details={"field": field, "minimum": minimum, "maximum": maximum},
        )
    if any(len(item) > item_max_length for item in values):
        raise InvalidInputError(
            f"{field} contains a value longer than {item_max_length}",
            details={"field": field, "item_max_length": item_max_length},
        )
    return values


def _structured_value(
    value: Any,
    *,
    field: str,
    location: str,
    depth: int,
    counter: list[int],
) -> Any:
    if depth > MAX_STRUCTURED_DEPTH:
        raise InvalidInputError(
            f"{field} exceeds the maximum nesting depth of {MAX_STRUCTURED_DEPTH}",
            details={"field": field, "location": location, "max_depth": MAX_STRUCTURED_DEPTH},
        )
    counter[0] += 1
    if counter[0] > MAX_STRUCTURED_NODES:
        raise InvalidInputError(
            f"{field} exceeds the maximum structured value size",
            details={"field": field, "max_nodes": MAX_STRUCTURED_NODES},
        )

    if isinstance(value, Mapping):
        if len(value) > MAX_STRUCTURED_CONTAINER_ITEMS:
            raise InvalidInputError(
                f"{field} contains too many object entries",
                details={
                    "field": field,
                    "location": location,
                    "maximum": MAX_STRUCTURED_CONTAINER_ITEMS,
                },
            )
        result: dict[str, Any] = {}
        for raw_key, child in value.items():
            if not isinstance(raw_key, str):
                raise InvalidInputError(
                    f"{field} object keys must be strings",
                    details={"field": field, "location": location},
                )
            key = raw_key.strip()
            if not key or len(key) > MAX_STRUCTURED_KEY_LENGTH or any(ord(char) < 32 for char in key):
                raise InvalidInputError(
                    f"{field} contains an invalid object key",
                    details={
                        "field": field,
                        "location": location,
                        "max_key_length": MAX_STRUCTURED_KEY_LENGTH,
                    },
                )
            result[key] = _structured_value(
                child,
                field=field,
                location=f"{location}.{key}",
                depth=depth + 1,
                counter=counter,
            )
        return result

    if isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)):
        if len(value) > MAX_STRUCTURED_CONTAINER_ITEMS:
            raise InvalidInputError(
                f"{field} contains too many array items",
                details={
                    "field": field,
                    "location": location,
                    "maximum": MAX_STRUCTURED_CONTAINER_ITEMS,
                },
            )
        return [
            _structured_value(
                child,
                field=field,
                location=f"{location}[{index}]",
                depth=depth + 1,
                counter=counter,
            )
            for index, child in enumerate(value)
        ]

    if isinstance(value, str):
        if len(value) > MAX_STRUCTURED_STRING_LENGTH:
            raise InvalidInputError(
                f"{field} contains a string longer than {MAX_STRUCTURED_STRING_LENGTH}",
                details={
                    "field": field,
                    "location": location,
                    "max_length": MAX_STRUCTURED_STRING_LENGTH,
                },
            )
        return value
    if value is None or isinstance(value, (bool, int)):
        return value
    if isinstance(value, float):
        if not math.isfinite(value):
            raise InvalidInputError(
                f"{field} contains a non-finite number",
                details={"field": field, "location": location},
            )
        return value
    raise InvalidInputError(
        f"{field} must contain only JSON-compatible values",
        details={"field": field, "location": location, "type": type(value).__name__},
    )


def _mapping(payload: Mapping[str, Any], field: str) -> dict[str, Any]:
    raw = payload.get(field)
    if raw is None:
        return {}
    if not isinstance(raw, Mapping):
        raise InvalidInputError(f"{field} must be an object", details={"field": field})
    validated = _structured_value(
        raw,
        field=field,
        location=field,
        depth=0,
        counter=[0],
    )
    assert isinstance(validated, dict)
    return validated


def _constraints(payload: Mapping[str, Any], field: str = "constraints") -> list[dict[str, Any]]:
    """Validate v2 typed constraints while preserving polarity."""
    raw = payload.get(field)
    if raw is None:
        return []
    if isinstance(raw, Mapping):
        raw = [{"id": key, "value": value.get("value") if isinstance(value, Mapping) and "value" in value else value,
                "polarity": (value.get("polarity") or value.get("status") or "required") if isinstance(value, Mapping) else "required"}
               for key, value in raw.items()]
    if not isinstance(raw, Sequence) or isinstance(raw, (str, bytes, bytearray)):
        raise InvalidInputError(f"{field} must be an array of constraint objects", details={"field": field})
    if len(raw) > MAX_STRUCTURED_CONTAINER_ITEMS:
        raise InvalidInputError(f"{field} contains too many constraints", details={"field": field})
    result: list[dict[str, Any]] = []
    seen: set[str] = set()
    for index, item in enumerate(raw):
        if not isinstance(item, Mapping):
            raise InvalidInputError(f"{field}[{index}] must be an object", details={"field": field})
        _reject_unknown_fields(item, {"id", "value", "polarity"})
        identifier = _required_text(item, "id", max_length=128).lower()
        if any(ord(char) < 32 for char in identifier):
            raise InvalidInputError(f"{field}[{index}].id contains control characters", details={"field": field})
        if identifier in seen:
            raise InvalidInputError(f"{field} contains duplicate ids", details={"field": field, "id": identifier})
        seen.add(identifier)
        polarity = _enum_value(item, "polarity", allowed=("required", "preferred", "excluded"), default="required")
        value = _structured_value(item.get("value"), field=field, location=f"{field}[{index}].value", depth=0, counter=[0])
        result.append({"id": identifier, "value": value, "polarity": polarity})
    return result


def _request_id(payload: Mapping[str, Any]) -> str:
    raw = payload.get("request_id")
    if raw is None:
        return ""
    if not isinstance(raw, str):
        raise InvalidInputError("request_id must be a string", details={"field": "request_id"})
    value = raw.strip()
    if len(value) > 128:
        raise InvalidInputError(
            "request_id exceeds the maximum length of 128",
            details={"field": "request_id", "max_length": 128},
        )
    return value


def _provider_output(value: ProviderOutput | Mapping[str, Any] | Any, tool: str) -> ProviderOutput:
    if isinstance(value, ProviderOutput):
        return value
    if isinstance(value, Mapping):
        return ProviderOutput(data=dict(value))
    raise UpstreamContractError(
        "Provider returned an unsupported payload",
        details={"tool": tool, "received_type": type(value).__name__},
    )


def _mock_boundaries(data: Mapping[str, Any]) -> tuple[tuple[str, ...], tuple[Risk, ...]]:
    if not data.get("mock"):
        return (), ()
    return (
        ("M0 is using deterministic fixture data; no live project fact has been verified.",),
        (
            Risk(
                code="MOCK_DATA",
                message="Do not use fixture output for production technology or license decisions.",
                severity="high",
            ),
        ),
    )


@dataclass(frozen=True, slots=True)
class ToolSpec:
    name: str
    description: str
    input_fields: tuple[str, ...]


class ToolRegistry:
    """Validate and invoke the transport-neutral read-only tools."""

    def __init__(self, provider: ProjectIntelligenceProvider) -> None:
        self._provider = provider
        self._handlers: dict[str, ToolHandler] = {
            "search_ai_projects": self._search_ai_projects,
            "get_project_facts": self._get_project_facts,
            "get_license_evidence": self._get_license_evidence,
            "compare_ai_projects": self._compare_ai_projects,
            "find_alternatives": self._find_alternatives,
            "compose_ai_stack": self._compose_ai_stack,
        }

    @property
    def specs(self) -> tuple[ToolSpec, ...]:
        return (
            ToolSpec("search_ai_projects", "Find projects from explicit requirements and constraints.", ("query",)),
            ToolSpec("get_project_facts", "Return current evidence-backed facts for one project.", ("project_id",)),
            ToolSpec("get_license_evidence", "Return license observations without legal conclusions.", ("project_id",)),
            ToolSpec("compare_ai_projects", "Compare two to five projects against explicit criteria.", ("project_ids",)),
            ToolSpec("find_alternatives", "Find candidate alternatives to a named project.", ("project_id",)),
            ToolSpec("compose_ai_stack", "Compose a candidate stack from a business goal and constraints.", ("business_goal",)),
        )

    def invoke(self, tool_name: str, arguments: Mapping[str, Any] | None = None) -> ToolResult:
        if tool_name not in TOOL_NAMES:
            raise UnknownToolError(tool_name)
        if arguments is not None and not isinstance(arguments, Mapping):
            raise InvalidInputError("Tool arguments must be an object")
        handler = self._handlers[tool_name]
        payload = dict(arguments or {})
        try:
            return handler(payload)
        except (InvalidInputError, UpstreamContractError, ProviderUnavailableError):
            raise
        except Exception as exc:  # provider failures must not leak internals
            raise ProviderUnavailableError() from exc

    def _result(
        self,
        tool: str,
        payload: Mapping[str, Any],
        output: ProviderOutput,
        *,
        verified_facts: tuple[VerifiedFact, ...] = (),
        recommendations: tuple[Recommendation, ...] = (),
        unknowns: tuple[str, ...] = (),
        risks: tuple[Risk, ...] = (),
    ) -> ToolResult:
        mock_unknowns, mock_risks = _mock_boundaries(output.data)
        return ToolResult(
            tool=tool,
            data=output.data,
            verified_facts=output.verified_facts + verified_facts,
            recommendations=output.recommendations + recommendations,
            unknowns=output.unknowns + unknowns + mock_unknowns,
            risks=output.risks + risks + mock_risks,
            execution=ExecutionEffects(
                business_data_write=False,
                ephemeral_control_plane_effects=("selector_task_create_or_cancel",)
                if tool in {"search_ai_projects", "find_alternatives", "compose_ai_stack"}
                else (),
            ),
            request_id=_request_id(payload),
        )

    def _search_ai_projects(self, payload: Mapping[str, Any]) -> ToolResult:
        _reject_unknown_fields(payload, {"query", "constraints", "locale", "request_id"})
        request = {
            "query": _required_text(payload, "query"),
            "constraints": _constraints(payload),
            "locale": _locale(payload),
        }
        output = _provider_output(self._provider.search_projects(request), "search_ai_projects")
        return self._result("search_ai_projects", payload, output)

    def _get_project_facts(self, payload: Mapping[str, Any]) -> ToolResult:
        _reject_unknown_fields(payload, {"project_id", "locale", "request_id"})
        request = {
            "project_id": _required_text(payload, "project_id", max_length=256),
            "locale": _locale(payload),
        }
        output = _provider_output(self._provider.get_project_facts(request), "get_project_facts")
        unknowns = () if output.data.get("found", True) else (
            "The requested project was not found in the current provider snapshot.",
        )
        return self._result("get_project_facts", payload, output, unknowns=unknowns)

    def _get_license_evidence(self, payload: Mapping[str, Any]) -> ToolResult:
        _reject_unknown_fields(payload, {"project_id", "locale", "request_id"})
        request = {
            "project_id": _required_text(payload, "project_id", max_length=256),
            "locale": _locale(payload),
        }
        output = _provider_output(self._provider.get_license_evidence(request), "get_license_evidence")
        risks = (
            Risk(
                code="NOT_LEGAL_ADVICE",
                message="License observations are technical evidence, not legal advice.",
                severity="medium",
            ),
        )
        unknowns = () if output.data.get("license") else (
            "No verified license evidence is available for this project.",
        )
        return self._result("get_license_evidence", payload, output, unknowns=unknowns, risks=risks)

    def _compare_ai_projects(self, payload: Mapping[str, Any]) -> ToolResult:
        _reject_unknown_fields(payload, {"project_ids", "criteria", "context", "locale", "request_id"})
        request = {
            "project_ids": _string_list(payload, "project_ids", minimum=2, maximum=5),
            "criteria": _string_list(payload, "criteria", maximum=12),
            "context": _mapping(payload, "context"),
            "locale": _locale(payload),
        }
        output = _provider_output(self._provider.compare_projects(request), "compare_ai_projects")
        recommendations = (
            Recommendation(
                summary="Treat the comparison as a decision aid and verify every blocking requirement before adoption.",
                assumptions=("The provider returned comparable records from one current snapshot.",),
            ),
        )
        return self._result("compare_ai_projects", payload, output, recommendations=recommendations)

    def _find_alternatives(self, payload: Mapping[str, Any]) -> ToolResult:
        _reject_unknown_fields(payload, {"project_id", "constraints", "locale", "request_id"})
        request = {
            "project_id": _required_text(payload, "project_id", max_length=256),
            "constraints": _constraints(payload),
            "locale": _locale(payload),
        }
        output = _provider_output(self._provider.find_alternatives(request), "find_alternatives")
        return self._result("find_alternatives", payload, output)

    def _compose_ai_stack(self, payload: Mapping[str, Any]) -> ToolResult:
        _reject_unknown_fields(
            payload,
            {"business_goal", "constraints", "existing_stack", "locale", "request_id"},
        )
        request = {
            "business_goal": _required_text(payload, "business_goal"),
            "constraints": _constraints(payload),
            "existing_stack": _string_list(payload, "existing_stack", maximum=20),
            "locale": _locale(payload),
        }
        output = _provider_output(self._provider.compose_stack(request), "compose_ai_stack")
        recommendations = (
            Recommendation(
                summary="Validate the proposed components with a small isolated proof of concept before production use.",
                assumptions=("Project compatibility has not yet been tested in the user's environment.",),
            ),
        )
        risks = (
            Risk(
                code="INTEGRATION_NOT_VERIFIED",
                message="A proposed stack can contain individually valid projects that are not mutually compatible.",
                severity="high",
            ),
        )
        return self._result(
            "compose_ai_stack",
            payload,
            output,
            recommendations=recommendations,
            risks=risks,
        )
