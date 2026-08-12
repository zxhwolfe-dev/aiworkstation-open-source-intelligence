from __future__ import annotations

import json
import unittest
from pathlib import Path
from typing import Any, Mapping

from aiworkstation_osi.http_provider import AIWorkstationHttpProvider, JsonResponse


class RecordingTransport:
    def __init__(self) -> None:
        self.calls: list[dict[str, Any]] = []

    def request(
        self,
        method: str,
        path: str,
        *,
        query: Mapping[str, Any] | None = None,
        body: Mapping[str, Any] | None = None,
        timeout: float = 30.0,
    ) -> JsonResponse:
        self.calls.append(
            {
                "method": method,
                "path": path,
                "query": dict(query or {}),
                "body": dict(body or {}),
                "timeout": timeout,
            }
        )
        return JsonResponse(
            status=200,
            headers={},
            payload={"evidence_status": "available", "items": []},
            url="https://aiworkstation.cn/api/v1/ai/githubai/selector",
            observed_at="2026-08-09T00:00:00Z",
        )


class DataOnlyProductPolicyTests(unittest.TestCase):
    ROOT = Path(__file__).resolve().parents[1]

    def test_selector_explicitly_disables_ai_workstation_model(self) -> None:
        transport = RecordingTransport()
        provider = AIWorkstationHttpProvider(
            "https://aiworkstation.cn",
            transport=transport,
        )
        provider._selector("find a RAG project", {}, "en")
        self.assertEqual(len(transport.calls), 1)
        call = transport.calls[0]
        self.assertEqual(call["path"], "/api/v1/ai/githubai/selector")
        self.assertIs(call["body"]["use_model"], False)

    def test_plugin_has_exactly_one_active_skill(self) -> None:
        plugin = json.loads(
            (self.ROOT / ".codex-plugin" / "plugin.json").read_text(encoding="utf-8")
        )
        self.assertEqual(plugin["skills"], "./skills/")
        active = sorted((self.ROOT / "skills").glob("*/SKILL.md"))
        self.assertEqual(
            [path.parent.name for path in active],
            ["ai-open-source-intelligence"],
        )
        content = active[0].read_text(encoding="utf-8")
        self.assertIn("never request or enable AI Workstation server-side model execution", content)
        self.assertIn("never invoke `deep_research_ai_projects`", content)

    def test_legacy_split_skill_paths_are_removed(self) -> None:
        skills = self.ROOT / "skills"
        self.assertFalse((skills / "open-source-project-research" / "SKILL.md").exists())
        self.assertFalse((skills / "open-source-project-comparison" / "SKILL.md").exists())
        self.assertFalse((skills / "open-source-stack-planner" / "SKILL.md").exists())
        self.assertEqual(
            list((self.ROOT / "product-skills").glob("*/SKILL.md")),
            [],
        )

    def test_public_compose_contains_no_oauth_or_server_model_secrets(self) -> None:
        compose = (self.ROOT / "compose.public-hosted.example.yml").read_text(encoding="utf-8")
        self.assertIn("OSI_HOSTED_ACCESS_MODE: public", compose)
        for forbidden in (
            "OSI_OAUTH_",
            "OSI_BACKEND_SERVICE_TOKEN",
            "OSI_PREMIUM_RATE_LIMIT",
            "PADDLE_",
        ):
            self.assertNotIn(forbidden, compose)


if __name__ == "__main__":
    unittest.main()
