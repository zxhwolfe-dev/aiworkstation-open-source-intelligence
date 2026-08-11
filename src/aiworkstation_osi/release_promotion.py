"""Pure release identity and promotion state checks used by the release workflow.

The workflow talks to GitHub and PyPI; this module deliberately only validates
the JSON returned by those services. Keeping the state machine pure makes
rerun behaviour testable without credentials or a live release.
"""

from __future__ import annotations

from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass
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


def promotion_decision(
    payload: Mapping[str, Any],
    *,
    tag: str,
    commit: str,
    expected_assets: Sequence[str],
    release_id: int,
    prerelease: bool,
) -> Literal["publish", "already_public"]:
    """Return the safe final action for a Draft or already-public Release."""

    identity = validate_release(
        payload,
        tag=tag,
        commit=commit,
        expected_assets=expected_assets,
        release_id=release_id,
        prerelease=prerelease if payload.get("draft") is False else None,
    )
    if identity.draft:
        return "publish"
    return "already_public"
