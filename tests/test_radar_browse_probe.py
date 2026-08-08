from __future__ import annotations

import unittest
from unittest.mock import patch

from aiworkstation_osi.providers import ProviderOutput
from aiworkstation_osi.radar_browse_probe import probe_radar_browsing


class FakeRadarProvider:
    def __init__(self, *args, **kwargs):
        self.project_calls = []
        self.skill_calls = []

    def get_radar_overview(self, request):
        return ProviderOutput(
            data={
                "snapshot_id": "sha256:overview",
                "source_url": "https://aiworkstation.cn/api/v1/ai/githubai/overview",
                "rankings": [{"id": "daily"}],
                "collections": [{"id": "rag"}],
                "categories": [{"id": "rag"}],
                "scenarios": [{"id": "knowledge-base"}],
            }
        )

    def browse_radar_projects(self, request):
        self.project_calls.append(dict(request))
        return ProviderOutput(
            data={
                "items": [{"id": "infiniflow/ragflow"}],
                "total": 1,
                "snapshot_id": "sha256:projects",
                "source_url": "https://aiworkstation.cn/api/v1/ai/githubai/projects",
            }
        )

    def browse_radar_skills(self, request):
        self.skill_calls.append(dict(request))
        if request.get("skill_id"):
            return ProviderOutput(
                data={
                    "found": True,
                    "item": {"id": request["skill_id"]},
                    "source_url": "https://aiworkstation.cn/api/v1/ai/githubai/skills/detail",
                }
            )
        return ProviderOutput(
            data={
                "items": [{"id": "open-source-project-research"}],
                "total": 1,
                "source_url": "https://aiworkstation.cn/api/v1/ai/githubai/skills",
            }
        )


class RadarBrowseProbeTests(unittest.TestCase):
    def test_probe_exercises_all_navigation_dimensions_and_skill_detail(self) -> None:
        fake = FakeRadarProvider()
        with patch(
            "aiworkstation_osi.radar_browse_probe.FullRadarHttpProvider",
            return_value=fake,
        ):
            report = probe_radar_browsing(
                base_url="https://aiworkstation.cn",
                locale="en",
            )
        self.assertTrue(report["ok"])
        self.assertEqual(report["summary"], {"passed": 7, "failed": 0})
        self.assertEqual(
            fake.project_calls,
            [
                {"ranking": "daily", "locale": "en", "limit": 3, "offset": 0},
                {"collection": "rag", "locale": "en", "limit": 3, "offset": 0},
                {"category": "rag", "locale": "en", "limit": 3, "offset": 0},
                {"scenario": "knowledge-base", "locale": "en", "limit": 3, "offset": 0},
            ],
        )
        self.assertEqual(fake.skill_calls[0], {"locale": "en", "limit": 3, "offset": 0})
        self.assertEqual(
            fake.skill_calls[1],
            {"locale": "en", "skill_id": "open-source-project-research"},
        )

    def test_missing_navigation_dimension_fails_closed(self) -> None:
        fake = FakeRadarProvider()
        original = fake.get_radar_overview

        def missing_collection(request):
            output = original(request)
            data = dict(output.data)
            data["collections"] = []
            return ProviderOutput(data=data)

        fake.get_radar_overview = missing_collection
        with patch(
            "aiworkstation_osi.radar_browse_probe.FullRadarHttpProvider",
            return_value=fake,
        ):
            report = probe_radar_browsing(
                base_url="https://aiworkstation.cn",
                locale="zh",
            )
        self.assertFalse(report["ok"])
        self.assertIn("overview has no usable collections entry", report["errors"])
        failed = [row["id"] for row in report["checks"] if row.get("ok") is not True]
        self.assertIn("browse_collections", failed)

    def test_invalid_locale_is_rejected_before_network(self) -> None:
        with self.assertRaises(ValueError):
            probe_radar_browsing(base_url="https://aiworkstation.cn", locale="fr")


if __name__ == "__main__":
    unittest.main()
