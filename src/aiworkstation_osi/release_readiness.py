"""Produce a deterministic release-readiness report for the M1 alpha.

The report distinguishes repository/code readiness, Skills-only external-alpha
readiness, hosted private-alpha readiness, and broad public-launch readiness. It
never contacts AI Workstation and never claims that CI, Codex, remote MCP tests,
or human review occurred without explicit evidence supplied by the operator.
"""

from __future__ import annotations

import argparse
import json
import tempfile
from pathlib import Path
from typing import Any, Mapping, Sequence

from .alpha_bundle import build_alpha_bundle
from .endpoint_policy import validate_mcp_endpoint
from .fixture_replay import replay_contract_directory
from .fixture_validation import validate_contract_directory
from .plugin_validation import validate_plugin_package

READINESS_SCHEMA_VERSION = "osi.release-readiness.v2"

REQUIRED_REPOSITORY_PATHS = (
    ".codex-plugin/plugin.json",
    ".agents/plugins/marketplace.json",
    ".github/workflows/ci.yml",
    ".github/workflows/live-contract-validation.yml",
    ".github/workflows/alpha-package.yml",
    ".github/workflows/release.yml",
    ".dockerignore",
    "Dockerfile",
    "compose.hosted.example.yml",
    "README.md",
    "README.zh-CN.md",
    "CHANGELOG.md",
    "LICENSE",
    "TERMS.md",
    "SECURITY.md",
    "PRIVACY.md",
    "SUPPORT.md",
    "CONTRIBUTING.md",
    "CODE_OF_CONDUCT.md",
    "ROADMAP.md",
    "docs/QUICKSTART.md",
    "docs/FAQ.md",
    "docs/MODEL-AND-DATA-FLOW.md",
    "docs/openai-plugin-submission.md",
    "docs/architecture.md",
    "docs/codex-setup.md",
    "docs/live-validation-workflow.md",
    "docs/production-validation.md",
    "docs/plugin-packaging.md",
    "docs/alpha-tester-guide.md",
    "docs/external-alpha-checklist.md",
    "docs/hosted-mcp.md",
    "docs/public-launch-decisions.md",
    "product-skills/ai-open-source-intelligence/SKILL.md",
    "schemas/tool-manifest.json",
    "schemas/tool-result.schema.json",
    "evals/cases.json",
    "evals/plugin-cases.json",
    "src/aiworkstation_osi/endpoint_policy.py",
    "src/aiworkstation_osi/http_server.py",
    "src/aiworkstation_osi/remote_smoke.py",
    "tests/test_http_server.py",
    "tests/test_remote_smoke.py",
    "tests/test_container_packaging.py",
)


def _check(check_id: str, ok: bool, message: str, **details: Any) -> dict[str, Any]:
    return {
        "id": check_id,
        "ok": bool(ok),
        "message": message,
        "details": details,
    }


def _load_json(path: Path) -> Mapping[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, Mapping):
        raise ValueError(f"{path} must contain a JSON object")
    return value


def _pyproject_version(root: Path) -> str:
    try:
        from ._version import __version__
        return __version__
    except Exception:
        return ""


def _contract_gate(directory: Path | None, locale: str) -> tuple[dict[str, Any], list[str]]:
    blockers: list[str] = []
    if directory is None:
        blockers.append(f"{locale} production contract capture has not been supplied")
        return (
            _check(
                f"contracts-{locale}",
                False,
                f"No {locale} contract directory was supplied.",
                supplied=False,
            ),
            blockers,
        )

    validation = validate_contract_directory(directory)
    replay = replay_contract_directory(directory) if validation.get("ok") else {
        "ok": False,
        "summary": {"passed": 0, "failed": 0},
    }
    manifest_locale = ""
    manifest_project_id = ""
    try:
        manifest = _load_json(directory / "manifest.json")
        manifest_locale = str(manifest.get("locale") or "")
        manifest_project_id = str(manifest.get("project_id") or "")
    except (OSError, ValueError, json.JSONDecodeError):
        pass

    locale_ok = manifest_locale == locale
    ok = bool(validation.get("ok")) and bool(replay.get("ok")) and locale_ok
    if not validation.get("ok"):
        blockers.append(f"{locale} contract validation failed")
    if validation.get("ok") and not replay.get("ok"):
        blockers.append(f"{locale} contract replay failed")
    if manifest_locale and not locale_ok:
        blockers.append(f"{locale} contract directory declares locale {manifest_locale}")
    if not manifest_locale:
        blockers.append(f"{locale} contract manifest locale is missing")

    return (
        _check(
            f"contracts-{locale}",
            ok,
            f"{locale} contract capture must validate and replay through the hardened provider.",
            supplied=True,
            directory=str(directory),
            manifest_locale=manifest_locale,
            project_id=manifest_project_id,
            validation_summary=validation.get("summary") or {},
            replay_summary=replay.get("summary") or {},
        ),
        blockers,
    )


def _remote_endpoint_gate(remote_mcp_url: str) -> tuple[dict[str, Any], list[str]]:
    blockers: list[str] = []
    value = remote_mcp_url.strip()
    if not value:
        blockers.append("hosted MCP endpoint URL is missing")
        return (
            _check(
                "hosted-mcp-endpoint",
                False,
                "No hosted MCP endpoint URL was supplied.",
                supplied=False,
            ),
            blockers,
        )
    try:
        normalized = validate_mcp_endpoint(value, allow_http_localhost=False)
    except ValueError as exc:
        blockers.append(f"hosted MCP endpoint is invalid: {exc}")
        return (
            _check(
                "hosted-mcp-endpoint",
                False,
                "Hosted MCP endpoint must be a credential-free HTTPS /mcp URL.",
                supplied=True,
                endpoint=value,
                error=str(exc),
            ),
            blockers,
        )
    return (
        _check(
            "hosted-mcp-endpoint",
            True,
            "Hosted MCP endpoint is a credential-free HTTPS /mcp URL.",
            supplied=True,
            endpoint=normalized,
        ),
        blockers,
    )


def evaluate_release_readiness(
    root: Path,
    *,
    contracts_en: Path | None = None,
    contracts_zh: Path | None = None,
    ci_python310_passed: bool = False,
    ci_python312_passed: bool = False,
    codex_tested: bool = False,
    artifact_reviewed: bool = False,
    live_validation_run_id: str = "",
    reviewer: str = "",
    remote_mcp_tested: bool = False,
    remote_mcp_url: str = "",
    hosted_gateway_protected: bool = False,
) -> dict[str, Any]:
    """Evaluate code gates and explicit alpha attestations offline."""

    repository_root = Path(root).resolve()
    checks: list[dict[str, Any]] = []
    code_blockers: list[str] = []
    operational_blockers: list[str] = []
    hosted_alpha_blockers: list[str] = []
    warnings: list[str] = []

    missing_paths = [
        relative
        for relative in REQUIRED_REPOSITORY_PATHS
        if not (repository_root / relative).is_file()
    ]
    checks.append(
        _check(
            "required-repository-paths",
            not missing_paths,
            "Required source, workflow, unified Skill, schema, deployment and release documents exist.",
            missing=missing_paths,
        )
    )
    if missing_paths:
        code_blockers.append("required repository files are missing")

    try:
        plugin_report = validate_plugin_package(repository_root)
    except Exception as exc:
        plugin_report = {
            "local_skills_ready": False,
            "public_submission_ready": False,
            "errors": [str(exc)],
            "warnings": [],
        }
    plugin_ready = bool(plugin_report.get("local_skills_ready"))
    checks.append(
        _check(
            "plugin-package",
            plugin_ready,
            "Single-Skill plugin package passes the offline validator.",
            errors=plugin_report.get("errors") or [],
            warnings=plugin_report.get("warnings") or [],
            public_submission_ready=bool(plugin_report.get("public_submission_ready")),
        )
    )
    if not plugin_ready:
        code_blockers.append("single-Skill plugin package validation failed")
    warnings.extend(str(value) for value in plugin_report.get("warnings") or [])

    try:
        plugin = _load_json(repository_root / ".codex-plugin" / "plugin.json")
        plugin_version = str(plugin.get("version") or "")
        python_version = _pyproject_version(repository_root)
        changelog = (repository_root / "CHANGELOG.md").read_text(encoding="utf-8")
        version_ok = bool(plugin_version) and plugin_version == python_version and (
            f"## [{plugin_version}]" in changelog
        )
    except (OSError, ValueError, json.JSONDecodeError):
        plugin_version = ""
        python_version = ""
        version_ok = False
    checks.append(
        _check(
            "version-alignment",
            version_ok,
            "Plugin, Python package, and changelog versions agree.",
            plugin_version=plugin_version,
            python_version=python_version,
        )
    )
    if not version_ok:
        code_blockers.append("package and plugin versions are not aligned")

    try:
        with tempfile.TemporaryDirectory() as temp_dir:
            first = build_alpha_bundle(repository_root, Path(temp_dir) / "first")
            second = build_alpha_bundle(repository_root, Path(temp_dir) / "second")
            first_bytes = Path(first["archive"]).read_bytes()
            second_bytes = Path(second["archive"]).read_bytes()
            bundle_ok = (
                first_bytes == second_bytes
                and first.get("archive_sha256") == second.get("archive_sha256")
                and first.get("distribution_mode") == "skills-only"
                and first.get("live_mcp_bundled") is False
            )
            bundle_details = {
                "archive_sha256": first.get("archive_sha256"),
                "file_count": first.get("file_count"),
                "distribution_mode": first.get("distribution_mode"),
                "live_mcp_bundled": first.get("live_mcp_bundled"),
            }
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        bundle_ok = False
        bundle_details = {"error": str(exc)}
    checks.append(
        _check(
            "deterministic-alpha-bundle",
            bundle_ok,
            "Two single-Skill alpha builds from the same tree are byte-identical and safely scoped.",
            **bundle_details,
        )
    )
    if not bundle_ok:
        code_blockers.append("deterministic alpha bundle build failed")

    en_check, en_blockers = _contract_gate(contracts_en, "en")
    zh_check, zh_blockers = _contract_gate(contracts_zh, "zh")
    checks.extend((en_check, zh_check))
    operational_blockers.extend(en_blockers)
    operational_blockers.extend(zh_blockers)

    attestations = {
        "ci_python310_passed": bool(ci_python310_passed),
        "ci_python312_passed": bool(ci_python312_passed),
        "codex_tested": bool(codex_tested),
        "artifact_reviewed": bool(artifact_reviewed),
        "live_validation_run_id": str(live_validation_run_id).strip(),
        "reviewer": str(reviewer).strip(),
        "remote_mcp_tested": bool(remote_mcp_tested),
        "remote_mcp_url": str(remote_mcp_url).strip(),
        "hosted_gateway_protected": bool(hosted_gateway_protected),
    }
    for key, label in (
        ("ci_python310_passed", "GitHub Actions succeeded on Python 3.10"),
        ("ci_python312_passed", "GitHub Actions succeeded on Python 3.12"),
        ("codex_tested", "The package and nine-tool MCP workflow were tested from Codex"),
        ("artifact_reviewed", "A human reviewed the sanitized live-validation artifacts"),
    ):
        ok = bool(attestations[key])
        checks.append(
            _check(
                f"attestation-{key.replace('_', '-')}",
                ok,
                label + ".",
                operator_attested=ok,
            )
        )
        if not ok:
            operational_blockers.append(label.lower() + " is not attested")

    run_id_ok = bool(attestations["live_validation_run_id"])
    reviewer_ok = bool(attestations["reviewer"])
    checks.append(
        _check(
            "validation-evidence",
            run_id_ok and reviewer_ok,
            "Live validation run ID and artifact reviewer are recorded.",
            live_validation_run_id=attestations["live_validation_run_id"],
            reviewer=attestations["reviewer"],
        )
    )
    if not run_id_ok:
        operational_blockers.append("live validation workflow run ID is missing")
    if not reviewer_ok:
        operational_blockers.append("artifact reviewer is missing")

    code_ready = not code_blockers
    external_alpha_ready = code_ready and not operational_blockers

    endpoint_check, endpoint_blockers = _remote_endpoint_gate(attestations["remote_mcp_url"])
    checks.append(endpoint_check)
    hosted_alpha_blockers.extend(endpoint_blockers)

    remote_test_ok = bool(attestations["remote_mcp_tested"])
    checks.append(
        _check(
            "attestation-remote-mcp-tested",
            remote_test_ok,
            "The deployed Streamable HTTP endpoint passed the remote nine-tool smoke test.",
            operator_attested=remote_test_ok,
        )
    )
    if not remote_test_ok:
        hosted_alpha_blockers.append("deployed Streamable HTTP MCP smoke test is not attested")

    gateway_ok = bool(attestations["hosted_gateway_protected"])
    checks.append(
        _check(
            "attestation-hosted-gateway-protected",
            gateway_ok,
            "The hosted endpoint is behind the required TLS/rate-limited gateway or trusted private network.",
            operator_attested=gateway_ok,
        )
    )
    if not gateway_ok:
        hosted_alpha_blockers.append(
            "hosted MCP gateway TLS/rate-limit/private-network protection is not attested"
        )

    if not external_alpha_ready:
        hosted_alpha_blockers.append("Skills-only external-alpha gates are not complete")

    hosted_private_alpha_ready = external_alpha_ready and not hosted_alpha_blockers

    public_launch_ready = False
    public_launch_blockers = [
        "service-specific hosted privacy/terms and operational retention policy are not final",
        "production anonymous-usage monitoring and abuse thresholds still need real-user validation",
        "canonical public MCP connection has not completed platform review",
        "public directory submission review/publish has not occurred",
    ]

    return {
        "schema_version": READINESS_SCHEMA_VERSION,
        "repository_root": str(repository_root),
        "version": plugin_version,
        "code_ready": code_ready,
        "external_alpha_ready": external_alpha_ready,
        "hosted_private_alpha_ready": hosted_private_alpha_ready,
        "public_launch_ready": public_launch_ready,
        "summary": {
            "checks": len(checks),
            "passed": sum(1 for check in checks if check["ok"]),
            "failed": sum(1 for check in checks if not check["ok"]),
        },
        "checks": checks,
        "code_blockers": code_blockers,
        "operational_blockers": operational_blockers,
        "hosted_alpha_blockers": hosted_alpha_blockers,
        "public_launch_blockers": public_launch_blockers,
        "warnings": warnings,
        "attestations": attestations,
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="osi-readiness")
    parser.add_argument("--root", type=Path, default=Path.cwd())
    parser.add_argument("--contracts-en", type=Path)
    parser.add_argument("--contracts-zh", type=Path)
    parser.add_argument("--ci-python310-passed", action="store_true")
    parser.add_argument("--ci-python312-passed", action="store_true")
    parser.add_argument("--codex-tested", action="store_true")
    parser.add_argument("--artifact-reviewed", action="store_true")
    parser.add_argument("--live-validation-run-id", default="")
    parser.add_argument("--reviewer", default="")
    parser.add_argument("--remote-mcp-tested", action="store_true")
    parser.add_argument("--remote-mcp-url", default="")
    parser.add_argument("--hosted-gateway-protected", action="store_true")
    parser.add_argument("--output", type=Path)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    report = evaluate_release_readiness(
        args.root,
        contracts_en=args.contracts_en,
        contracts_zh=args.contracts_zh,
        ci_python310_passed=args.ci_python310_passed,
        ci_python312_passed=args.ci_python312_passed,
        codex_tested=args.codex_tested,
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
    return 0 if report.get("code_ready") is True else 1


if __name__ == "__main__":
    raise SystemExit(main())
