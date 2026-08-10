from __future__ import annotations

import json
import unittest

from aiworkstation_osi.contracts import Evidence, Recommendation, Risk, ToolResult, VerifiedFact


class ToolResultContractTests(unittest.TestCase):
    def test_result_serializes_four_product_boundaries(self) -> None:
        result = ToolResult(
            tool="get_project_facts",
            data={"project_id": "owner/repo"},
            verified_facts=(
                VerifiedFact(
                    field="license",
                    value="Apache-2.0",
                    confidence="high",
                    evidence=(
                        Evidence(
                            source_url="https://github.com/owner/repo/blob/main/LICENSE",
                            observed_at="2026-08-01T00:00:00Z",
                            supports=("license",),
                        ),
                    ),
                ),
            ),
            recommendations=(Recommendation(summary="Verify commercial-use obligations."),),
            unknowns=("Deployment support was not verified.",),
            risks=(Risk(code="NOT_LEGAL_ADVICE", message="Technical evidence only."),),
            request_id="request-1",
        )

        payload = result.to_dict()
        encoded = json.dumps(payload, ensure_ascii=False)

        self.assertEqual(payload["schema_version"], "osi.tool-result.v2")
        self.assertFalse(payload["execution"]["business_data_write"])
        self.assertEqual(payload["tool"], "get_project_facts")
        self.assertEqual(payload["verified_facts"][0]["field"], "license")
        self.assertEqual(payload["recommendations"][0]["summary"], "Verify commercial-use obligations.")
        self.assertEqual(payload["unknowns"], ["Deployment support was not verified."])
        self.assertIn("NOT_LEGAL_ADVICE", encoded)
        self.assertTrue(payload["generated_at"].endswith("Z"))


if __name__ == "__main__":
    unittest.main()
