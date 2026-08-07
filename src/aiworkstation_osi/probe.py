"""Probe the live public Radar contract without exposing private data."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, Mapping, Sequence

from .contracts import utc_now_iso
from .errors import ToolError
from .strict_http_provider import AIWorkstationHttpProvider
from .tools import ToolRegistry

DEFAULT_EN_QUERY = "Find a self-hosted RAG project with Docker and a web UI."
DEFAULT_ZH_QUERY = "找支持 Docker、Web 界面和私有部署的 RAG 知识库项目。"


def _check(check_id: str, ok: bool, message: str, **details: Any) -> dict[str, Any]:
    return {"id": check_id, "ok": bool(ok), "message": message, "details": details}


def evaluate_probe(
    facts: Mapping[str, Any],
    license_result: Mapping[str, Any],
    search: Mapping[str, Any],
) -> list[dict[str, Any]]:
    """Evaluate already-sanitized tool envelopes from a live probe."""

    checks: list[dict[str, Any]] = []
    facts_data = facts.get("data") if isinstance(facts.get("data"), Mapping) else {}
    project = facts_data.get("project") if isinstance(facts_data.get("project"), Mapping) else {}
    snapshot = str(facts_data.get("snapshot_id") or "")
    checks.append(
        _check(
            "project-found",
            bool(facts_data.get("found") and project),
            "Named project resolves to one current public record.",
            project_id=project.get("project_id"),
        )
    )
    checks.append(
        _check(
            "project-snapshot",
            bool(snapshot),
            "Project facts include public snapshot identity.",
            snapshot_id=snapshot,
        )
    )
    checks.append(
        _check(
            "project-evidence",
            bool(facts.get("verified_facts")),
            "At least one project fact carries evidence.",
            verified_fact_count=len(facts.get("verified_facts") or []),
        )
    )

    license_data = (
        license_result.get("data")
        if isinstance(license_result.get("data"), Mapping)
        else {}
    )
    license_value = license_data.get("license")
    evidence_status = str(license_data.get("evidence_status") or "")
    evidence_count = int(license_data.get("evidence_count") or 0)
    explicit_unknown = bool(license_result.get("unknowns"))
    verified_license = bool(license_value) and evidence_status == "verified" and evidence_count > 0
    explicit_unknown_license = not license_value and explicit_unknown
    checks.append(
        _check(
            "license-boundary",
            verified_license or explicit_unknown_license,
            "License is backed by direct public License evidence or explicitly unknown; it is never silently inferred.",
            license=license_value,
            evidence_status=evidence_status,
            evidence_count=evidence_count,
            explicit_unknown=explicit_unknown,
        )
    )
    risk_codes = {
        str(row.get("code") or "")
        for row in license_result.get("risks") or []
        if isinstance(row, Mapping)
    }
    checks.append(
        _check(
            "license-legal-boundary",
            "NOT_LEGAL_ADVICE" in risk_codes,
            "License tool marks the legal-advice boundary.",
            risk_codes=sorted(risk_codes),
        )
    )

    search_data = search.get("data") if isinstance(search.get("data"), Mapping) else {}
    selector_evidence_status = str(search_data.get("evidence_status") or "")
    search_snapshot = str(search_data.get("snapshot_id") or "")
    project_count = int(search_data.get("total") or 0)
    no_match_reason = str(search_data.get("no_match_reason") or "").strip()
    checks.append(
        _check(
            "selector-evidence",
            selector_evidence_status in {"available", "partial"},
            "Selector discloses usable evidence status.",
            evidence_status=selector_evidence_status,
            notice=search_data.get("notice"),
        )
    )
    checks.append(
        _check(
            "selector-honesty",
            project_count > 0 or bool(no_match_reason),
            "Search returns verified candidates or an explicit no-match reason.",
            project_count=project_count,
            no_match_reason=no_match_reason,
        )
    )
    checks.append(
        _check(
            "selector-snapshot",
            project_count == 0 or bool(search_snapshot),
            "Hydrated search candidates share public snapshot identity.",
            snapshot_id=search_snapshot,
        )
    )
    return checks


def run_probe(
    *,
    base_url: str,
    locale: str,
    project_id: str,
    query: str,
    timeout: float = 30.0,
) -> dict[str, Any]:
    """Run three read-only calls and return a sanitized validation report."""

    provider = AIWorkstationHttpProvider(base_url, timeout=timeout, hydrate_limit=3)
    registry = ToolRegistry(provider)
    facts = registry.invoke(
        "get_project_facts",
        {"project_id": project_id, "locale": locale, "request_id": "probe-facts"},
    ).to_dict()
    license_result = registry.invoke(
        "get_license_evidence",
        {"project_id": project_id, "locale": locale, "request_id": "probe-license"},
    ).to_dict()
    search = registry.invoke(
        "search_ai_projects",
        {
            "query": query,
            "constraints": {"docker": "required", "web_ui": "preferred"},
            "locale": locale,
            "source_mode": "required",
            "request_id": "probe-search",
        },
    ).to_dict()
    checks = evaluate_probe(facts, license_result, search)
    return {
        "schema_version": "osi.public-radar-probe.v1",
        "generated_at": utc_now_iso(),
        "base_url": base_url.rstrip("/"),
        "locale": locale,
        "project_id": project_id,
        "ok": all(check["ok"] for check in checks),
        "checks": checks,
        "summary": {
            "passed": sum(1 for check in checks if check["ok"]),
            "failed": sum(1 for check in checks if not check["ok"]),
        },
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="osi-probe")
    parser.add_argument("--base-url", default="https://aiworkstation.cn")
    parser.add_argument("--locale", choices=("zh", "en"), default="en")
    parser.add_argument("--project-id", default="infiniflow/ragflow")
    parser.add_argument("--query")
    parser.add_argument("--timeout", type=float, default=30.0)
    parser.add_argument("--output", type=Path)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    query = args.query or (DEFAULT_ZH_QUERY if args.locale == "zh" else DEFAULT_EN_QUERY)
    try:
        report = run_probe(
            base_url=args.base_url,
            locale=args.locale,
            project_id=args.project_id,
            query=query,
            timeout=args.timeout,
        )
    except (ToolError, ValueError) as exc:
        report = {
            "schema_version": "osi.public-radar-probe.v1",
            "generated_at": utc_now_iso(),
            "base_url": args.base_url.rstrip("/"),
            "locale": args.locale,
            "project_id": args.project_id,
            "ok": False,
            "error": {
                "code": getattr(exc, "code", "INVALID_CONFIGURATION"),
                "message": str(exc),
            },
        }
    rendered = json.dumps(report, ensure_ascii=False, indent=2) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(rendered, encoding="utf-8")
    print(rendered, end="")
    return 0 if report.get("ok") else 1


if __name__ == "__main__":
    raise SystemExit(main())
