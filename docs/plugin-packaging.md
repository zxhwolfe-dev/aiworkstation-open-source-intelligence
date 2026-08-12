# Plugin packaging and distribution

The current repository package contains exactly one active Skill,
`skills/ai-open-source-intelligence/SKILL.md`, plus `.mcp.json`, which
connects the installed Plugin to the production nine-tool Hosted MCP. The
remote MCP runtime remains independently deployed and is not embedded in the
archive.

The published `v0.3.0` archive is an immutable historical Skills-only artifact.
This complete package uses the `v0.3.1` patch identity rather than rebuilding
or replacing `v0.3.0`.

Package identity is read from `.codex-plugin/plugin.json`; its version must equal
the Python runtime, wheel metadata and Changelog. The repository marketplace
entry is local, available, and uses the supported `ON_INSTALL` installation
lifecycle policy. This marketplace policy is not an MCP authentication mode:
the production Hosted MCP remains anonymous and the platform submission uses
**No Authentication**.

Validate and build:

```bash
python -m pip install -e ".[mcp]"
osi-validate-plugin --root .
osi-build-alpha --root . --output-dir dist/alpha
(cd dist/alpha && sha256sum --check SHA256SUMS)
```

The deterministic ZIP contains the Plugin, Hosted MCP and marketplace
manifests, unified Skill, bilingual README/quickstart, Changelog, License,
Terms, Security, Privacy, Support, Roadmap, FAQ and reviewed tester guidance.
It excludes the remote MCP runtime, Python source, tests, workflows,
environment files, credentials and all removed legacy Skills.

The bundle declares:

```text
distribution_mode=skill-plus-hosted-mcp
hosted_mcp_config_bundled=true
live_mcp_bundled=false
```

For Codex and the ChatGPT desktop Codex host, the repository Marketplace can
therefore install the Skill and Hosted MCP configuration together. ChatGPT web
Developer-mode testing still requires registering the MCP connection first;
the public directory submission must use **With MCP / Universal / No
Authentication** so the reviewed public install includes both components.

GitHub Release, PyPI and GHCR must promote artifacts built from one exact tag and
SHA. PyPI uses Trusted Publishing; GHCR bakes the commit into
`OSI_IMAGE_COMMIT`. A published package is not evidence that the Hosted endpoint
has passed staging or public-launch gates.
