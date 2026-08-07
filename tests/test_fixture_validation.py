from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path
from typing import Any

from aiworkstation_osi.contract_capture import (
    CAPTURE_SCHEMA_VERSION,
    FIXTURE_SCHEMA_VERSION,
    REMOVED_KEYS,
)
from aiworkstation_osi.fixture_validation import validate_contract_directory


def project() -> dict[str, Any]:
    return {
        "id": "ragflow",
        "owner": "infiniflow",
        "repo": "ragflow",
        "full_name": "infiniflow/ragflow",
    }


def fixture(scenario: str, payload: dict[str, Any]) -> dict[str, Any]:
    return {
        "schema_version": FIXTURE_SCHEMA_VERSION,
        "scenario": scenario,
        "request_fingerprint": "sha256:" + "a" * 64,
        "observed_at": "2026-08-06T14:00:00Z",
        "status": 200,
        "headers": {"content-type": "application/json", "etag": '"fixture"'},
        "payload": payload,
    }


def write_valid_directory(root: Path) -> None:
    files = {
        "project-list.json": fixture(
            "project-list",
            {"snapshot_id": "snapshot-1", "items": [project()]},
        ),
        "project-detail.json": fixture(
            "project-detail",
            {
                "snapshot_id": "snapshot-1",
                "item": {
                    **project(),
                    "summary": "Public project summary.",
                    "license": "Apache-2.0",
                },
            },
        ),
        "selector-formal.json": fixture(
            "selector-formal",
            {"evidence_status": "available", "items": [project()]},
        ),
        "selector-no-match.json": fixture(
            "selector-no-match",
            {
                "evidence_status": "available",
                "items": [],
                "no_match_reason": "No project satisfies every hard requirement.",
                "near_matches": [],
            },
        ),
    }
    manifest = {
        "schema_version": CAPTURE_SCHEMA_VERSION,
        "generated_at": "2026-08-06T14:00:00Z",
        "locale": "en",
        "project_id": "infiniflow/ragflow",
        "fixture_files": sorted(files),
        "sanitization": {
            "removed_keys": sorted(REMOVED_KEYS),
            "max_string_length": 500,
            "max_list_items": 20,
            "stores_query_text": False,
        },
    }
    root.mkdir(parents=True, exist_ok=True)
    (root / "manifest.json").write_text(json.dumps(manifest), encoding="utf-8")
    for filename, payload in files.items():
        (root / filename).write_text(json.dumps(payload), encoding="utf-8")


class FixtureValidationTests(unittest.TestCase):
    def test_valid_directory_passes(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            write_valid_directory(root)
            report = validate_contract_directory(root)

        self.assertTrue(report["ok"])
        self.assertEqual(report["summary"], {"errors": 0, "warnings": 0})

    def test_removed_key_and_unsafe_header_fail(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            write_valid_directory(root)
            path = root / "project-detail.json"
            payload = json.loads(path.read_text(encoding="utf-8"))
            payload["headers"]["authorization"] = "Bearer secret"
            payload["payload"]["source_hash"] = "internal"
            path.write_text(json.dumps(payload), encoding="utf-8")
            report = validate_contract_directory(root)

        self.assertFalse(report["ok"])
        rendered = " ".join(report["errors"])
        self.assertIn("unsafe headers", rendered)
        self.assertIn("source_hash", rendered)

    def test_no_match_fixture_cannot_contain_formal_project(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            write_valid_directory(root)
            path = root / "selector-no-match.json"
            payload = json.loads(path.read_text(encoding="utf-8"))
            payload["payload"]["items"] = [project()]
            path.write_text(json.dumps(payload), encoding="utf-8")
            report = validate_contract_directory(root)

        self.assertFalse(report["ok"])
        self.assertTrue(
            any("no-match fixture contains formal projects" in value for value in report["errors"])
        )

    def test_detail_without_direct_snapshot_is_warning_when_list_identity_is_safe(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            write_valid_directory(root)
            path = root / "project-detail.json"
            payload = json.loads(path.read_text(encoding="utf-8"))
            payload["payload"].pop("snapshot_id")
            path.write_text(json.dumps(payload), encoding="utf-8")
            report = validate_contract_directory(root)

        self.assertTrue(report["ok"])
        self.assertEqual(report["summary"]["warnings"], 1)
        self.assertIn("no direct snapshot identity", report["warnings"][0])

    def test_formal_and_near_match_cannot_coexist(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            write_valid_directory(root)
            path = root / "selector-formal.json"
            payload = json.loads(path.read_text(encoding="utf-8"))
            payload["payload"]["near_matches"] = [
                {
                    "status": "near_match",
                    "project": {
                        "id": "alternative",
                        "owner": "owner",
                        "repo": "alternative",
                        "full_name": "owner/alternative",
                    },
                    "blocking_constraints": [{"id": "license", "status": "unverified"}],
                }
            ]
            path.write_text(json.dumps(payload), encoding="utf-8")
            report = validate_contract_directory(root)

        self.assertFalse(report["ok"])
        self.assertTrue(any("coexist" in value for value in report["errors"]))


if __name__ == "__main__":
    unittest.main()
