"""Non-secret release identity used to bind Hosted evidence to a deployment."""

from __future__ import annotations

import os
import re

from . import __version__

RELEASE_COMMIT_ENV = "OSI_RELEASE_COMMIT"
IMAGE_COMMIT_ENV = "OSI_IMAGE_COMMIT"
_COMMIT_RE = re.compile(r"^[0-9a-fA-F]{40}$")
_SERVER_VERSION_RE = re.compile(r"^([^+]+)\+git\.([0-9a-f]{40})$")


def _normalize_commit(value: str, *, field: str) -> str:
    commit = str(value or "").strip()
    if not _COMMIT_RE.fullmatch(commit):
        raise ValueError(f"{field} must be an exact 40-character Git commit SHA")
    return commit.lower()


def normalize_release_commit(value: str) -> str:
    return _normalize_commit(value, field=RELEASE_COMMIT_ENV)


def normalize_image_commit(value: str) -> str:
    return _normalize_commit(value, field=IMAGE_COMMIT_ENV)


def load_release_commit(*, required: bool = True) -> str:
    raw = str(os.getenv(RELEASE_COMMIT_ENV) or "").strip()
    if not raw:
        if required:
            raise ValueError(f"{RELEASE_COMMIT_ENV} is required for Hosted MCP")
        return ""
    return normalize_release_commit(raw)


def load_image_commit(*, required: bool = True) -> str:
    raw = str(os.getenv(IMAGE_COMMIT_ENV) or "").strip()
    if not raw:
        if required:
            raise ValueError(
                f"{IMAGE_COMMIT_ENV} is missing; Hosted MCP must run from a candidate-bound image"
            )
        return ""
    return normalize_image_commit(raw)


def validate_hosted_deployment_identity() -> str:
    """Return the exact Hosted candidate only when runtime and image identities agree."""

    release_commit = load_release_commit(required=True)
    image_commit = load_image_commit(required=True)
    if release_commit != image_commit:
        raise ValueError(
            f"{RELEASE_COMMIT_ENV} does not match the candidate baked into {IMAGE_COMMIT_ENV}"
        )
    return image_commit


def hosted_server_version(commit: str) -> str:
    return f"{__version__}+git.{normalize_release_commit(commit)}"


def release_commit_from_server_version(version: str) -> str:
    match = _SERVER_VERSION_RE.fullmatch(str(version or "").strip())
    return match.group(2) if match else ""
