"""AI Workstation Open Source Intelligence core package."""

from .app import create_default_registry, create_registry_from_env, invoke_tool
from .contracts import TOOL_NAMES, ToolResult
from .strict_http_provider import AIWorkstationHttpProvider
from ._version import __version__

__all__ = [
    "AIWorkstationHttpProvider",
    "TOOL_NAMES",
    "ToolResult",
    "create_default_registry",
    "create_registry_from_env",
    "invoke_tool",
    "__version__",
]
