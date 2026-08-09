"""Build a deterministic, reviewable Skills-only external-alpha archive."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import stat
import zipfile
from pathlib import Path, PurePosixPath
from typing import Any, Sequence

BUNDLE_SCHEMA_VERSION = "osi.alpha-bundle.v1"
MAX_FILE_BYTES = 1_000_000
FIXED_ZIP_TIME = (1980, 1, 1, 0, 0, 0)

REQUIRED_FILES = (
    ".codex-plugin/plugin.json",
    ".agents/plugins/marketplace.json",
    "README.md",
    "README.zh-CN.md",
    "CHANGELOG.md",
    "LICENSE",
    "TERMS.md",
    "SECURITY.md",
    "PRIVACY.md",
    "SUPPORT.md",
    "ROADMAP.md",
    "docs/QUICKSTART.md",
    "docs/FAQ.md",
    "docs/codex-setup.md",
    "docs/plugin-packaging.md",
    "docs/alpha-tester-guide.md",
    "docs/external-alpha-checklist.md",
)

SECRET_PATTERNS = (
    re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----"),
    re.compile(r"\bgh[pousr]_[A-Za-z0-9]{30,}\b"),
    re.compile(r"\bgithub_pat_[A-Za-z0-9_]{40,}\b"),
    re.compile(r"\bsk-[A-Za-z0-9]{32,}\b"),
    re.compile(r"\bAKIA[0-9A-Z]{16}\b"),
)


def _sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _safe_relative_path(path: Path, root: Path) -> str:
    relative = path.relative_to(root).as_posix()
    pure = PurePosixPath(relative)
    if pure.is_absolute() or ".." in pure.parts or relative.startswith("/"):
        raise ValueError(f"unsafe bundle path: {relative}")
    return relative


def _read_public_file(path: Path, root: Path) -> tuple[str, bytes]:
    if path.is_symlink():
        raise ValueError(f"symlinks are not allowed in alpha bundles: {path}")
    if not path.is_file():
        raise ValueError(f"required bundle file is missing: {path}")
    relative = _safe_relative_path(path, root)
    data = path.read_bytes()
    if len(data) > MAX_FILE_BYTES:
        raise ValueError(f"bundle file exceeds {MAX_FILE_BYTES} bytes: {relative}")
    try:
        text = data.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise ValueError(f"bundle file must be UTF-8 text: {relative}") from exc
    for pattern in SECRET_PATTERNS:
        if pattern.search(text):
            raise ValueError(f"credential-like value found in bundle file: {relative}")
    return relative, data


def _plugin_metadata(root: Path) -> tuple[str, str]:
    path = root / ".codex-plugin" / "plugin.json"
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError("plugin.json must contain an object")
    name = str(payload.get("name") or "").strip()
    version = str(payload.get("version") or "").strip()
    if not re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*", name):
        raise ValueError("plugin name must be stable kebab-case")
    if not re.fullmatch(r"\d+\.\d+\.\d+(?:-[0-9A-Za-z.-]+)?", version):
        raise ValueError("plugin version must use semantic versioning")
    return name, version


def collect_bundle_files(root: Path) -> list[tuple[str, bytes]]:
    """Collect the reviewed single-Skill distribution surface."""

    resolved_root = root.resolve()
    collected: dict[str, bytes] = {}
    for relative in REQUIRED_FILES:
        path, data = _read_public_file(resolved_root / relative, resolved_root)
        collected[path] = data

    skills_root = resolved_root / "skills"
    if not skills_root.is_dir() or skills_root.is_symlink():
        raise ValueError("skills directory is missing or unsafe")
    skill_files = sorted(path for path in skills_root.rglob("*") if path.is_file())
    if not skill_files:
        raise ValueError("no Skill files were found")
    for file_path in skill_files:
        relative, data = _read_public_file(file_path, resolved_root)
        if Path(relative).suffix.lower() not in {".md", ".json", ".txt"}:
            raise ValueError(f"unsupported Skill bundle file type: {relative}")
        collected[relative] = data

    expected_skills = {"skills/ai-open-source-intelligence/SKILL.md"}
    actual_skill_docs = {path for path in collected if path.startswith("skills/") and path.endswith("/SKILL.md")}
    if actual_skill_docs != expected_skills:
        raise ValueError(
            "public bundle must contain exactly the unified Skill; found: "
            + ", ".join(sorted(actual_skill_docs))
        )
    return sorted(collected.items())


def _zip_info(path: str) -> zipfile.ZipInfo:
    info = zipfile.ZipInfo(path, FIXED_ZIP_TIME)
    info.compress_type = zipfile.ZIP_DEFLATED
    info.create_system = 3
    info.external_attr = (stat.S_IFREG | 0o644) << 16
    return info


def build_alpha_bundle(root: Path, output_dir: Path) -> dict[str, Any]:
    """Build a reproducible Skills-only ZIP and external checksum file."""

    resolved_root = root.resolve()
    name, version = _plugin_metadata(resolved_root)
    files = collect_bundle_files(resolved_root)
    manifest = {
        "schema_version": BUNDLE_SCHEMA_VERSION,
        "name": name,
        "version": version,
        "distribution_mode": "skills-only",
        "live_mcp_bundled": False,
        "files": [
            {"path": path, "size": len(data), "sha256": _sha256(data)}
            for path, data in files
        ],
    }
    manifest_bytes = (
        json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    ).encode("utf-8")

    output_dir.mkdir(parents=True, exist_ok=True)
    archive = output_dir / f"{name}-skills-{version}.zip"
    with zipfile.ZipFile(archive, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as bundle:
        bundle.writestr(_zip_info("BUNDLE-MANIFEST.json"), manifest_bytes)
        for path, data in files:
            bundle.writestr(_zip_info(path), data)

    archive_bytes = archive.read_bytes()
    archive_sha256 = _sha256(archive_bytes)
    checksum = output_dir / "SHA256SUMS"
    checksum.write_text(f"{archive_sha256}  {archive.name}\n", encoding="utf-8")

    report = {
        "ok": True,
        "schema_version": BUNDLE_SCHEMA_VERSION,
        "name": name,
        "version": version,
        "archive": str(archive),
        "archive_sha256": archive_sha256,
        "checksum_file": str(checksum),
        "file_count": len(files),
        "distribution_mode": "skills-only",
        "live_mcp_bundled": False,
    }
    (output_dir / "bundle-report.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return report


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="osi-build-alpha")
    parser.add_argument("--root", type=Path, default=Path.cwd())
    parser.add_argument("--output-dir", type=Path, default=Path("dist/alpha"))
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        report = build_alpha_bundle(args.root, args.output_dir)
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        print(
            json.dumps(
                {"ok": False, "error": {"code": "ALPHA_BUNDLE_INVALID", "message": str(exc)}},
                ensure_ascii=False,
                indent=2,
            )
        )
        return 1
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
