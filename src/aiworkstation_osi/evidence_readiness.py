"""Evidence-first wrapper for external-alpha release readiness.

The core ``osi-readiness`` command deliberately accepts operator attestations.
This wrapper replaces machine-verifiable attestations with candidate-bound
artifacts from GitHub Actions and a real Codex six-tool acceptance run. Human
artifact review remains explicitly human and is never synthesized here.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
from pathlib import Path
from typing import Any, Mapping, Sequence

from .codex_acceptance import WORKFLOW_VERSION, evaluate_ledger, load_ledger
from .contracts import TOOL_NAMES
from .evidence_manifests import (
    EXPECTED_REPOSITORY,
    validate_ci_evidence,
    validate_live_validation_evidence,
)
from .release_readiness import evaluate_release_readiness

CODEX_ACCEPTANCE_SCHEMA = "osi.codex-acceptance.v1"
DEFAULT_RADAR_BASE_URL = "https://aiworkstation.cn"


def _load_json(path: Path) -> Mapping[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, Mapping):
        raise ValueError(f"{path} must contain a JSON object")
    return payload


def _git_head(root: Path) -> str:
    """Return the exact candidate commit; release evidence fails closed without it."""

    try:
        completed = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=root,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
            timeout=15,
            check=False,
        )
    except (OSError, subprocess.TimeoutExpired):
        return ""
    return completed.stdout.strip() if completed.returncode == 0 else ""


def _sha256_file(path: Path) -> str:
    try:
        return hashlib.sha256(path.read_bytes()).hexdigest()
    except OSError:
        return ""


def validate_codex_acceptance_report(
    path: Path | None,
    *,
    root: Path,
    expected_base_url: str = DEFAULT_RADAR_BASE_URL,
) -> dict[str, Any]:
    """Validate that a real live six-tool Codex run belongs to this candidate."""

    errors: list[str] = []
    if path is None:
        return {
            "ok": False,
            "supplied": False,
            "path": "",
            "errors": ["Codex acceptance report was not supplied"],
        }

    report_path = path.expanduser().resolve()
    try:
        payload = _load_json(report_path)
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        return {
            "ok": False,
            "supplied": True,
            "path": str(report_path),
            "errors": [f"Codex acceptance report is unreadable: {exc}"],
        }

    candidate_commit = _git_head(root.resolve())
    report_commit = str(payload.get("commit") or "").strip()
    provider = str(payload.get("provider") or "").strip()
    base_url = str(payload.get("base_url") or "").strip().rstrip("/")
    expected_origin = str(expected_base_url or DEFAULT_RADAR_BASE_URL).strip().rstrip("/")
    reported_ledger = payload.get("ledger") if isinstance(payload.get("ledger"), Mapping) else {}
    required_tools = list(TOOL_NAMES)

    ledger_path_text = str(payload.get("ledger_path") or "").strip()
    ledger_path = Path(ledger_path_text).expanduser() if ledger_path_text else Path()
    ledger_absolute = bool(ledger_path_text) and ledger_path.is_absolute()
    if ledger_absolute:
        ledger_path = ledger_path.resolve()
    actual_events = load_ledger(ledger_path) if ledger_absolute else []
    actual_ledger = evaluate_ledger(actual_events)
    actual_digest = _sha256_file(ledger_path) if ledger_absolute else ""
    reported_digest = str(payload.get("ledger_sha256") or "").strip().lower()

    if payload.get("schema_version") != CODEX_ACCEPTANCE_SCHEMA:
        errors.append("Codex acceptance schema is not supported")
    if payload.get("workflow_version") != WORKFLOW_VERSION:
        errors.append("Codex acceptance workflow version is not supported")
    if payload.get("ok") is not True:
        errors.append("Codex acceptance report did not pass")
    if payload.get("codex_completed") is not True or payload.get("codex_returncode") != 0:
        errors.append("Codex acceptance process did not complete successfully")
    if provider != "http":
        errors.append("Codex acceptance must use the live HTTP provider")
    if base_url != expected_origin:
        errors.append("Codex acceptance used a different Radar origin")
    if not candidate_commit:
        errors.append("candidate Git commit could not be resolved")
    elif report_commit != candidate_commit:
        errors.append("Codex acceptance report belongs to a different candidate commit")
    if not ledger_absolute:
        errors.append("Codex acceptance ledger path must be absolute")
    elif not ledger_path.is_file():
        errors.append("Codex acceptance ledger file is missing")
    if not reported_digest or reported_digest != actual_digest:
        errors.append("Codex acceptance ledger digest does not match the report")
    if dict(reported_ledger) != actual_ledger:
        errors.append("Codex acceptance report ledger summary does not match the ledger file")

    expected_tools = [str(value) for value in actual_ledger.get("expected_tools") or []]
    successful_tools = [str(value) for value in actual_ledger.get("successful_tools") or []]
    missing_tools = [str(value) for value in actual_ledger.get("missing_tools") or []]
    if expected_tools != required_tools:
        errors.append("Codex acceptance expected-tool set does not match the six-tool contract")
    if set(successful_tools) != set(required_tools) or len(successful_tools) != len(required_tools):
        errors.append("Codex acceptance did not prove success for all six tools")
    if missing_tools:
        errors.append("Codex acceptance still reports missing tools")
    success_counts = actual_ledger.get("success_counts") if isinstance(actual_ledger.get("success_counts"), Mapping) else {}
    if any(int(success_counts.get(tool) or 0) < 1 for tool in required_tools):
        errors.append("Codex acceptance ledger lacks a success event for one or more tools")

    return {
        "ok": not errors,
        "supplied": True,
        "path": str(report_path),
        "candidate_commit": candidate_commit,
        "report_commit": report_commit,
        "provider": provider,
        "base_url": base_url,
        "codex_version": str(payload.get("codex_version") or "")[:200],
        "ledger_path": str(ledger_path) if ledger_absolute else ledger_path_text,
        "ledger_sha256": actual_digest,
        "successful_tools": successful_tools,
        "event_count": int(actual_ledger.get("event_count") or 0),
        "errors": errors,
    }


def _mark_machine_check(
    report: dict[str, Any],
    check_id: str,
    *,
    evidence: Mapping[str, Any],
    success_message: str,
    failure_message: str,
) -> None:
    for check in report.get("checks") or []:
        if not isinstance(check, dict) or check.get("id") != check_id:
            continue
        details = check.setdefault("details", {})
        details["operator_attested"] = False
        details["evidence_verified"] = bool(evidence.get("ok"))
        details["evidence_path"] = str(evidence.get("path") or "")
        check["message"] = success_message if evidence.get("ok") else failure_message
        return


def evaluate_evidence_readiness(
    root: Path,
    *,
    contracts_en: Path | None = None,
    contracts_zh: Path | None = None,
    ci_python310_passed: bool = False,
    ci_python312_passed: bool = False,
    ci_evidence: Path | None = None,
    codex_acceptance_report: Path | None = None,
    live_validation_evidence: Path | None = None,
    expected_base_url: str = DEFAULT_RADAR_BASE_URL,
    artifact_reviewed: bool = False,
    live_validation_run_id: str = "",
    reviewer: str = "",
    remote_mcp_tested: bool = False,
    remote_mcp_url: str = "",
    hosted_gateway_protected: bool = False,
) -> dict[str, Any]:
    """Evaluate readiness with machine gates derived from verifiable evidence."""

    repository_root = root.expanduser().resolve()
    candidate_commit = _git_head(repository_root)

    ci_manifest = validate_ci_evidence(
        ci_evidence,
        candidate_commit=candidate_commit,
        expected_repository=EXPECTED_REPOSITORY,
    )
    if ci_evidence is not None:
        effective_ci310 = bool(ci_manifest["ok"] and ci_manifest.get("python310_passed"))
        effective_ci312 = bool(ci_manifest["ok"] and ci_manifest.get("python312_passed"))
    else:
        effective_ci310 = bool(ci_python310_passed)
        effective_ci312 = bool(ci_python312_passed)

    live_manifest = validate_live_validation_evidence(
        live_validation_evidence,
        candidate_commit=candidate_commit,
        expected_base_url=expected_base_url,
        expected_repository=EXPECTED_REPOSITORY,
    )
    if live_validation_evidence is not None:
        if live_manifest["ok"]:
            effective_contracts_en = Path(str(live_manifest["contracts_en"]))
            effective_contracts_zh = Path(str(live_manifest["contracts_zh"]))
            effective_run_id = str(live_manifest["run_id"])
        else:
            effective_contracts_en = None
            effective_contracts_zh = None
            effective_run_id = ""
    else:
        effective_contracts_en = contracts_en
        effective_contracts_zh = contracts_zh
        effective_run_id = str(live_validation_run_id or "").strip()

    codex_evidence = validate_codex_acceptance_report(
        codex_acceptance_report,
        root=repository_root,
        expected_base_url=expected_base_url,
    )
    report = evaluate_release_readiness(
        repository_root,
        contracts_en=effective_contracts_en,
        contracts_zh=effective_contracts_zh,
        ci_python310_passed=effective_ci310,
        ci_python312_passed=effective_ci312,
        codex_tested=bool(codex_evidence["ok"]),
        artifact_reviewed=artifact_reviewed,
        live_validation_run_id=effective_run_id,
        reviewer=reviewer,
        remote_mcp_tested=remote_mcp_tested,
        remote_mcp_url=remote_mcp_url,
        hosted_gateway_protected=hosted_gateway_protected,
    )
    report["machine_evidence"] = {
        "ci": ci_manifest,
        "codex": codex_evidence,
        "live_validation": live_manifest,
    }
    # Backward-compatible alias for tooling created with the first evidence build.
    report["codex_acceptance_evidence"] = codex_evidence

    if ci_evidence is not None:
        _mark_machine_check(
            report,
            "attestation-ci-python310-passed",
            evidence=ci_manifest,
            success_message="Python 3.10 CI is verified by candidate-bound workflow evidence.",
            failure_message="Valid candidate-bound Python 3.10 CI evidence is required.",
        )
        _mark_machine_check(
            report,
            "attestation-ci-python312-passed",
            evidence=ci_manifest,
            success_message="Python 3.12 CI is verified by candidate-bound workflow evidence.",
            failure_message="Valid candidate-bound Python 3.12 CI evidence is required.",
        )

    _mark_machine_check(
        report,
        "attestation-codex-tested",
        evidence=codex_evidence,
        success_message="The real Codex six-tool MCP workflow is verified by candidate-bound acceptance evidence.",
        failure_message="A valid candidate-bound Codex six-tool acceptance report is required.",
    )

    if live_validation_evidence is not None:
        for check in report.get("checks") or []:
            if not isinstance(check, dict) or check.get("id") != "validation-evidence":
                continue
            details = check.setdefault("details", {})
            details["workflow_evidence_verified"] = bool(live_manifest.get("ok"))
            details["workflow_evidence_path"] = str(live_manifest.get("path") or "")
            details["workflow_run_id"] = str(live_manifest.get("run_id") or "")
            if live_manifest.get("ok") and reviewer:
                check["message"] = "Live validation run is candidate-bound and the human artifact reviewer is recorded."
            elif live_manifest.get("ok"):
                check["message"] = "Live validation run is candidate-bound; a named human artifact reviewer is still required."
            else:
                check["message"] = "Valid candidate-bound live validation workflow evidence is required."
            break

    return report


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="osi-evidence-readiness")
    parser.add_argument("--root", type=Path, default=Path.cwd())
    parser.add_argument("--contracts-en", type=Path)
    parser.add_argument("--contracts-zh", type=Path)
    parser.add_argument("--ci-python310-passed", action="store_true")
    parser.add_argument("--ci-python312-passed", action="store_true")
    parser.add_argument("--ci-evidence", type=Path)
    parser.add_argument("--codex-acceptance-report", type=Path)
    parser.add_argument("--live-validation-evidence", type=Path)
    parser.add_argument("--expected-base-url", default=DEFAULT_RADAR_BASE_URL)
    parser.add_argument("--artifact-reviewed", action="store_true")
    parser.add_argument("--live-validation-run-id", default="")
    parser.add_argument("--reviewer", default="")
    parser.add_argument("--remote-mcp-tested", action="store_true")
    parser.add_argument("--remote-mcp-url", default="")
    parser.add_argument("--hosted-gateway-protected", action="store_true")
    parser.add_argument("--output", type=Path)
    parser.add_argument("--require-external-alpha", action="store_true")
    parser.add_argument("--require-hosted-alpha", action="store_true")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if args.require_external_alpha and args.require_hosted_alpha:
        raise SystemExit("choose only one of --require-external-alpha or --require-hosted-alpha")
    report = evaluate_evidence_readiness(
        args.root,
        contracts_en=args.contracts_en,
        contracts_zh=args.contracts_zh,
        ci_python310_passed=args.ci_python310_passed,
        ci_python312_passed=args.ci_python312_passed,
        ci_evidence=args.ci_evidence,
        codex_acceptance_report=args.codex_acceptance_report,
        live_validation_evidence=args.live_validation_evidence,
        expected_base_url=args.expected_base_url,
        artifact_reviewed=args.artifact_reviewed,
        live_validation_run_id=args.live_validation_run_id,
        reviewer=args.reviewer,
        remote_mcp_tested=args.remote_mcp_tested,
        remote_mcp_url=args.remote_mcp_url,
        hosted_gateway_protected=args.hosted_gateway_protected,
    )
    rendered = json.dumps(report, ensure_ascii=False, indent=2) + "\n"
    if args.output:
        output = args.output.expanduser().resolve()
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(rendered, encoding="utf-8")
    print(rendered, end="")
    if args.require_hosted_alpha:
        ready = report["hosted_private_alpha_ready"]
    elif args.require_external_alpha:
        ready = report["external_alpha_ready"]
    else:
        ready = report["code_ready"]
    return 0 if ready else 1


if __name__ == "__main__":
    raise SystemExit(main())
