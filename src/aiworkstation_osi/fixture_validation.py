"""Validate sanitized public Radar contract captures before they are reviewed.

The validator is offline. It never contacts AI Workstation and never modifies a
capture directory.
"""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any, Mapping, Sequence

from .contract_capture import (
    CAPTURE_SCHEMA_VERSION,
    FIXTURE_SCHEMA_VERSION,
    MAX_LIST_ITEMS,
    MAX_STRING_LENGTH,
    REMOVED_KEYS,
    SAFE_HEADERS,
)
from .http_provider import _project_id, _selector_projects

EXPECTED_FIXTURES = {
    "project-list.json": "project-list",
    "project-detail.json": "project-detail",
    "selector-formal.json": "selector-formal",
    "selector-no-match.json": "selector-no-match",
}
FINGERPRINT_PATTERN = re.compile(r"^sha256:[0-9a-f]{64}$")
MAX_SANITIZED_STRING_LENGTH = MAX_STRING_LENGTH + 80


def _load_json(path: Path, errors: list[str]) -> Mapping[str, Any]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        errors.append(f"missing file: {path.name}")
        return {}
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        errors.append(f"invalid JSON file {path.name}: {exc}")
        return {}
    if not isinstance(payload, Mapping):
        errors.append(f"{path.name} must contain a JSON object")
        return {}
    return payload


def _collect_keys(value: Any) -> set[str]:
    if isinstance(value, Mapping):
        keys = {str(key).lower() for key in value}
        for child in value.values():
            keys.update(_collect_keys(child))
        return keys
    if isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)):
        keys: set[str] = set()
        for child in value:
            keys.update(_collect_keys(child))
        return keys
    return set()


def _check_bounds(value: Any, *, location: str, errors: list[str]) -> None:
    if isinstance(value, Mapping):
        for key, child in value.items():
            _check_bounds(child, location=f"{location}.{key}", errors=errors)
        return
    if isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)):
        if len(value) > MAX_LIST_ITEMS + 1:
            errors.append(f"{location} contains more than the sanitized list limit")
        for index, child in enumerate(value):
            _check_bounds(child, location=f"{location}[{index}]", errors=errors)
        return
    if isinstance(value, str) and len(value) > MAX_SANITIZED_STRING_LENGTH:
        errors.append(f"{location} exceeds the sanitized string limit")


def _snapshot(payload: Mapping[str, Any]) -> str:
    for key in ("snapshot_id", "public_snapshot_id", "current_snapshot_id"):
        value = str(payload.get(key) or "").strip()
        if value:
            return value
    return ""


def _validate_near_matches(
    payload: Mapping[str, Any],
    *,
    scenario: str,
    formal_ids: set[str],
    errors: list[str],
) -> None:
    rows = payload.get("near_matches") or []
    if not isinstance(rows, Sequence) or isinstance(rows, (str, bytes, bytearray)):
        errors.append(f"{scenario}: near_matches must be an array")
        return
    if len(rows) > 3:
        errors.append(f"{scenario}: more than three near matches")
    near_ids: set[str] = set()
    for index, row in enumerate(rows):
        if not isinstance(row, Mapping) or row.get("status") != "near_match":
            errors.append(f"{scenario}: malformed near match at index {index}")
            continue
        project = row.get("project")
        blockers = row.get("blocking_constraints")
        if not isinstance(project, Mapping):
            errors.append(f"{scenario}: near match {index} is missing a project")
            continue
        project_id = _project_id(project)
        if not project_id:
            errors.append(f"{scenario}: near match {index} lacks a stable project ID")
        elif project_id in near_ids:
            errors.append(f"{scenario}: duplicate near match {project_id}")
        else:
            near_ids.add(project_id)
        if (
            not isinstance(blockers, Sequence)
            or isinstance(blockers, (str, bytes, bytearray))
            or len(blockers) != 1
        ):
            errors.append(f"{scenario}: near match {project_id or index} must have exactly one blocker")
            continue
        blocker = blockers[0]
        if not isinstance(blocker, Mapping) or blocker.get("status") not in {"conflict", "unverified"}:
            errors.append(f"{scenario}: near-match blocker is invalid for {project_id or index}")
    if formal_ids and near_ids:
        errors.append(f"{scenario}: formal recommendations and near matches coexist")


def validate_contract_directory(directory: Path) -> dict[str, Any]:
    """Return a deterministic validation report for one capture directory."""

    root = Path(directory)
    errors: list[str] = []
    warnings: list[str] = []
    manifest = _load_json(root / "manifest.json", errors)
    if manifest:
        if manifest.get("schema_version") != CAPTURE_SCHEMA_VERSION:
            errors.append("manifest.json has an unsupported schema_version")
        if manifest.get("locale") not in {"zh", "en"}:
            errors.append("manifest.json locale must be zh or en")
        declared_files = manifest.get("fixture_files")
        if not isinstance(declared_files, Sequence) or isinstance(declared_files, (str, bytes)):
            errors.append("manifest.json fixture_files must be an array")
        elif set(str(value) for value in declared_files) != set(EXPECTED_FIXTURES):
            errors.append("manifest.json fixture_files do not match the required four scenarios")
        sanitization = manifest.get("sanitization")
        if not isinstance(sanitization, Mapping):
            errors.append("manifest.json is missing sanitization metadata")
        else:
            if sanitization.get("stores_query_text") is not False:
                errors.append("manifest.json must declare stores_query_text=false")
            declared_removed = {str(value).lower() for value in sanitization.get("removed_keys") or []}
            if not REMOVED_KEYS.issubset(declared_removed):
                errors.append("manifest.json removed_keys is incomplete")

    fixtures: dict[str, Mapping[str, Any]] = {}
    for filename, scenario in EXPECTED_FIXTURES.items():
        fixture = _load_json(root / filename, errors)
        fixtures[filename] = fixture
        if not fixture:
            continue
        if fixture.get("schema_version") != FIXTURE_SCHEMA_VERSION:
            errors.append(f"{filename} has an unsupported schema_version")
        if fixture.get("scenario") != scenario:
            errors.append(f"{filename} scenario does not match its filename")
        fingerprint = str(fixture.get("request_fingerprint") or "")
        if not FINGERPRINT_PATTERN.fullmatch(fingerprint):
            errors.append(f"{filename} has an invalid request_fingerprint")
        status = fixture.get("status")
        if not isinstance(status, int) or not 200 <= status < 300:
            errors.append(f"{filename} status must be a successful HTTP status")
        headers = fixture.get("headers")
        if not isinstance(headers, Mapping):
            errors.append(f"{filename} headers must be an object")
        else:
            unsafe_headers = sorted({str(key).lower() for key in headers} - SAFE_HEADERS)
            if unsafe_headers:
                errors.append(f"{filename} contains unsafe headers: {unsafe_headers}")
        payload = fixture.get("payload")
        if not isinstance(payload, Mapping):
            errors.append(f"{filename} payload must be an object")
            continue
        forbidden = sorted(_collect_keys(fixture).intersection(REMOVED_KEYS))
        if forbidden:
            errors.append(f"{filename} contains removed keys: {forbidden}")
        _check_bounds(fixture, location=filename, errors=errors)

    list_payload = fixtures.get("project-list.json", {}).get("payload")
    list_snapshot = ""
    list_project_ids: set[str] = set()
    if isinstance(list_payload, Mapping):
        list_snapshot = _snapshot(list_payload)
        if not list_snapshot:
            errors.append("project-list: snapshot identity is missing")
        items = list_payload.get("items")
        if not isinstance(items, Sequence) or isinstance(items, (str, bytes, bytearray)) or not items:
            errors.append("project-list: items must be a non-empty array")
        else:
            for item in items:
                if isinstance(item, Mapping) and _project_id(item):
                    list_project_ids.add(_project_id(item))
            if not list_project_ids:
                errors.append("project-list: no item has a stable project identity")

    detail_payload = fixtures.get("project-detail.json", {}).get("payload")
    if isinstance(detail_payload, Mapping):
        item = detail_payload.get("item")
        if not isinstance(item, Mapping) or not item:
            errors.append("project-detail: item is missing")
        else:
            detail_project_id = _project_id(item)
            if not detail_project_id:
                errors.append("project-detail: stable project identity is missing")
            elif list_project_ids and detail_project_id not in list_project_ids:
                errors.append("project-detail: project identity does not match the captured list")
        detail_snapshot = _snapshot(detail_payload)
        if detail_snapshot and list_snapshot and detail_snapshot != list_snapshot:
            errors.append("project-detail: snapshot identity differs from the project list")
        elif not detail_snapshot:
            warnings.append("project-detail: response has no direct snapshot identity; adapter must rely on exact list resolution")

    formal_payload = fixtures.get("selector-formal.json", {}).get("payload")
    if isinstance(formal_payload, Mapping):
        evidence_status = str(formal_payload.get("evidence_status") or "")
        if evidence_status not in {"available", "partial"}:
            errors.append("selector-formal: evidence_status is unavailable")
        if evidence_status == "partial" and not str(formal_payload.get("notice") or "").strip():
            errors.append("selector-formal: partial evidence requires a public notice")
        formal_rows = _selector_projects(formal_payload)
        formal_ids = {_project_id(row) for row in formal_rows if _project_id(row)}
        if not formal_ids:
            errors.append("selector-formal: expected at least one formal project")
        _validate_near_matches(
            formal_payload,
            scenario="selector-formal",
            formal_ids=formal_ids,
            errors=errors,
        )

    no_match_payload = fixtures.get("selector-no-match.json", {}).get("payload")
    if isinstance(no_match_payload, Mapping):
        evidence_status = str(no_match_payload.get("evidence_status") or "")
        if evidence_status not in {"available", "partial"}:
            errors.append("selector-no-match: evidence_status is unavailable")
        if evidence_status == "partial" and not str(no_match_payload.get("notice") or "").strip():
            errors.append("selector-no-match: partial evidence requires a public notice")
        formal_rows = _selector_projects(no_match_payload)
        formal_ids = {_project_id(row) for row in formal_rows if _project_id(row)}
        if formal_ids:
            errors.append("selector-no-match: impossible-query fixture contains formal projects")
        if not str(no_match_payload.get("no_match_reason") or "").strip():
            errors.append("selector-no-match: explicit no_match_reason is missing")
        _validate_near_matches(
            no_match_payload,
            scenario="selector-no-match",
            formal_ids=formal_ids,
            errors=errors,
        )

    return {
        "schema_version": "osi.public-contract-validation.v1",
        "directory": str(root),
        "ok": not errors,
        "summary": {"errors": len(errors), "warnings": len(warnings)},
        "errors": errors,
        "warnings": warnings,
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="osi-validate-contracts")
    parser.add_argument("--directory", type=Path, required=True)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    report = validate_contract_directory(args.directory)
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0 if report["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
