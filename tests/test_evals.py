from __future__ import annotations

import json
import unittest
from collections import Counter
from pathlib import Path

from aiworkstation_osi.contracts import TOOL_NAMES
from aiworkstation_osi.app import invoke_tool


class EvaluationCorpusTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        path = Path(__file__).resolve().parents[1] / "evals" / "cases.json"
        cls.payload = json.loads(path.read_text(encoding="utf-8"))

    def test_schema_and_case_ids(self) -> None:
        self.assertEqual(self.payload["schema_version"], "osi.evals.v1")
        case_ids = [case["id"] for case in self.payload["cases"]]
        self.assertEqual(len(case_ids), len(set(case_ids)))

    def test_initial_corpus_is_bilingual_and_balanced(self) -> None:
        counts = Counter(case["locale"] for case in self.payload["cases"])
        self.assertGreaterEqual(counts["zh"], 8)
        self.assertGreaterEqual(counts["en"], 8)

    def test_every_case_targets_declared_tool_and_behavior(self) -> None:
        for case in self.payload["cases"]:
            with self.subTest(case=case["id"]):
                self.assertIn(case["tool"], TOOL_NAMES)
                self.assertIsInstance(case["arguments"], dict)
                self.assertTrue(case["expects"])

    def test_corpus_executes_deterministically(self) -> None:
        for case in self.payload["cases"]:
            with self.subTest(case=case["id"]):
                try:
                    result = invoke_tool(case["tool"], case["arguments"])
                except Exception as exc:
                    self.assertIn(case["tool"], {"search_ai_projects", "find_alternatives", "compose_ai_stack"})
                    self.assertIn("Unsupported required constraint", str(exc))
                else:
                    self.assertEqual(result["tool"], case["tool"])
                    self.assertEqual(result["schema_version"], "osi.tool-result.v2")


if __name__ == "__main__":
    unittest.main()
