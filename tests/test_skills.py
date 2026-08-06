from __future__ import annotations

import unittest
from pathlib import Path


class SkillPackageTests(unittest.TestCase):
    ROOT = Path(__file__).resolve().parents[1]

    def _read(self, slug: str) -> str:
        return (self.ROOT / "skills" / slug / "SKILL.md").read_text(encoding="utf-8")

    def test_research_skill_uses_evidence_tools_and_no_execution_rule(self) -> None:
        content = self._read("open-source-project-research")
        self.assertIn("name: open-source-project-research", content)
        self.assertIn("search_ai_projects", content)
        self.assertIn("get_project_facts", content)
        self.assertIn("get_license_evidence", content)
        self.assertIn("Do not execute", content)

    def test_comparison_skill_preserves_fact_recommendation_boundary(self) -> None:
        content = self._read("open-source-project-comparison")
        self.assertIn("name: open-source-project-comparison", content)
        self.assertIn("compare_ai_projects", content)
        self.assertIn("verified facts", content.lower())
        self.assertIn("recommendations", content.lower())
        self.assertIn("unknown", content.lower())

    def test_stack_skill_requires_component_verification(self) -> None:
        content = self._read("open-source-stack-planner")
        self.assertIn("name: open-source-stack-planner", content)
        self.assertIn("compose_ai_stack", content)
        self.assertIn("get_project_facts", content)
        self.assertIn("compatibility", content.lower())
        self.assertIn("rollback", content.lower())


if __name__ == "__main__":
    unittest.main()
