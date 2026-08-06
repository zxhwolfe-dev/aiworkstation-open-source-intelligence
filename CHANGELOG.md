# Changelog

All notable pre-release changes are recorded here. Dates refer to repository
changes, not public availability.

## [Unreleased]

### Added

- Manual bilingual live-contract validation workflow with allow-listed origins,
  sanitized captures, offline validation, provider replay and safe artifact
  upload.
- Deterministic Skills-only alpha ZIP builder with embedded file manifest,
  external SHA-256 checksum and credential-like-content checks.
- Manual alpha packaging workflow that runs release gates and inspects the
  archive before upload.
- External alpha tester guide and release checklist.

### Changed

- CI now builds and verifies the Skills-only alpha package on Python 3.10 and
  3.12.
- README and plugin packaging documentation describe the actual distribution,
  validation and live-data boundaries.

## [0.1.0-alpha.1] - 2026-08-06

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

- No hosted public MCP service.
- No authentication, quotas, billing, saved collections or team features.
- Skills-only plugin installations do not receive live project tools by
  themselves.
- Public production contract validation and manual artifact review remain
  release gates.
- No open-source software license has been selected.
