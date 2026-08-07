from __future__ import annotations

import hashlib
import json
import tempfile
import unittest
from pathlib import Path

from aiworkstation_osi.evidence_manifests import (
    EXPECTED_REPOSITORY,
    validate_ci_evidence,
    validate_live_validation_evidence,
)


class EvidenceManifestTests(unittest.TestCase):
    def test_ci_evidence_requires_both_python_versions_and_candidate_commit(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "ci-evidence.json"
            path.write_text(json.dumps({
                "schema_version": "osi.ci-evidence.v1",
                "workflow": "ci",
                "run_id": "12345",
                "run_attempt": "1",
                "commit": "candidate-sha",
                "repository": EXPECTED_REPOSITORY,
                "python_versions": ["3.10", "3.12"],
                "python310_passed": True,
                "python312_passed": True,
            }), encoding="utf-8")

            valid = validate_ci_evidence(path, candidate_commit="candidate-sha")
            stale = validate_ci_evidence(path, candidate_commit="different-sha")

        self.assertTrue(valid["ok"])
        self.assertTrue(valid["python310_passed"])
        self.assertTrue(valid["python312_passed"])
        self.assertFalse(stale["ok"])
        self.assertIn("different candidate commit", " ".join(stale["errors"]))

    def _live_bundle(self, root: Path) -> Path:
        for locale in ("en", "zh"):
            directory = root / f"contracts-{locale}"
            directory.mkdir(parents=True, exist_ok=True)
            for filename in (
                "manifest.json",
                "project-list.json",
                "project-detail.json",
                "selector-formal.json",
                "selector-no-match.json",
            ):
                (directory / filename).write_text(
                    json.dumps({"locale": locale, "file": filename}) + "\n",
                    encoding="utf-8",
                )
        for filename in (
            "probe-en.json",
            "probe-zh.json",
            "replay-en.json",
            "replay-zh.json",
        ):
            (root / filename).write_text('{"ok":true}\n', encoding="utf-8")
        (root / "SUMMARY.md").write_text("validated\n", encoding="utf-8")

        files = {
            path.relative_to(root).as_posix(): hashlib.sha256(path.read_bytes()).hexdigest()
            for path in sorted(root.rglob("*"))
            if path.is_file()
        }
        evidence_path = root / "validation-evidence.json"
        evidence_path.write_text(json.dumps({
            "schema_version": "osi.live-validation-evidence.v1",
            "workflow": "live-contract-validation",
            "run_id": "67890",
            "run_attempt": "1",
            "commit": "candidate-sha",
            "repository": EXPECTED_REPOSITORY,
            "base_url": "https://aiworkstation.cn",
            "project_id": "infiniflow/ragflow",
            "contracts": {"en": "contracts-en", "zh": "contracts-zh"},
            "checks": {
                "probe_en": True,
                "probe_zh": True,
                "contract_validate_en": True,
                "contract_validate_zh": True,
                "replay_en": True,
                "replay_zh": True,
                "forbidden_key_scan": True,
            },
            "files": files,
        }), encoding="utf-8")
        return evidence_path

    def test_live_validation_evidence_binds_contracts_and_file_digests(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            path = self._live_bundle(root)
            result = validate_live_validation_evidence(
                path,
                candidate_commit="candidate-sha",
                expected_base_url="https://aiworkstation.cn",
            )

        self.assertTrue(result["ok"])
        self.assertEqual(result["run_id"], "67890")
        self.assertTrue(result["contracts_en"].endswith("contracts-en"))
        self.assertTrue(result["contracts_zh"].endswith("contracts-zh"))
        self.assertGreaterEqual(result["verified_file_count"], 15)

    def test_live_validation_tamper_or_wrong_origin_fails_closed(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            path = self._live_bundle(root)
            (root / "probe-en.json").write_text('{"ok":false}\n', encoding="utf-8")
            result = validate_live_validation_evidence(
                path,
                candidate_commit="candidate-sha",
                expected_base_url="https://useaistation.com",
            )

        self.assertFalse(result["ok"])
        errors = " ".join(result["errors"])
        self.assertIn("different Radar origin", errors)
        self.assertIn("digest mismatch", errors)

    def test_live_validation_rejects_unsafe_contract_path(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            path = self._live_bundle(root)
            payload = json.loads(path.read_text(encoding="utf-8"))
            payload["contracts"]["en"] = "../outside"
            path.write_text(json.dumps(payload), encoding="utf-8")
            result = validate_live_validation_evidence(
                path,
                candidate_commit="candidate-sha",
                expected_base_url="https://aiworkstation.cn",
            )

        self.assertFalse(result["ok"])
        self.assertIn("en contract directory", " ".join(result["errors"]))

    def test_live_validation_requires_hash_coverage_for_each_contract_fixture(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            path = self._live_bundle(root)
            payload = json.loads(path.read_text(encoding="utf-8"))
            payload["files"].pop("contracts-en/project-detail.json")
            path.write_text(json.dumps(payload), encoding="utf-8")
            result = validate_live_validation_evidence(
                path,
                candidate_commit="candidate-sha",
                expected_base_url="https://aiworkstation.cn",
            )

        self.assertFalse(result["ok"])
        self.assertIn(
            "digest manifest does not cover contracts-en/project-detail.json",
            " ".join(result["errors"]),
        )


if __name__ == "__main__":
    unittest.main()
