from __future__ import annotations

import unittest
from pathlib import Path


class ContainerPackagingTests(unittest.TestCase):
    ROOT = Path(__file__).resolve().parents[1]

    @classmethod
    def setUpClass(cls) -> None:
        cls.dockerfile = (cls.ROOT / "Dockerfile").read_text(encoding="utf-8")
        cls.compose = (cls.ROOT / "compose.hosted.example.yml").read_text(encoding="utf-8")
        cls.dockerignore = (cls.ROOT / ".dockerignore").read_text(encoding="utf-8")

    def test_image_runs_as_non_root_user(self) -> None:
        self.assertIn("useradd --system", self.dockerfile)
        self.assertIn("USER osi", self.dockerfile)
        self.assertNotIn("USER root", self.dockerfile)

    def test_image_uses_guarded_http_entrypoint(self) -> None:
        self.assertIn('CMD ["osi-mcp-http"]', self.dockerfile)
        self.assertIn("HEALTHCHECK", self.dockerfile)
        self.assertNotIn("OSI_MCP_HTTP_PUBLIC_BIND_ACK", self.dockerfile)

    def test_compose_example_is_host_loopback_only_and_allowlisted(self) -> None:
        self.assertIn('"127.0.0.1:8000:8000"', self.compose)
        self.assertNotIn('"0.0.0.0:8000:8000"', self.compose)
        self.assertIn("OSI_PROVIDER: http", self.compose)
        self.assertIn(
            "OSI_MCP_HTTP_PUBLIC_BIND_ACK: reverse-proxy-or-private-network",
            self.compose,
        )
        self.assertIn(
            "OSI_MCP_HTTP_ALLOWED_HOSTS: 127.0.0.1:8000,localhost:8000",
            self.compose,
        )
        self.assertIn('OSI_MCP_HTTP_ALLOWED_ORIGINS: ""', self.compose)
        self.assertIn('OSI_MCP_HTTP_MAX_REQUEST_BODY_BYTES: "262144"', self.compose)

    def test_compose_drops_linux_privileges(self) -> None:
        self.assertIn("read_only: true", self.compose)
        self.assertIn("no-new-privileges:true", self.compose)
        self.assertIn("cap_drop:", self.compose)
        self.assertIn("- ALL", self.compose)

    def test_build_context_excludes_local_secrets_and_large_non_runtime_surfaces(self) -> None:
        for marker in (".env", "tests", "docs", "skills", "tmp", ".git"):
            with self.subTest(marker=marker):
                self.assertIn(marker, self.dockerignore)


if __name__ == "__main__":
    unittest.main()
