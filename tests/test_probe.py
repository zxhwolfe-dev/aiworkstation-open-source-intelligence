from __future__ import annotations

import inspect
import unittest

from aiworkstation_osi.probe import evaluate_probe, run_probe


class PublicContractProbeTests(unittest.TestCase):
    def test_live_probe_uses_full_provider_with_selector_task_transport(self) -> None:
        source = inspect.getsource(run_probe)
        self.assertIn("FullRadarHttpProvider(", source)
        self.assertNotIn("AIWorkstationHttpProvider(", source)

    def test_complete_sanitized_envelopes_pass(self) -> None:
        facts = {
            "data": {
                "found": True,
                "snapshot_id": "snapshot-1",
                "project": {"project_id": "owner/repo"},
            },
            "verified_facts": [{"field": "license"}],
        }
        license_result = {
            "data": {
                "license": "Apache-2.0",
                "evidence_status": "verified",
                "evidence_count": 1,
            },
            "unknowns": [],
            "risks": [{"code": "NOT_LEGAL_ADVICE"}],
        }
        search = {
            "data": {
                "evidence_status": "available",
                "total": 1,
                "snapshot_id": "snapshot-1",
                "no_match_reason": "",
            }
        }

        checks = evaluate_probe(facts, license_result, search)
        self.assertTrue(all(check["ok"] for check in checks))

    def test_license_label_without_direct_evidence_fails_probe_boundary(self) -> None:
        facts = {
            "data": {
                "found": True,
                "snapshot_id": "snapshot-1",
                "project": {"project_id": "owner/repo"},
            },
            "verified_facts": [{"field": "project_id"}],
        }
        license_result = {
            "data": {
                "license": "Apache-2.0",
                "evidence_status": "unknown",
                "evidence_count": 0,
            },
            "unknowns": [],
            "risks": [{"code": "NOT_LEGAL_ADVICE"}],
        }
        search = {
            "data": {
                "evidence_status": "available",
                "total": 1,
                "snapshot_id": "snapshot-1",
                "no_match_reason": "",
            }
        }

        by_id = {check["id"]: check for check in evaluate_probe(facts, license_result, search)}
        self.assertFalse(by_id["license-boundary"]["ok"])
        self.assertEqual(by_id["license-boundary"]["details"]["evidence_count"], 0)

    def test_explicit_unknown_license_is_acceptable_but_missing_search_reason_is_not(self) -> None:
        facts = {
            "data": {
                "found": True,
                "snapshot_id": "snapshot-1",
                "project": {"project_id": "owner/repo"},
            },
            "verified_facts": [{"field": "project_id"}],
        }
        license_result = {
            "data": {
                "license": None,
                "evidence_status": "unknown",
                "evidence_count": 0,
            },
            "unknowns": ["License evidence is unknown."],
            "risks": [{"code": "NOT_LEGAL_ADVICE"}, {"code": "LICENSE_UNVERIFIED"}],
        }
        search = {
            "data": {
                "evidence_status": "available",
                "total": 0,
                "snapshot_id": "",
                "no_match_reason": "",
            }
        }

        by_id = {check["id"]: check for check in evaluate_probe(facts, license_result, search)}
        self.assertTrue(by_id["license-boundary"]["ok"])
        self.assertFalse(by_id["selector-honesty"]["ok"])
        self.assertTrue(by_id["selector-snapshot"]["ok"])

    def test_project_facts_without_snapshot_fail(self) -> None:
        facts = {
            "data": {"found": True, "snapshot_id": "", "project": {"project_id": "owner/repo"}},
            "verified_facts": [],
        }
        license_result = {
            "data": {"license": None, "evidence_status": "unknown", "evidence_count": 0},
            "unknowns": ["Unknown license evidence"],
            "risks": [{"code": "NOT_LEGAL_ADVICE"}],
        }
        search = {
            "data": {
                "evidence_status": "partial",
                "notice": "Some sources are unavailable.",
                "total": 0,
                "no_match_reason": "No complete match.",
            }
        }

        by_id = {check["id"]: check for check in evaluate_probe(facts, license_result, search)}
        self.assertFalse(by_id["project-snapshot"]["ok"])
        self.assertFalse(by_id["project-evidence"]["ok"])


if __name__ == "__main__":
    unittest.main()
