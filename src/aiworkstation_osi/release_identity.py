"""Non-secret release identity used to bind Hosted evidence to a deployment."""

from __future__ import annotations

import os
import re

from . import __version__

RELEASE_COMMIT_ENV = "OSI_RELEASE_COMMIT"
_COMMIT_RE = re.compile(r"^[0-9a-fA-F]{40}$")
_SERVER_VERSION_RE = re.compile(r"^([^+]+)\+git\.([0-9a-f]{40})$")


def normalize_release_commit(value: str) -> str:
    commit = str(value or "").strip()
    if not _COMMIT_RE.fullmatch(commit):
        raise ValueError(f"{RELEASE_COMMIT_ENV} must be an exact 40-character Git commit SHA")
    return commit.lower()


def load_release_commit(*, required: bool = True) -> str:
    raw = str(os.getenv(RELEASE_COMMIT_ENV) or "").strip()
    if not raw:
        if required:
            raise ValueError(f"{RELEASE_COMMIT_ENV} is required for Hosted MCP")
        return ""
    return normalize_release_commit(raw)


def hosted_server_version(commit: str) -> str:
    return f"{__version__}+git.{normalize_release_commit(commit)}"


def release_commit_from_server_version(version: str) -> str:
    match = _SERVER_VERSION_RE.fullmatch(str(version or "").strip())
    return match.group(2) if match else ""
