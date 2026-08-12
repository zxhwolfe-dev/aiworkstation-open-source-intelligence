from __future__ import annotations

import hashlib
import json
import tempfile
import unittest
import zipfile
from pathlib import Path

from aiworkstation_osi.alpha_bundle import BUNDLE_SCHEMA_VERSION, build_alpha_bundle


class AlphaBundleTests(unittest.TestCase):
    ROOT = Path(__file__).resolve().parents[1]

    def test_bundle_contains_one_reviewed_complete_plugin_surface(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            report = build_alpha_bundle(self.ROOT, Path(temp_dir))
            archive = Path(report["archive"])
            with zipfile.ZipFile(archive) as bundle:
                names = set(bundle.namelist())
                manifest = json.loads(bundle.read("BUNDLE-MANIFEST.json"))

            self.assertEqual(report["schema_version"], BUNDLE_SCHEMA_VERSION)
            self.assertEqual(report["distribution_mode"], "skill-plus-hosted-mcp")
            self.assertTrue(report["hosted_mcp_config_bundled"])
            self.assertFalse(report["live_mcp_bundled"])
            self.assertIn(".codex-plugin/plugin.json", names)
            self.assertIn(".mcp.json", names)
            self.assertIn(".agents/plugins/marketplace.json", names)
            self.assertIn("assets/plugin-icon.svg", names)
            self.assertIn("README.md", names)
            self.assertIn("README.zh-CN.md", names)
            self.assertIn("CHANGELOG.md", names)
            self.assertIn("LICENSE", names)
            self.assertIn("TERMS.md", names)
            self.assertIn("ROADMAP.md", names)
            self.assertIn("SECURITY.md", names)
            self.assertIn("PRIVACY.md", names)
            self.assertIn("SUPPORT.md", names)
            self.assertIn("docs/QUICKSTART.md", names)
            self.assertIn("docs/FAQ.md", names)
            self.assertIn("skills/ai-open-source-intelligence/SKILL.md", names)
            self.assertIn("docs/alpha-tester-guide.md", names)
            self.assertIn("schemas/tool-result.schema.json", names)
            self.assertIn("schemas/error.schema.json", names)
            self.assertFalse(any(name.startswith("product-skills/") for name in names))
            self.assertNotIn("src/aiworkstation_osi/mcp_server.py", names)
            self.assertNotIn("pyproject.toml", names)
            self.assertEqual(manifest["distribution_mode"], "skill-plus-hosted-mcp")
            self.assertTrue(manifest["hosted_mcp_config_bundled"])
            self.assertFalse(manifest["live_mcp_bundled"])

    def test_embedded_manifest_matches_every_packaged_file(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            report = build_alpha_bundle(self.ROOT, Path(temp_dir))
            archive = Path(report["archive"])
            with zipfile.ZipFile(archive) as bundle:
                manifest = json.loads(bundle.read("BUNDLE-MANIFEST.json"))
                declared = manifest["files"]
                declared_paths = {row["path"] for row in declared}
                actual_paths = set(bundle.namelist()) - {"BUNDLE-MANIFEST.json"}
                self.assertEqual(declared_paths, actual_paths)
                for row in declared:
                    with self.subTest(path=row["path"]):
                        data = bundle.read(row["path"])
                        self.assertEqual(row["size"], len(data))
                        self.assertEqual(row["sha256"], hashlib.sha256(data).hexdigest())

    def test_bundle_is_reproducible(self) -> None:
        with tempfile.TemporaryDirectory() as first_dir, tempfile.TemporaryDirectory() as second_dir:
            first = build_alpha_bundle(self.ROOT, Path(first_dir))
            second = build_alpha_bundle(self.ROOT, Path(second_dir))
            first_bytes = Path(first["archive"]).read_bytes()
            second_bytes = Path(second["archive"]).read_bytes()

            self.assertEqual(first_bytes, second_bytes)
            self.assertEqual(first["archive_sha256"], second["archive_sha256"])
            self.assertEqual(
                first["archive_sha256"],
                hashlib.sha256(first_bytes).hexdigest(),
            )

    def test_checksum_matches_archive(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            report = build_alpha_bundle(self.ROOT, Path(temp_dir))
            archive = Path(report["archive"])
            checksum = Path(report["checksum_file"]).read_text(encoding="utf-8").strip()
            digest, filename = checksum.split("  ", 1)

            self.assertEqual(filename, archive.name)
            self.assertEqual(digest, hashlib.sha256(archive.read_bytes()).hexdigest())


if __name__ == "__main__":
    unittest.main()
