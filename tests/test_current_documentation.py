from __future__ import annotations

import re
import unittest
from pathlib import Path


class CurrentDocumentationTests(unittest.TestCase):
    ROOT = Path(__file__).resolve().parents[1]
    CURRENT_SURFACES = (
        "README.md",
        "README.zh-CN.md",
        "CONTRIBUTING.md",
        "ROADMAP.md",
        "docs/QUICKSTART.md",
        "docs/FAQ.md",
        "docs/WEBSITE-LAUNCH-COPY.md",
        "docs/alpha-tester-guide.md",
        "docs/architecture.md",
        "docs/codex-setup.md",
        "docs/error-codes.md",
        "docs/external-alpha-checklist.md",
        "docs/hosted-mcp.md",
        "docs/openai-plugin-submission.md",
        "docs/security-and-privacy.md",
    )

    def test_current_surfaces_do_not_restore_pre_v030_counts_or_broken_url(self) -> None:
        forbidden = (
            re.compile(r"\bsix read-only (?:MCP )?tools\b", re.IGNORECASE),
            re.compile(r"\bsix-tool (?:product|live|Codex|surface)\b", re.IGNORECASE),
            re.compile(r"\bthree reusable Skills\b", re.IGNORECASE),
            re.compile(r"\bprivate-alpha capable\b", re.IGNORECASE),
            re.compile(r"六个只读工具"),
            re.compile(r"https://useaistation\.com/githubai/terms/"),
        )
        failures: list[str] = []
        for relative in self.CURRENT_SURFACES:
            content = (self.ROOT / relative).read_text(encoding="utf-8")
            for pattern in forbidden:
                if pattern.search(content):
                    failures.append(f"{relative}: {pattern.pattern}")
        self.assertEqual(failures, [])

    def test_quickstart_covers_current_install_paths(self) -> None:
        content = (self.ROOT / "docs/QUICKSTART.md").read_text(encoding="utf-8")
        self.assertIn("https://mcp.aiworkstation.cn/mcp", content)
        self.assertIn("Authentication: No Authentication", content)
        self.assertIn("aiworkstation-open-source-intelligence[mcp]==0.3.0", content)
        self.assertIn("codex plugin marketplace add", content)
        self.assertIn("get_radar_overview", content)
        self.assertIn("browse_radar_projects", content)
        self.assertIn("browse_radar_skills", content)
        self.assertIn("single install includes both", content)
        self.assertIn("--ref main", content)

    def test_current_package_documents_one_install_without_rewriting_v030(self) -> None:
        manifest = (self.ROOT / ".codex-plugin" / "plugin.json").read_text(encoding="utf-8")
        packaging = (self.ROOT / "docs/plugin-packaging.md").read_text(encoding="utf-8")
        self.assertIn('"mcpServers": "./.mcp.json"', manifest)
        self.assertIn("hosted_mcp_config_bundled=true", packaging)
        self.assertIn("v0.3.0", packaging)
        self.assertIn("immutable", packaging)

    def test_current_docs_distinguish_hosted_runtime_from_directory_approval(self) -> None:
        faq = (self.ROOT / "docs/FAQ.md").read_text(encoding="utf-8")
        submission = (self.ROOT / "docs/openai-plugin-submission.md").read_text(encoding="utf-8")
        self.assertIn("Yes. `v0.3.0` is deployed", faq)
        self.assertIn("not yet submitted or approved", submission)


if __name__ == "__main__":
    unittest.main()
