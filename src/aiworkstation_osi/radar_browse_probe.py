"""Probe the public Radar browsing surfaces used by the one-install product."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, Mapping, Sequence

from .full_radar_provider import FullRadarHttpProvider

DIMENSIONS = (
    ("rankings", "ranking"),
    ("collections", "collection"),
    ("categories", "category"),
    ("scenarios", "scenario"),
)


def _rows(value: Any) -> list[Mapping[str, Any]]:
    if not isinstance(value, Sequence) or isinstance(value, (str, bytes, bytearray)):
        return []
    return [row for row in value if isinstance(row, Mapping)]


def _row_id(row: Mapping[str, Any]) -> str:
    for key in ("id", "slug", "value", "key", "name"):
        value = str(row.get(key) or "").strip()
        if value:
            return value
    return ""


def probe_radar_browsing(
    *,
    base_url: str,
    locale: str,
    timeout: float = 30.0,
) -> dict[str, Any]:
    if locale not in {"en", "zh"}:
        raise ValueError("locale must be en or zh")
    provider = FullRadarHttpProvider(base_url, timeout=timeout, hydrate_limit=3)
    checks: list[dict[str, Any]] = []
    errors: list[str] = []

    overview = provider.get_radar_overview({"locale": locale})
    overview_data = dict(overview.data)
    overview_snapshot = str(overview_data.get("snapshot_id") or "")
    checks.append(
        {
            "id": "overview",
            "ok": True,
            "source_url": str(overview_data.get("source_url") or ""),
            "snapshot_id": overview_snapshot,
        }
    )

    dimension_summary: dict[str, Any] = {}
    for dimension, filter_name in DIMENSIONS:
        rows = _rows(overview_data.get(dimension))
        identifier = _row_id(rows[0]) if rows else ""
        dimension_summary[dimension] = {
            "count": len(rows),
            "sample_id": identifier,
        }
        if not identifier:
            errors.append(f"overview has no usable {dimension} entry")
            checks.append({"id": f"browse_{dimension}", "ok": False})
            continue
        output = provider.browse_radar_projects(
            {
                filter_name: identifier,
                "locale": locale,
                "limit": 3,
                "offset": 0,
            }
        )
        data = dict(output.data)
        checks.append(
            {
                "id": f"browse_{dimension}",
                "ok": bool(data.get("snapshot_id")),
                "sample_id": identifier,
                "returned": len(data.get("items") or []),
                "total": int(data.get("total") or 0),
                "snapshot_id": str(data.get("snapshot_id") or ""),
                "source_url": str(data.get("source_url") or ""),
            }
        )
        if not data.get("snapshot_id"):
            errors.append(f"{dimension} project browse is missing snapshot identity")

    skills = provider.browse_radar_skills(
        {"locale": locale, "limit": 3, "offset": 0}
    )
    skill_data = dict(skills.data)
    skill_items = _rows(skill_data.get("items"))
    skill_id = _row_id(skill_items[0]) if skill_items else ""
    checks.append(
        {
            "id": "browse_skills",
            "ok": True,
            "returned": len(skill_items),
            "total": int(skill_data.get("total") or 0),
            "sample_id": skill_id,
            "source_url": str(skill_data.get("source_url") or ""),
        }
    )
    skill_detail_ok = True
    if skill_id:
        detail = provider.browse_radar_skills(
            {"locale": locale, "skill_id": skill_id}
        )
        detail_data = dict(detail.data)
        skill_detail_ok = detail_data.get("found") is True and isinstance(detail_data.get("item"), Mapping)
        if not skill_detail_ok:
            errors.append("sample Skill detail did not return a public item")
    checks.append(
        {
            "id": "skill_detail",
            "ok": skill_detail_ok,
            "sample_id": skill_id,
        }
    )

    failed = [row["id"] for row in checks if row.get("ok") is not True]
    return {
        "schema_version": "osi.radar-browse-probe.v1",
        "ok": not errors and not failed,
        "base_url": base_url.rstrip("/"),
        "locale": locale,
        "overview_snapshot_id": overview_snapshot,
        "dimensions": dimension_summary,
        "checks": checks,
        "summary": {
            "passed": sum(1 for row in checks if row.get("ok") is True),
            "failed": sum(1 for row in checks if row.get("ok") is not True),
        },
        "errors": errors,
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="osi-probe-radar")
    parser.add_argument("--base-url", required=True)
    parser.add_argument("--locale", choices=("en", "zh"), required=True)
    parser.add_argument("--timeout", type=float, default=30.0)
    parser.add_argument("--output", type=Path)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        report = probe_radar_browsing(
            base_url=args.base_url,
            locale=args.locale,
            timeout=args.timeout,
        )
    except Exception as exc:
        report = {
            "schema_version": "osi.radar-browse-probe.v1",
            "ok": False,
            "base_url": args.base_url.rstrip("/"),
            "locale": args.locale,
            "errors": [str(exc)],
        }
    rendered = json.dumps(report, ensure_ascii=False, indent=2) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(rendered, encoding="utf-8")
    print(rendered, end="")
    return 0 if report.get("ok") is True else 1


if __name__ == "__main__":
    raise SystemExit(main())
