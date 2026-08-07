# Changelog

All notable pre-release changes are recorded here. Dates refer to repository changes, not public availability.

## [Unreleased]

### Added

- Apache-2.0 public repository license and public `TERMS.md`.
- Product-first English README plus complete Simplified Chinese README.
- Public Quickstart, FAQ, model/data-flow explanation, Roadmap, contribution guide and Code of Conduct.
- Structured GitHub issue templates for bugs, evidence problems, public-contract regressions, project coverage and feature requests.
- OpenAI Skills-only plugin submission pack with listing copy, starter prompts, five positive test cases and three negative/boundary cases.
- Guarded GitHub release workflow for deterministic Skills bundle releases.
- PyPI Trusted Publishing workflow preparation and expanded package metadata.
- GHCR versioned container publishing workflow.
- Guarded stateless JSON Streamable HTTP MCP server with loopback-safe defaults, explicit non-loopback acknowledgement, MCP Host/origin allowlists, request body caps and allow-listed live Radar origins.
- Non-root Docker image, minimal build context and localhost-only hardened Compose example for private hosted-alpha deployment.
- `osi-remote-smoke` for real remote MCP tool discovery, read-only annotation validation and optional bilingual structured search calls.
- Privacy-minimized structured tool telemetry written to stderr.
- Four-level `osi-readiness` report distinguishing code, Skills-only external alpha, hosted private alpha and broad public-launch readiness.
- Bilingual live-contract validation, deterministic Skills-only packaging, evidence manifests and real Codex six-tool acceptance.

### Changed

- Public plugin metadata now includes Apache-2.0, public privacy/terms/support URLs and five starter prompts.
- `osi-validate-plugin` can treat the Skills metadata package as public-submission metadata ready while still warning that MCP is a separate workflow.
- Skills-only distribution bundles now include license, terms, bilingual onboarding, FAQ and roadmap documents.
- `osi-readiness` no longer reports the resolved software-license decision as a public-launch blocker; hosted service identity/authentication, quotas, abuse controls, service-specific legal/retention policy and platform review remain separate blockers.
- Verified project facts distinguish validated repository/public metadata from analysis/editorial projection fields.
- Verified licenses require direct public `License` transparency evidence; missing/indirect evidence remains unknown.
- Live contract captures remove query/prompt text and selector query-analysis structures before artifacts are retained.
- CI validates Python 3.10/3.12, MCP contracts, package surfaces and guarded HTTP/container configuration.

### Security

- Public Radar redirects fail closed rather than following another origin.
- Non-loopback Streamable HTTP binds require explicit deployment acknowledgement and Host/origin restrictions.
- Telemetry does not accept query text, constraints, project IDs or raw request bodies.
- Skills-only release bundles exclude runtime source and scan public files for common credential-like material.
- Public issue intake explicitly redirects security-sensitive reports away from public issues.

## [0.1.0] - 2026-08-06

**Pre-release status:** M1 Alpha. This version number identifies the current plugin contract and package contents; it does not imply a broad public hosted MCP launch.

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
- Versioned result envelope separating verified facts, recommendations, unknowns and risks.
- Deterministic offline mock provider.
- Hardened public AI Workstation Radar HTTP provider with snapshot, selector, near-match and license boundaries.
- MCP Python SDK v2 stdio server with six read-only annotated tools.
- Bilingual core and plugin-workflow evaluation corpora.
- Public contract probe, sanitized fixture capture, fixture validation and offline replay.
- Skills-only Codex plugin manifest and repository marketplace.
- Security, privacy, architecture, Codex setup and production-validation documentation.
- Automated tests and GitHub Actions CI for Python 3.10 and 3.12.

### Known limitations

- The first directory/package release is Skills-only unless a live MCP connection is separately configured.
- Broad public hosted MCP still requires final identity/authentication, revocation, quotas, rate limiting, abuse controls, monitoring and service-specific operational/legal policy.
- Cross-project compatibility remains unverified until separately tested.
- License evidence is technical evidence, not legal advice.
