"""Stable, transport-neutral errors for the public tool layer."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping


@dataclass(slots=True)
class ToolError(Exception):
    code: str
    message: str
    retryable: bool = False
    details: Mapping[str, Any] | None = None

    def __str__(self) -> str:
        return f"{self.code}: {self.message}"

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": "osi.error.v1",
            "error": {
                "code": self.code,
                "message": self.message,
                "retryable": self.retryable,
                "details": dict(self.details or {}),
            },
        }


class InvalidInputError(ToolError):
    def __init__(self, message: str, *, details: Mapping[str, Any] | None = None) -> None:
        super().__init__("INVALID_INPUT", message, False, details)


class UnknownToolError(ToolError):
    def __init__(self, tool_name: str) -> None:
        super().__init__(
            "UNKNOWN_TOOL",
            f"Unknown tool: {tool_name}",
            False,
            {"tool": tool_name},
        )


class ProviderUnavailableError(ToolError):
    def __init__(self, message: str = "Project intelligence provider is unavailable") -> None:
        super().__init__("PROVIDER_UNAVAILABLE", message, True)


class UpstreamContractError(ToolError):
    def __init__(self, message: str, *, details: Mapping[str, Any] | None = None) -> None:
        super().__init__("UPSTREAM_CONTRACT_ERROR", message, False, details)
