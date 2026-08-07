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
from aiworkstation_osi.fixture_replay import FixtureReplayTransport, replay_contract_directory


def project() -> dict[str, Any]:
    return {
        "id": "ragflow",
        "owner": "infiniflow",
        "repo": "ragflow",
        "full_name": "infiniflow/ragflow",
        "name": "RAGFlow",
    }


def fixture(scenario: str, payload: dict[str, Any]) -> dict[str, Any]:
    return {
        "schema_version": FIXTURE_SCHEMA_VERSION,
        "scenario": scenario,
        "request_fingerprint": "sha256:" + "b" * 64,
        "observed_at": "2026-08-06T14:00:00Z",
        "status": 200,
        "headers": {"content-type": "application/json", "etag": '"fixture"'},
        "payload": payload,
    }


def write_replay_directory(root: Path) -> None:
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
                    "summary": "Public RAG platform summary.",
                    "license": "Apache-2.0",
                    "deployment": ["self-hosted", "docker"],
                    "languages": ["Python"],
                    "stars": 100,
                    "updated_at": "2026-08-05T00:00:00Z",
                    "categories": ["rag"],
                    "use_cases": ["knowledge-base"],
                    "archived": False,
                    "interpretation": {
                        "coverage_level": "EN_L2",
                        "transparency": {
                            "published_at": "2026-08-06T13:00:00Z",
                            "source_updated_at": "2026-08-06T12:00:00Z",
                            "quality_label": "Deterministically validated and independently reviewed",
                            "sources": [
                                {
                                    "source_label": "README",
                                    "source_path": "README.md",
                                    "section_heading": "Deployment",
                                    "excerpt": "Self-host with Docker.",
                                },
                                {
                                    "source_label": "License",
                                    "source_path": "LICENSE",
                                    "section_heading": "License",
                                    "excerpt": "Licensed under Apache-2.0.",
                                },
                            ],
                        },
                    },
                },
            },
        ),
        "selector-formal.json": fixture(
            "selector-formal",
            {
                "evidence_status": "available",
                "result_kind": "projects",
                "items": [project()],
                "near_matches": [],
            },
        ),
        "selector-no-match.json": fixture(
            "selector-no-match",
            {
                "evidence_status": "available",
                "items": [],
                "near_matches": [],
                "no_match_reason": "No project satisfies every hard requirement.",
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


class FixtureReplayTests(unittest.TestCase):
    def test_valid_capture_replays_through_production_provider(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            write_replay_directory(root)
            report = replay_contract_directory(root)

        self.assertTrue(report["ok"])
        self.assertEqual(report["summary"]["failed"], 0)
        by_id = {check["id"]: check for check in report["checks"]}
        self.assertTrue(by_id["project-snapshot"]["ok"])
        self.assertTrue(by_id["license-boundary"]["ok"])
        self.assertEqual(by_id["license-boundary"]["details"]["license"], "Apache-2.0")
        self.assertTrue(by_id["selector-honesty"]["ok"])
        self.assertTrue(by_id["no-match-replay"]["ok"])
        formal_paths = {call["path"] for call in report["request_summary"]["formal_calls"]}
        self.assertIn("/api/v1/ai/githubai/projects", formal_paths)
        self.assertIn("/api/v1/ai/githubai/selector", formal_paths)

    def test_invalid_capture_returns_validation_failure_without_replay(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            write_replay_directory(root)
            (root / "selector-no-match.json").unlink()
            report = replay_contract_directory(root)

        self.assertFalse(report["ok"])
        self.assertFalse(report["validation"]["ok"])
        self.assertEqual(report["checks"], [])

    def test_replay_transport_rejects_unknown_selector_mode(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            write_replay_directory(root)
            with self.assertRaises(ValueError):
                FixtureReplayTransport(root, selector_scenario="unexpected")


if __name__ == "__main__":
    unittest.main()
