"""Pure release identity and promotion state checks used by the release workflow.

The workflow talks to GitHub and PyPI; this module deliberately only validates
the JSON returned by those services. Keeping the state machine pure makes
rerun behaviour testable without credentials or a live release.
"""

from __future__ import annotations

import hashlib
import io
import re
import tarfile
import zipfile
from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Literal


class ReleasePromotionError(ValueError):
    """A release cannot safely be staged, resumed, or promoted."""


@dataclass(frozen=True)
class ReleaseIdentity:
    release_id: int
    tag_name: str
    target_commitish: str
    draft: bool
    prerelease: bool
    asset_ids: Mapping[str, int]


_CHECKSUM_LINE = re.compile(r"^([0-9a-fA-F]{64})  ([^\s]+)$")
_SAFE_FILENAME = re.compile(r"^[^/\\]+$")


def parse_checksum_manifest(content: str, expected_names: Sequence[str]) -> dict[str, str]:
    """Parse a strict sha256sum manifest before any file is trusted."""

    expected = list(expected_names)
    if len(set(expected)) != len(expected) or any(
        not isinstance(name, str) or not _SAFE_FILENAME.fullmatch(name) or name in {"", ".", ".."}
        or Path(name).is_absolute() or ".." in name
        for name in expected
    ):
        raise ReleasePromotionError("expected checksum filenames are unsafe")
    parsed: dict[str, str] = {}
    lines = content.splitlines()
    if not lines or any(not line.strip() for line in lines):
        raise ReleasePromotionError("checksum manifest is malformed")
    for line in lines:
        match = _CHECKSUM_LINE.fullmatch(line)
        if match is None:
            raise ReleasePromotionError("checksum manifest contains an unsupported record")
        digest, name = match.groups()
        if (
            not _SAFE_FILENAME.fullmatch(name)
            or name in {"", ".", ".."}
            or Path(name).is_absolute()
            or ".." in name
        ):
            raise ReleasePromotionError("checksum manifest contains an unsafe filename")
        if name in parsed:
            raise ReleasePromotionError(f"duplicate checksum filename: {name}")
        parsed[name] = digest.lower()
    if set(parsed) != set(expected):
        raise ReleasePromotionError("checksum manifest file set is not exact")
    return parsed


def verify_checksum_manifest(
    content: str,
    expected_names: Sequence[str],
    files: Mapping[str, bytes],
) -> dict[str, str]:
    """Validate manifest syntax, exact names, and bytes in one fail-closed step."""

    expected = parse_checksum_manifest(content, expected_names)
    if set(files) != set(expected):
        raise ReleasePromotionError("files do not match checksum manifest set")
    for name, digest in expected.items():
        if hashlib.sha256(files[name]).hexdigest() != digest:
            raise ReleasePromotionError(f"checksum mismatch: {name}")
    return expected


def _metadata_fields(content: bytes) -> tuple[str, str]:
    from email import policy
    from email.parser import BytesParser

    metadata = BytesParser(policy=policy.default).parsebytes(content)
    name = metadata.get("Name")
    version = metadata.get("Version")
    if not isinstance(name, str) or not isinstance(version, str):
        raise ReleasePromotionError("package metadata lacks Name or Version")
    return name, version


def validate_wheel_metadata(content: bytes, expected_name: str, expected_version: str) -> None:
    """Require one exact wheel METADATA file with the expected identity."""

    try:
        with zipfile.ZipFile(io.BytesIO(content)) as archive:
            metadata_names = [name for name in archive.namelist() if name.endswith(".dist-info/METADATA")]
            if len(metadata_names) != 1:
                raise ReleasePromotionError("wheel must contain exactly one dist-info/METADATA")
            name, version = _metadata_fields(archive.read(metadata_names[0]))
    except (OSError, zipfile.BadZipFile, KeyError) as exc:
        raise ReleasePromotionError("wheel metadata is unreadable") from exc
    if name != expected_name or version != expected_version:
        raise ReleasePromotionError("wheel Name or Version does not match release")


def validate_sdist_metadata(content: bytes, expected_name: str, expected_version: str) -> None:
    """Require one top-level sdist directory and one matching PKG-INFO."""

    try:
        with tarfile.open(fileobj=io.BytesIO(content), mode="r:*") as archive:
            members = archive.getmembers()
            top_levels = {member.name.split("/", 1)[0] for member in members if member.name}
            root_name = next(iter(top_levels)) if len(top_levels) == 1 else ""
            root_pkg_info = [member for member in members if member.name == f"{root_name}/PKG-INFO"]
            if (
                len(top_levels) != 1
                or len(root_pkg_info) != 1
                or not root_pkg_info[0].isfile()
            ):
                raise ReleasePromotionError("sdist must contain one top-level directory and PKG-INFO")
            extracted = archive.extractfile(root_pkg_info[0])
            if extracted is None:
                raise ReleasePromotionError("sdist PKG-INFO is unreadable")
            name, version = _metadata_fields(extracted.read())
    except (OSError, tarfile.TarError) as exc:
        raise ReleasePromotionError("sdist metadata is unreadable") from exc
    if name != expected_name or version != expected_version:
        raise ReleasePromotionError("sdist Name or Version does not match release")


def _assets(payload: Mapping[str, Any], expected_assets: Sequence[str]) -> dict[str, int]:
    raw = payload.get("assets")
    if not isinstance(raw, list):
        raise ReleasePromotionError("release assets are missing")
    names: list[str] = []
    asset_ids: dict[str, int] = {}
    for item in raw:
        if not isinstance(item, Mapping):
            raise ReleasePromotionError("release contains an invalid asset")
        name = item.get("name")
        asset_id = item.get("id")
        if not isinstance(name, str) or not isinstance(asset_id, int) or asset_id <= 0:
            raise ReleasePromotionError("release asset lacks a valid name or id")
        if name in asset_ids:
            raise ReleasePromotionError(f"duplicate release asset: {name}")
        names.append(name)
        asset_ids[name] = asset_id
    if sorted(names) != sorted(expected_assets):
        raise ReleasePromotionError("release asset set is not exactly the expected set")
    if len(asset_ids) != len(expected_assets):
        raise ReleasePromotionError("release asset count is not exact")
    return asset_ids


def validate_release(
    payload: Mapping[str, Any],
    *,
    tag: str,
    commit: str,
    expected_assets: Sequence[str],
    release_id: int | None = None,
    draft: bool | None = None,
    prerelease: bool | None = None,
) -> ReleaseIdentity:
    """Validate one GitHub Release response and return its stable identity."""

    actual_id = payload.get("id")
    if not isinstance(actual_id, int) or actual_id <= 0:
        raise ReleasePromotionError("release id is missing or invalid")
    if release_id is not None and actual_id != release_id:
        raise ReleasePromotionError("release id changed")
    if payload.get("tag_name") != tag:
        raise ReleasePromotionError("release tag does not match input tag")
    actual_draft = payload.get("draft")
    if not isinstance(actual_draft, bool):
        raise ReleasePromotionError("release draft state is missing")
    if draft is not None and actual_draft is not draft:
        raise ReleasePromotionError("release draft state is unexpected")
    actual_prerelease = payload.get("prerelease")
    if not isinstance(actual_prerelease, bool):
        raise ReleasePromotionError("release prerelease state is missing")
    if prerelease is not None and actual_prerelease is not prerelease:
        raise ReleasePromotionError("release prerelease state is unexpected")
    target = payload.get("target_commitish")
    if not isinstance(target, str) or target.lower() != commit.lower():
        raise ReleasePromotionError("release target_commitish does not match input commit")
    return ReleaseIdentity(
        release_id=actual_id,
        tag_name=tag,
        target_commitish=target,
        draft=actual_draft,
        prerelease=actual_prerelease,
        asset_ids=_assets(payload, expected_assets),
    )


def flatten_releases(payload: Any) -> list[Mapping[str, Any]]:
    """Flatten ``gh api --paginate --slurp`` output."""

    if not isinstance(payload, list):
        raise ReleasePromotionError("releases API response is not a list")
    if all(isinstance(item, Mapping) for item in payload):
        return [item for item in payload if isinstance(item, Mapping)]
    flattened: list[Mapping[str, Any]] = []
    for page in payload:
        if not isinstance(page, list) or not all(isinstance(item, Mapping) for item in page):
            raise ReleasePromotionError("paginated releases response is invalid")
        flattened.extend(item for item in page if isinstance(item, Mapping))
    return flattened


def locate_draft(
    releases: Iterable[Mapping[str, Any]],
    *,
    tag: str,
    commit: str,
    expected_assets: Sequence[str],
) -> ReleaseIdentity | None:
    """Find exactly one matching Draft Release by API identity, never by ref."""

    same_tag = [item for item in releases if item.get("tag_name") == tag]
    public = [item for item in same_tag if item.get("draft") is False]
    if public:
        raise ReleasePromotionError("a published Release already exists for the requested tag")
    candidates = [item for item in same_tag if item.get("draft") is True]
    if len(candidates) > 1:
        raise ReleasePromotionError("multiple Draft Releases match the requested tag")
    if not candidates:
        return None
    return validate_release(
        candidates[0],
        tag=tag,
        commit=commit,
        expected_assets=expected_assets,
        draft=True,
    )


def locate_release(
    releases: Iterable[Mapping[str, Any]],
    *,
    tag: str,
    commit: str,
    expected_assets: Sequence[str],
) -> ReleaseIdentity | None:
    """Locate exactly one release for a tag, whether Draft or public."""

    candidates = [item for item in releases if item.get("tag_name") == tag]
    if len(candidates) > 1:
        raise ReleasePromotionError("multiple Releases match the requested tag")
    if not candidates:
        return None
    return validate_release(
        candidates[0],
        tag=tag,
        commit=commit,
        expected_assets=expected_assets,
    )


def validate_preflight_release(
    payload: Mapping[str, Any],
    *,
    tag: str,
    commit: str,
    expected_assets: Sequence[str],
    release_id: int,
    prerelease: bool,
    tag_commit: str | None,
) -> ReleaseIdentity:
    """Validate Draft/public identity before any downstream promotion starts."""

    is_public = payload.get("draft") is False
    identity = validate_release(
        payload,
        tag=tag,
        commit=commit,
        expected_assets=expected_assets,
        release_id=release_id,
        prerelease=prerelease if is_public else None,
    )
    if identity.draft:
        if tag_commit is not None:
            raise ReleasePromotionError("tag ref exists before Draft promotion")
    elif tag_commit is None or tag_commit.lower() != commit.lower():
        raise ReleasePromotionError("published tag ref does not match input commit")
    return identity


def promotion_decision(
    payload: Mapping[str, Any],
    *,
    tag: str,
    commit: str,
    expected_assets: Sequence[str],
    release_id: int,
    prerelease: bool,
    tag_commit: str | None,
) -> Literal["publish", "already_public"]:
    """Return the safe final action for a Draft or already-public Release."""

    identity = validate_preflight_release(
        payload,
        tag=tag,
        commit=commit,
        expected_assets=expected_assets,
        release_id=release_id,
        prerelease=prerelease,
        tag_commit=tag_commit,
    )
    if identity.draft:
        return "publish"
    return "already_public"
