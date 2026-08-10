# Plugin packaging and distribution

Version 0.3 ships a Skills-only Plugin package containing exactly one active
Skill: `product-skills/ai-open-source-intelligence/SKILL.md`. The live nine-tool
MCP runtime is installed and deployed separately.

Package identity is read from `.codex-plugin/plugin.json`; its version must equal
the Python runtime, wheel metadata and Changelog. The repository marketplace
entry is local, available, and declares no installation authentication.

Validate and build:

```bash
python -m pip install -e ".[mcp]"
osi-validate-plugin --root .
osi-build-alpha --root . --output-dir dist/alpha
(cd dist/alpha && sha256sum --check SHA256SUMS)
```

The deterministic ZIP contains the Plugin and marketplace manifests, unified
Skill, bilingual README/quickstart, Changelog, License, Terms, Security, Privacy,
Support, Roadmap, FAQ and reviewed tester guidance. It excludes Python source,
tests, workflows, environment files, credentials and all removed legacy Skills.

GitHub Release, PyPI and GHCR must promote artifacts built from one exact tag and
SHA. PyPI uses Trusted Publishing; GHCR bakes the commit into
`OSI_IMAGE_COMMIT`. A published package is not evidence that the Hosted endpoint
has passed staging or public-launch gates.
