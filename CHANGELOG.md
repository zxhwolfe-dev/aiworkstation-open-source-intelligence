# Changelog

All notable pre-release changes are recorded here. Dates refer to repository
changes, not public availability.

## [Unreleased]

### Added

- Guarded stateless JSON Streamable HTTP MCP server with loopback-safe defaults,
  explicit non-loopback acknowledgement and allow-listed live Radar origins.
- Non-root Docker image, minimal build context and localhost-only hardened
  Compose example for private hosted-alpha deployment.
- `osi-remote-smoke` for real remote MCP tool discovery, read-only annotation
  validation and optional bilingual structured search calls.
- Four-level `osi-readiness` v2 report distinguishing code, Skills-only external
  alpha, hosted private alpha and broad public-launch readiness.
- Hosted MCP deployment runbook, public-launch decision register and alpha
  support policy.
- Manual bilingual live-contract validation workflow with allow-listed origins,
  sanitized captures, offline validation, hardened-provider replay and safe
  artifact upload.
- Deterministic Skills-only alpha ZIP builder with embedded file manifest,
  external SHA-256 checksum and credential-like-content checks.
- Manual alpha packaging workflow that runs release gates and inspects the
  archive before upload.
- External alpha tester guide, structured feedback templates and release
  checklist.

### Changed

- CI now validates the guarded HTTP configuration, builds the container on
  Python 3.12, verifies the Compose configuration, and smoke-tests the expanded
  CLI surface.
- Live contract replay derives locale and project identity from the captured
  manifest instead of accepting duplicate identity flags.
- Skills-only alpha bundles now include `SECURITY.md`, `PRIVACY.md` and
  `SUPPORT.md` while continuing to exclude runtime source and MCP code.
- Release-readiness gates now require explicit protected-gateway/private-network
  and remote-MCP evidence before declaring hosted private-alpha readiness.
- README and M1 documentation now describe the actual Skills-only, stdio and
  guarded hosted distribution boundaries.

### Security

- Non-loopback Streamable HTTP binds are rejected unless the operator opts into
  the live provider and explicitly acknowledges a reverse-proxy/private-network
  deployment.
- The bind acknowledgement is never treated as authentication; a fake
  "assume authentication" switch is rejected.
- Remote smoke URLs must use HTTPS outside localhost and may not embed
  credentials, query strings or fragments.
- The example container runs as a non-root user with a read-only filesystem,
  dropped capabilities, `no-new-privileges`, bounded resources and host-loopback
  port exposure.

## [0.1.0] - 2026-08-06

**Pre-release status:** M1 Alpha. This version number identifies the current
plugin contract and package contents; it does not imply a broad public launch.

### Added

- Three Skills:
  - `open-source-project-research`
  - `open-source-project-comparison`
  - `open-source-stack-planner`
- Six read-only tool contracts:
  - `search_ai_projects`
  - `get_project_facts`
  - `get_license_evidence`
  - `compare_ai_projects`
  - `find_alternatives`
  - `compose_ai_stack`
- Versioned result envelope separating verified facts, recommendations,
  unknowns and risks.
- Deterministic offline mock provider.
- Hardened public AI Workstation Radar HTTP provider with snapshot, selector,
  near-match and license boundaries.
- MCP Python SDK v2 stdio server with six read-only annotated tools.
- Bilingual core and plugin-workflow evaluation corpora.
- Public contract probe, sanitized fixture capture, fixture validation and
  offline replay.
- Skills-only Codex plugin manifest and repository marketplace.
- Security, privacy, architecture, Codex setup and production-validation
  documentation.
- Automated tests and GitHub Actions CI for Python 3.10 and 3.12.

### Security

- No repository code execution or installation is performed by project tools.
- Public repository and web content is treated as untrusted data.
- Missing licenses are explicit unknowns and not permission.
- Provider failures and malformed contracts fail closed.
- Default execution remains offline until the HTTP provider is explicitly
  enabled.

### Known limitations

- No native per-user hosted MCP authorization, quotas, billing or abuse-control
  system.
- Skills-only plugin installations do not receive live project tools by
  themselves.
- Public production contract validation and manual artifact review remain
  release gates.
- No broad public plugin-directory release has occurred.
- No open-source software license has been selected.
