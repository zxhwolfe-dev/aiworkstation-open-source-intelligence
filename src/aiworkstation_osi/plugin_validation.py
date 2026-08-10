"""Validate the local Codex plugin package and repo marketplace offline."""

from __future__ import annotations

import argparse
import json
import re
import urllib.parse
from pathlib import Path
from typing import Any, Mapping, Sequence

PLUGIN_NAME_PATTERN = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
SEMVER_PATTERN = re.compile(r"^(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)$")
SKILL_NAME_PATTERN = re.compile(r"(?m)^name:\s*([^\s]+)\s*$")
SKILL_DESCRIPTION_PATTERN = re.compile(r"(?m)^description:\s*(.+?)\s*$")

REQUIRED_MANIFEST_FIELDS = {"name", "version", "description", "skills"}
REQUIRED_INTERFACE_FIELDS = {
    "displayName",
    "shortDescription",
    "longDescription",
    "developerName",
    "category",
    "capabilities",
    "websiteURL",
    "defaultPrompt",
    "brandColor",
}
PUBLIC_INTERFACE_URL_FIELDS = (
    "supportURL",
    "privacyPolicyURL",
    "termsOfServiceURL",
)
REQUIRED_MARKETPLACE_POLICY_FIELDS = {"installation", "authentication"}


def _load_object(path: Path, errors: list[str]) -> Mapping[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        errors.append(f"missing file: {path}")
        return {}
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        errors.append(f"invalid JSON file {path}: {exc}")
        return {}
    if not isinstance(value, Mapping):
        errors.append(f"{path} must contain a JSON object")
        return {}
    return value


def _resolve_relative_path(root: Path, raw_path: Any, label: str, errors: list[str]) -> Path | None:
    if not isinstance(raw_path, str) or not raw_path.startswith("./"):
        errors.append(f"{label} must be a ./-prefixed path relative to the plugin root")
        return None
    candidate = (root / raw_path[2:]).resolve()
    try:
        candidate.relative_to(root.resolve())
    except ValueError:
        errors.append(f"{label} escapes the plugin root")
        return None
    return candidate


def _frontmatter(content: str, path: Path, errors: list[str]) -> tuple[str, str]:
    if not content.startswith("---\n"):
        errors.append(f"{path}: SKILL.md must start with YAML frontmatter")
        return "", ""
    name = SKILL_NAME_PATTERN.search(content)
    description = SKILL_DESCRIPTION_PATTERN.search(content)
    if not name:
        errors.append(f"{path}: frontmatter name is missing")
    if not description or not description.group(1).strip():
        errors.append(f"{path}: frontmatter description is missing")
    return (
        name.group(1).strip() if name else "",
        description.group(1).strip() if description else "",
    )


def _validate_component_path(
    root: Path,
    manifest: Mapping[str, Any],
    field: str,
    expected_name: str,
    errors: list[str],
) -> None:
    if field not in manifest:
        return
    path = _resolve_relative_path(root, manifest[field], field, errors)
    if path is None:
        return
    if path != (root / expected_name).resolve():
        errors.append(f"{field} must point to {expected_name}")
    if not path.is_file():
        errors.append(f"{field} target does not exist: {path}")


def _public_https_url(value: Any) -> bool:
    text = str(value or "").strip()
    if not text:
        return False
    try:
        parsed = urllib.parse.urlparse(text)
    except ValueError:
        return False
    return (
        parsed.scheme == "https"
        and bool(parsed.netloc)
        and parsed.hostname not in {"localhost", "127.0.0.1", "::1"}
        and parsed.username is None
        and parsed.password is None
    )


def validate_plugin_package(root: Path) -> dict[str, Any]:
    """Return local-install and public-submission metadata readiness for one plugin root."""

    plugin_root = Path(root).resolve()
    errors: list[str] = []
    warnings: list[str] = []
    public_blockers: list[str] = []
    manifest_path = plugin_root / ".codex-plugin" / "plugin.json"
    marketplace_path = plugin_root / ".agents" / "plugins" / "marketplace.json"
    manifest = _load_object(manifest_path, errors)
    marketplace = _load_object(marketplace_path, errors)

    manifest_directory = manifest_path.parent
    if manifest_directory.exists():
        extra_entries = sorted(
            path.name for path in manifest_directory.iterdir() if path.name != "plugin.json"
        )
        if extra_entries:
            errors.append(
                ".codex-plugin must contain only plugin.json; found: " + ", ".join(extra_entries)
            )

    if manifest:
        missing = sorted(REQUIRED_MANIFEST_FIELDS - set(manifest))
        if missing:
            errors.append(f"plugin manifest is missing required fields: {missing}")
        name = str(manifest.get("name") or "")
        version = str(manifest.get("version") or "")
        description = str(manifest.get("description") or "").strip()
        if not PLUGIN_NAME_PATTERN.fullmatch(name):
            errors.append("plugin name must be stable kebab-case")
        if not SEMVER_PATTERN.fullmatch(version):
            errors.append("plugin version must be semantic x.y.z")
        if not description:
            errors.append("plugin description must be non-empty")

        skills_root = _resolve_relative_path(plugin_root, manifest.get("skills"), "skills", errors)
        skill_names: set[str] = set()
        if skills_root is not None:
            if not skills_root.is_dir():
                errors.append(f"skills directory does not exist: {skills_root}")
            else:
                skill_files = sorted(skills_root.glob("*/SKILL.md"))
                if not skill_files:
                    errors.append("skills directory contains no */SKILL.md files")
                for skill_file in skill_files:
                    content = skill_file.read_text(encoding="utf-8")
                    skill_name, _description = _frontmatter(content, skill_file, errors)
                    if skill_name and skill_name != skill_file.parent.name:
                        errors.append(
                            f"{skill_file}: frontmatter name must match directory {skill_file.parent.name}"
                        )
                    if skill_name in skill_names:
                        errors.append(f"duplicate skill name: {skill_name}")
                    if skill_name:
                        skill_names.add(skill_name)

        _validate_component_path(plugin_root, manifest, "mcpServers", ".mcp.json", errors)
        _validate_component_path(plugin_root, manifest, "apps", ".app.json", errors)

        interface = manifest.get("interface")
        if not isinstance(interface, Mapping):
            errors.append("plugin manifest interface must be an object")
            interface_mapping: Mapping[str, Any] = {}
        else:
            interface_mapping = interface
            missing_interface = sorted(REQUIRED_INTERFACE_FIELDS - set(interface))
            if missing_interface:
                errors.append(f"plugin interface is missing fields: {missing_interface}")
            prompts = interface.get("defaultPrompt")
            if (
                not isinstance(prompts, Sequence)
                or isinstance(prompts, (str, bytes, bytearray))
                or len(prompts) < 3
                or any(not isinstance(prompt, str) or not prompt.strip() for prompt in prompts)
            ):
                errors.append("plugin interface must provide at least three non-empty default prompts")
            capabilities = interface.get("capabilities")
            if not isinstance(capabilities, Sequence) or isinstance(
                capabilities, (str, bytes, bytearray)
            ):
                errors.append("plugin capabilities must be an array")
            else:
                if "Read" not in capabilities:
                    errors.append("read-only product must declare the Read capability")
                if "Write" in capabilities:
                    errors.append("read-only product must not declare the Write capability")
            brand_color = str(interface.get("brandColor") or "")
            if not re.fullmatch(r"#[0-9A-Fa-f]{6}", brand_color):
                errors.append("brandColor must be a six-digit hexadecimal color")

        license_id = str(manifest.get("license") or "").strip()
        if not license_id:
            public_blockers.append("software license is missing")
        elif license_id != "Apache-2.0":
            public_blockers.append("public Skills release expects license=Apache-2.0")
        elif not (plugin_root / "LICENSE").is_file():
            public_blockers.append("Apache-2.0 LICENSE file is missing")

        for field in PUBLIC_INTERFACE_URL_FIELDS:
            value = interface_mapping.get(field)
            if not value:
                public_blockers.append(f"{field} is missing")
            elif not _public_https_url(value):
                public_blockers.append(f"{field} must be a public credential-free HTTPS URL")

        if not _public_https_url(interface_mapping.get("websiteURL")):
            public_blockers.append("websiteURL must be a public credential-free HTTPS URL")

        if "mcpServers" not in manifest and "apps" not in manifest:
            warnings.append(
                "current package is Skills-only; MCP server setup remains a separate local workflow"
            )

    if marketplace:
        if not str(marketplace.get("name") or "").strip():
            errors.append("marketplace name is required")
        interface = marketplace.get("interface")
        if not isinstance(interface, Mapping) or not str(interface.get("displayName") or "").strip():
            errors.append("marketplace interface.displayName is required")
        plugins = marketplace.get("plugins")
        if not isinstance(plugins, Sequence) or isinstance(plugins, (str, bytes, bytearray)):
            errors.append("marketplace plugins must be an array")
        else:
            matching_entries = [
                entry
                for entry in plugins
                if isinstance(entry, Mapping) and entry.get("name") == manifest.get("name")
            ]
            if len(matching_entries) != 1:
                errors.append("marketplace must contain exactly one entry for this plugin")
            else:
                entry = matching_entries[0]
                source = entry.get("source")
                if not isinstance(source, Mapping):
                    errors.append("marketplace source must be an object")
                else:
                    if source.get("source") != "local":
                        errors.append("repo-scoped marketplace source must be local")
                    source_path = _resolve_relative_path(
                        plugin_root,
                        source.get("path"),
                        "marketplace source.path",
                        errors,
                    )
                    if source_path is not None and source_path != plugin_root:
                        errors.append("repo marketplace must point to the repository-root plugin")
                policy = entry.get("policy")
                if not isinstance(policy, Mapping):
                    errors.append("marketplace policy must be an object")
                else:
                    missing_policy = sorted(REQUIRED_MARKETPLACE_POLICY_FIELDS - set(policy))
                    if missing_policy:
                        errors.append(f"marketplace policy is missing fields: {missing_policy}")
                    if policy.get("installation") not in {
                        "AVAILABLE",
                        "INSTALLED_BY_DEFAULT",
                        "NOT_AVAILABLE",
                    }:
                        errors.append("marketplace installation policy is invalid")
                    if policy.get("authentication") not in {"NONE", "ON_INSTALL"}:
                        errors.append("marketplace authentication policy is invalid")
                if not str(entry.get("category") or "").strip():
                    errors.append("marketplace category is required")

    for blocker in public_blockers:
        warnings.append("public submission is blocked: " + blocker)

    local_ready = not errors
    public_ready = local_ready and not public_blockers
    return {
        "schema_version": "osi.plugin-validation.v1",
        "plugin_root": str(plugin_root),
        "plugin_name": manifest.get("name") if manifest else None,
        "plugin_version": manifest.get("version") if manifest else None,
        "local_skills_ready": local_ready,
        "public_submission_ready": public_ready,
        "summary": {"errors": len(errors), "warnings": len(warnings)},
        "errors": errors,
        "warnings": warnings,
        "public_submission_blockers": public_blockers,
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="osi-validate-plugin")
    parser.add_argument("--root", type=Path, default=Path.cwd())
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    report = validate_plugin_package(args.root)
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0 if report["local_skills_ready"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
