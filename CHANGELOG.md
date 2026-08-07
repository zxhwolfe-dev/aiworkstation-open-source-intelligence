# Changelog

All notable pre-release changes are recorded here. Dates refer to repository
changes, not public availability.

## [Unreleased]

### Added

- Guarded stateless JSON Streamable HTTP MCP server with loopback-safe defaults,
  explicit non-loopback acknowledgement, MCP Host/origin allowlists, request
  body caps and allow-listed live Radar origins.
- Non-root Docker image, minimal build context and localhost-only hardened
  Compose example for private hosted-alpha deployment.
- `osi-remote-smoke` for real remote MCP tool discovery, read-only annotation
  validation and optional bilingual structured search calls.
- A real CI Streamable-HTTP round trip that starts the local server, connects
  with an MCP client, discovers the six tools and invokes one read-only search.
- Privacy-minimized structured tool telemetry written to stderr. It records tool
  name, outcome, duration, public error code and safe aggregate counts; query
  text, constraints, project IDs and raw request IDs are not accepted by the
  telemetry event API.
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

- Verified project facts now distinguish validated repository/public metadata
  from analysis/editorial projection fields. Summary, deployment classification,
  categories and use cases remain visible in `data.project` but are not promoted
  to `verified_facts` merely because they appear in the public detail JSON.
- Verified licenses now require a direct public `License` transparency source
  with a public excerpt. A license label without direct evidence is downgraded to
  an explicit unknown and `LICENSE_UNVERIFIED` risk.
- `get_project_facts` exposes `field_evidence_status` so clients can distinguish
  `verified_public_metadata`, `verified_direct_evidence`,
  `public_projection_only` and `unknown` values.
- Live probes require an observed license to report `evidence_status=verified`
  and a positive direct evidence count; otherwise the license must remain an
  explicit unknown.
- CI validates the guarded HTTP configuration, builds the container on Python
  3.12, verifies the Compose configuration, runs Python compile checks and
  smoke-tests the expanded CLI surface.
- Live contract replay derives locale and project identity from the captured
  manifest instead of accepting duplicate identity flags.
- Skills-only alpha bundles include `SECURITY.md`, `PRIVACY.md` and `SUPPORT.md`
  while continuing to exclude runtime source and MCP code.
- Release-readiness gates require explicit protected-gateway/private-network and
  remote-MCP evidence before declaring hosted private-alpha readiness.
- README, schemas and M1 documentation describe the actual fact/evidence,
  Skills-only, stdio and guarded hosted distribution boundaries.

### Security

- Public Radar HTTP redirects are rejected before they can leave the configured
  upstream origin; a 3xx is treated as a contract change, not followed silently.
- Non-loopback Streamable HTTP binds are rejected unless the operator opts into
  the live provider, supplies explicit MCP Host allowlists and acknowledges a
  reverse-proxy/private-network deployment.
- The MCP SDK receives explicit Host/origin transport-security settings for
  non-loopback binds to reduce DNS-rebinding and Host-header risk.
- The bind acknowledgement is never treated as authentication; a fake
  "assume authentication" switch is rejected.
- Remote smoke URLs must use HTTPS outside localhost, use the canonical `/mcp`
  path and may not embed credentials, query strings or fragments.
- The example container runs as a non-root user with a read-only filesystem,
  dropped capabilities, `no-new-privileges`, bounded resources and host-loopback
  port exposure.
- Telemetry defaults to warnings/errors and never logs user query or structured
  request bodies.

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
