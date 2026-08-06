"""AI Workstation Open Source Intelligence core package."""

from .app import create_default_registry, invoke_tool
from .contracts import TOOL_NAMES, ToolResult

__all__ = ["TOOL_NAMES", "ToolResult", "create_default_registry", "invoke_tool"]
__version__ = "0.1.0"
