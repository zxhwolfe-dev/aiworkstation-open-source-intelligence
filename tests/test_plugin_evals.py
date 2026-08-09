from __future__ import annotations

import json
import unittest
from collections import Counter
from pathlib import Path

from aiworkstation_osi.contracts import TOOL_NAMES


class PluginEvaluationCorpusTests(unittest.TestCase):
    ROOT = Path(__file__).resolve().parents[1]

    @classmethod
    def setUpClass(cls) -> None:
        cls.payload = json.loads(
            (cls.ROOT / "evals" / "plugin-cases.json").read_text(encoding="utf-8")
        )

    def test_schema_and_unique_case_ids(self) -> None:
        self.assertEqual(self.payload["schema_version"], "osi.plugin-evals.v1")
        case_ids = [case["id"] for case in self.payload["cases"]]
        self.assertEqual(len(case_ids), len(set(case_ids)))

    def test_corpus_is_bilingual_and_targets_only_unified_skill(self) -> None:
        locale_counts = Counter(case["locale"] for case in self.payload["cases"])
        self.assertGreaterEqual(locale_counts["en"], 4)
        self.assertGreaterEqual(locale_counts["zh"], 4)
        self.assertEqual(
            {case["skill"] for case in self.payload["cases"]},
            {"ai-open-source-intelligence"},
        )

    def test_every_case_has_expects_forbids_and_declared_tools(self) -> None:
        declared_tools = set(TOOL_NAMES)
        for case in self.payload["cases"]:
            with self.subTest(case=case["id"]):
                self.assertIn(case["locale"], {"zh", "en"})
                self.assertEqual(case["skill"], "ai-open-source-intelligence")
                self.assertTrue(case["prompt"].strip())
                self.assertGreaterEqual(len(case["expects"]), 3)
                self.assertGreaterEqual(len(case["forbids"]), 3)
                self.assertTrue(set(case["tools_available"]).issubset(declared_tools))

    def test_skills_only_cases_require_honest_fallback(self) -> None:
        skills_only = [case for case in self.payload["cases"] if not case["tools_available"]]
        self.assertGreaterEqual(len(skills_only), 3)
        rendered = " ".join(
            text.lower()
            for case in skills_only
            for text in [*case["expects"], *case["forbids"]]
        )
        self.assertIn("live evidence", rendered)
        self.assertIn("实时证据", rendered)
        self.assertIn("model memory", rendered)
        self.assertIn("凭印象", rendered)
        self.assertIn("server-side model", rendered)
        self.assertIn("服务器模型", rendered)

    def test_corpus_never_permits_premium_or_server_model_fallback(self) -> None:
        forbids = " ".join(
            text.lower()
            for case in self.payload["cases"]
            for text in case["forbids"]
        )
        self.assertIn("deep_research_ai_projects", forbids)
        self.assertTrue(
            "server-side model" in forbids
            or "publisher model" in forbids
            or "网站大模型" in forbids
        )


if __name__ == "__main__":
    unittest.main()
