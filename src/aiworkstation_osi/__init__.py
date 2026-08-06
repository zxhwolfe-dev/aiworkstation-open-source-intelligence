"""AI Workstation Open Source Intelligence core package."""

from .app import create_default_registry, create_registry_from_env, invoke_tool
from .contracts import TOOL_NAMES, ToolResult
from .http_provider import AIWorkstationHttpProvider

__all__ = [
    "AIWorkstationHttpProvider",
    "TOOL_NAMES",
    "ToolResult",
    "create_default_registry",
    "create_registry_from_env",
    "invoke_tool",
]
__version__ = "0.1.0"
