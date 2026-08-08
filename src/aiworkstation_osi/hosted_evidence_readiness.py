"""Evidence-first Hosted Private Alpha readiness.

This wrapper extends the External Alpha evidence chain with a candidate-bound,
OAuth-authenticated remote MCP smoke report. It deliberately does not accept
manual booleans for the remote-MCP or gateway-protection gates.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, Mapping, Sequence

from .evidence_readiness import _git_head, evaluate_evidence_readiness
from .hosted_remote_evidence import validate_hosted_remote_evidence


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


def evaluate_hosted_evidence_readiness(
    root: Path,
    *,
    ci_evidence: Path,
    live_validation_evidence: Path,
    codex_acceptance_report: Path,
    hosted_remote_evidence: Path,
    artifact_reviewed: bool,
    reviewer: str,
    expected_base_url: str,
    expected_hosted_mcp_url: str,
    expected_oauth_issuer: str,
) -> dict[str, Any]:
    repository_root = root.expanduser().resolve()
    candidate_commit = _git_head(repository_root)
    hosted = validate_hosted_remote_evidence(
        hosted_remote_evidence,
        candidate_commit=candidate_commit,
        expected_endpoint=expected_hosted_mcp_url,
        expected_issuer=expected_oauth_issuer,
    )

    report = evaluate_evidence_readiness(
        repository_root,
        ci_evidence=ci_evidence,
        live_validation_evidence=live_validation_evidence,
        codex_acceptance_report=codex_acceptance_report,
        expected_base_url=expected_base_url,
        artifact_reviewed=artifact_reviewed,
        reviewer=reviewer,
        remote_mcp_tested=bool(hosted.get("ok")),
        remote_mcp_url=(
            str(hosted.get("endpoint") or expected_hosted_mcp_url)
            if expected_hosted_mcp_url
            else str(hosted.get("endpoint") or "")
        ),
        hosted_gateway_protected=bool(hosted.get("ok")),
    )
    machine = report.setdefault("machine_evidence", {})
    if isinstance(machine, dict):
        machine["hosted_remote"] = hosted
    report["hosted_remote_evidence"] = hosted

    _mark_machine_check(
        report,
        "attestation-remote-mcp-tested",
        evidence=hosted,
        success_message="The deployed OAuth-protected Hosted MCP passed candidate-bound remote evidence validation.",
        failure_message="Valid candidate-bound Hosted MCP remote evidence is required.",
    )
    _mark_machine_check(
        report,
        "attestation-hosted-gateway-protected",
        evidence=hosted,
        success_message="The OAuth 401 challenge and RFC 9728 protected-resource boundary are verified by remote evidence.",
        failure_message="Remote evidence must prove the OAuth-protected gateway boundary.",
    )
    for check in report.get("checks") or []:
        if not isinstance(check, dict) or check.get("id") != "hosted-mcp-endpoint":
            continue
        details = check.setdefault("details", {})
        details["remote_evidence_verified"] = bool(hosted.get("ok"))
        details["remote_evidence_path"] = str(hosted.get("path") or "")
        break

    return report


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="osi-hosted-evidence-readiness")
    parser.add_argument("--root", type=Path, default=Path.cwd())
    parser.add_argument("--ci-evidence", type=Path, required=True)
    parser.add_argument("--live-validation-evidence", type=Path, required=True)
    parser.add_argument("--codex-acceptance-report", type=Path, required=True)
    parser.add_argument("--hosted-remote-evidence", type=Path, required=True)
    parser.add_argument("--artifact-reviewed", action="store_true")
    parser.add_argument("--reviewer", required=True)
    parser.add_argument("--expected-base-url", default="https://aiworkstation.cn")
    parser.add_argument("--expected-hosted-mcp-url", required=True)
    parser.add_argument("--expected-oauth-issuer", required=True)
    parser.add_argument("--output", type=Path)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    report = evaluate_hosted_evidence_readiness(
        args.root,
        ci_evidence=args.ci_evidence,
        live_validation_evidence=args.live_validation_evidence,
        codex_acceptance_report=args.codex_acceptance_report,
        hosted_remote_evidence=args.hosted_remote_evidence,
        artifact_reviewed=args.artifact_reviewed,
        reviewer=args.reviewer,
        expected_base_url=args.expected_base_url,
        expected_hosted_mcp_url=args.expected_hosted_mcp_url,
        expected_oauth_issuer=args.expected_oauth_issuer,
    )
    rendered = json.dumps(report, ensure_ascii=False, indent=2) + "\n"
    if args.output:
        output = args.output.expanduser().resolve()
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(rendered, encoding="utf-8")
    print(rendered, end="")
    return 0 if report.get("hosted_private_alpha_ready") is True else 1


if __name__ == "__main__":
    raise SystemExit(main())
