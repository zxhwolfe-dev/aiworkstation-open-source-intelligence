"""Validate machine-generated GitHub Actions evidence for alpha readiness."""

from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path
from typing import Any, Mapping

EXPECTED_REPOSITORY = "zxhwolfe-dev/aiworkstation-open-source-intelligence"
CI_EVIDENCE_SCHEMA = "osi.ci-evidence.v1"
LIVE_EVIDENCE_SCHEMA = "osi.live-validation-evidence.v1"


def _load_json(path: Path) -> Mapping[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, Mapping):
        raise ValueError(f"{path} must contain a JSON object")
    return payload


def _unreadable(path: Path | None, kind: str, exc: Exception | None = None) -> dict[str, Any]:
    message = f"{kind} evidence was not supplied" if path is None else f"{kind} evidence is unreadable"
    if exc is not None:
        message += f": {exc}"
    return {
        "ok": False,
        "supplied": path is not None,
        "path": str(path.expanduser().resolve()) if path is not None else "",
        "errors": [message],
    }


def validate_ci_evidence(
    path: Path | None,
    *,
    candidate_commit: str,
    expected_repository: str = EXPECTED_REPOSITORY,
) -> dict[str, Any]:
    """Accept CI evidence only when the full 3.10/3.12 matrix completed."""

    if path is None:
        return _unreadable(None, "CI")
    evidence_path = path.expanduser().resolve()
    try:
        payload = _load_json(evidence_path)
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        return _unreadable(path, "CI", exc)

    errors: list[str] = []
    versions = [str(value) for value in payload.get("python_versions") or []]
    run_id = str(payload.get("run_id") or "").strip()
    if payload.get("schema_version") != CI_EVIDENCE_SCHEMA:
        errors.append("CI evidence schema is not supported")
    if payload.get("workflow") != "ci":
        errors.append("CI evidence came from the wrong workflow")
    if str(payload.get("repository") or "") != expected_repository:
        errors.append("CI evidence came from a different repository")
    if not candidate_commit or str(payload.get("commit") or "") != candidate_commit:
        errors.append("CI evidence belongs to a different candidate commit")
    if versions != ["3.10", "3.12"]:
        errors.append("CI evidence does not represent the required Python 3.10/3.12 matrix")
    if payload.get("python310_passed") is not True:
        errors.append("Python 3.10 CI is not proven green")
    if payload.get("python312_passed") is not True:
        errors.append("Python 3.12 CI is not proven green")
    if not run_id.isdigit():
        errors.append("CI workflow run ID is missing or invalid")

    return {
        "ok": not errors,
        "supplied": True,
        "path": str(evidence_path),
        "run_id": run_id,
        "run_attempt": str(payload.get("run_attempt") or ""),
        "candidate_commit": candidate_commit,
        "report_commit": str(payload.get("commit") or ""),
        "python310_passed": payload.get("python310_passed") is True,
        "python312_passed": payload.get("python312_passed") is True,
        "errors": errors,
    }


def _safe_relative(bundle_root: Path, value: Any) -> Path | None:
    text = str(value or "").strip()
    if not text:
        return None
    relative = Path(text)
    if relative.is_absolute():
        return None
    candidate = (bundle_root / relative).resolve()
    try:
        candidate.relative_to(bundle_root.resolve())
    except ValueError:
        return None
    return candidate


def _verify_file_manifest(bundle_root: Path, files: Mapping[str, Any]) -> list[str]:
    errors: list[str] = []
    for relative, expected in files.items():
        path = _safe_relative(bundle_root, relative)
        digest = str(expected or "").strip().lower()
        if path is None:
            errors.append(f"live evidence contains unsafe artifact path: {relative}")
            continue
        if not path.is_file():
            errors.append(f"live validation artifact is missing: {relative}")
            continue
        actual = hashlib.sha256(path.read_bytes()).hexdigest()
        if not re.fullmatch(r"[0-9a-f]{64}", digest) or actual != digest:
            errors.append(f"live validation artifact digest mismatch: {relative}")
    return errors


def validate_live_validation_evidence(
    path: Path | None,
    *,
    candidate_commit: str,
    expected_base_url: str,
    expected_repository: str = EXPECTED_REPOSITORY,
) -> dict[str, Any]:
    """Validate a downloaded live-contract-validation artifact bundle."""

    if path is None:
        return _unreadable(None, "live validation")
    evidence_path = path.expanduser().resolve()
    try:
        payload = _load_json(evidence_path)
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        return _unreadable(path, "live validation", exc)

    errors: list[str] = []
    bundle_root = evidence_path.parent
    run_id = str(payload.get("run_id") or "").strip()
    base_url = str(payload.get("base_url") or "").strip().rstrip("/")
    expected_origin = str(expected_base_url or "").strip().rstrip("/")
    project_id = str(payload.get("project_id") or "").strip()
    checks = payload.get("checks") if isinstance(payload.get("checks"), Mapping) else {}
    required_checks = (
        "probe_en",
        "probe_zh",
        "contract_validate_en",
        "contract_validate_zh",
        "replay_en",
        "replay_zh",
        "forbidden_key_scan",
    )
    files = payload.get("files") if isinstance(payload.get("files"), Mapping) else {}

    if payload.get("schema_version") != LIVE_EVIDENCE_SCHEMA:
        errors.append("live validation evidence schema is not supported")
    if payload.get("workflow") != "live-contract-validation":
        errors.append("live validation evidence came from the wrong workflow")
    if str(payload.get("repository") or "") != expected_repository:
        errors.append("live validation evidence came from a different repository")
    if not candidate_commit or str(payload.get("commit") or "") != candidate_commit:
        errors.append("live validation evidence belongs to a different candidate commit")
    if base_url != expected_origin:
        errors.append("live validation evidence used a different Radar origin")
    if not run_id.isdigit():
        errors.append("live validation workflow run ID is missing or invalid")
    if not re.fullmatch(r"[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+", project_id):
        errors.append("live validation project identity is invalid")
    for check_id in required_checks:
        if checks.get(check_id) is not True:
            errors.append(f"live validation check is not proven green: {check_id}")
    if not files:
        errors.append("live validation artifact digest manifest is missing")
    else:
        errors.extend(_verify_file_manifest(bundle_root, files))

    contracts = payload.get("contracts") if isinstance(payload.get("contracts"), Mapping) else {}
    contracts_en = _safe_relative(bundle_root, contracts.get("en"))
    contracts_zh = _safe_relative(bundle_root, contracts.get("zh"))
    required_contract_files = (
        "manifest.json",
        "project-list.json",
        "project-detail.json",
        "selector-formal.json",
        "selector-no-match.json",
    )
    for locale, directory in (("en", contracts_en), ("zh", contracts_zh)):
        if directory is None or not directory.is_dir():
            errors.append(f"{locale} contract directory from live evidence is unavailable")
            continue
        missing: list[str] = []
        for name in required_contract_files:
            fixture = directory / name
            if not fixture.is_file():
                missing.append(name)
                continue
            relative = fixture.relative_to(bundle_root).as_posix()
            if relative not in files:
                errors.append(f"live validation digest manifest does not cover {relative}")
        if missing:
            errors.append(f"{locale} contract directory is incomplete: {', '.join(missing)}")

    for required_relative in (
        "probe-en.json",
        "probe-zh.json",
        "replay-en.json",
        "replay-zh.json",
        "SUMMARY.md",
    ):
        if not (bundle_root / required_relative).is_file():
            errors.append(f"live validation bundle is missing {required_relative}")
        elif required_relative not in files:
            errors.append(f"live validation digest manifest does not cover {required_relative}")

    return {
        "ok": not errors,
        "supplied": True,
        "path": str(evidence_path),
        "run_id": run_id,
        "run_attempt": str(payload.get("run_attempt") or ""),
        "candidate_commit": candidate_commit,
        "report_commit": str(payload.get("commit") or ""),
        "base_url": base_url,
        "project_id": project_id,
        "contracts_en": str(contracts_en) if contracts_en is not None else "",
        "contracts_zh": str(contracts_zh) if contracts_zh is not None else "",
        "verified_file_count": len(files),
        "errors": errors,
    }
