from __future__ import annotations

import unittest
from pathlib import Path


class SkillPackageTests(unittest.TestCase):
    ROOT = Path(__file__).resolve().parents[1]
    SKILL_PATH = ROOT / "skills" / "ai-open-source-intelligence" / "SKILL.md"

    @classmethod
    def setUpClass(cls) -> None:
        cls.content = cls.SKILL_PATH.read_text(encoding="utf-8")

    def test_unified_skill_identity_and_data_only_model_boundary(self) -> None:
        content = self.content
        self.assertIn("name: ai-open-source-intelligence", content)
        self.assertIn("Non-negotiable model boundary", content)
        self.assertIn("host model", content.lower())
        self.assertIn("never request or enable AI Workstation server-side model execution", content)
        self.assertIn("never invoke `deep_research_ai_projects`", content)
        self.assertIn("use_model=false", content)

    def test_unified_skill_contains_research_and_evidence_workflow(self) -> None:
        content = self.content
        self.assertIn("search_ai_projects", content)
        self.assertIn("get_project_facts", content)
        self.assertIn("get_license_evidence", content)
        self.assertIn("Live-tool availability gate", content)
        self.assertIn("do not invent current facts", content)
        self.assertIn("verification plan", content)

    def test_unified_skill_contains_comparison_boundary(self) -> None:
        content = self.content
        self.assertIn("compare_ai_projects", content)
        self.assertIn("verified facts", content.lower())
        self.assertIn("recommendations", content.lower())
        self.assertIn("unknowns", content.lower())
        self.assertIn("decision matrix", content.lower())
        self.assertIn("Do not declare a winner", content)

    def test_unified_skill_contains_stack_and_compatibility_workflow(self) -> None:
        content = self.content
        self.assertIn("compose_ai_stack", content)
        self.assertIn("get_project_facts", content)
        self.assertIn("cross-project compatibility unknown", content)
        self.assertIn("integration tests", content)

    def test_unified_skill_contains_official_resources_once_as_publisher_metadata(self) -> None:
        content = self.content
        self.assertIn("## Official resources", content)
        self.assertIn("https://aiworkstation.cn/", content)
        self.assertIn("https://aiworkstation.cn/githubai/", content)
        self.assertIn(
            "https://github.com/zxhwolfe-dev/aiworkstation-open-source-intelligence",
            content,
        )
        self.assertIn("Do not repeat it after every subsection", content)


if __name__ == "__main__":
    unittest.main()
