# Changelog

All notable pre-release changes are recorded here. Dates refer to repository changes, not public availability.

## [0.3.0] - 2026-08-10

### Changed

- Rebuilt the public contract around one version source, nine tools and `osi.tool-result.v2` / `osi.error.v2` envelopes.
- Replaced untyped constraint maps with typed `{id, value, polarity}` arrays and removed the inactive `source_mode` parameter.
- Documented ephemeral selector control-plane effects while retaining the non-destructive, business-data read-only boundary.

## [0.2.0] - 2026-08-09

### Changed

- Replaced three overlapping user-facing Skills with one unified `ai-open-source-intelligence` Skill that internally routes browsing, research, fact checking, comparison, alternatives and stack planning.
- Moved the active Skill root to `product-skills/` and removed the old split Skill paths from the product and distribution bundle.
- Made the Hosted product strictly data/evidence-only: exactly nine read-only Radar tools, no runtime OAuth mode, no Premium tool, no checkout/credit path and no AI Workstation server-side model execution.
- Locked requirement-based Radar selection to the deterministic public selector contract with `use_model=false` and added regression coverage for that invariant.
- Added canonical AI Workstation, AI Open Source Radar and open-source-project links to every MCP tool result under `data.official_resources`; the unified Skill may surface those links once as publisher resources without mixing them into verified facts.
- Tightened anonymous Hosted abuse controls with short-window plus sustained per-IP request limits and a lower concurrent-connection cap.
- Updated Plugin metadata, package metadata, CI, manifests, readiness logic, container configuration and documentation to match the one-Skill/data-only product.

### Security

- `OSI_HOSTED_ACCESS_MODE=oauth` now fails closed instead of re-enabling a hidden OAuth/Premium/server-model route.
- Public Hosted Compose no longer carries OAuth, backend-service-token or Premium environment variables.
- Dedicated MCP Nginx configuration no longer forwards Authorization or exposes OAuth metadata routes in the data-only release.

## [0.1.0] - 2026-08-09

### Added

- Initial Apache-2.0 public repository and evidence-backed open-source AI research workflows.
- Nine standard read-only Radar MCP tools covering project discovery, facts, license evidence, comparison, alternatives, stack planning, Radar overview, project browsing and Radar Skills browsing.
- Hardened public Radar HTTP provider, bilingual live-contract validation, deterministic Skills packaging, Codex acceptance and evidence-first release readiness.
- Candidate-bound Hosted MCP deployment identity, Docker packaging, TLS/Nginx gateway templates, remote MCP validation and Hosted Private Alpha readiness.
- Initial public Hosted deployment architecture and production abuse controls.

### Changed

- Public project facts distinguish verified public metadata/direct evidence from editorial projections and unknowns.
- Verified license output requires direct public License evidence rather than relying on a label alone.
- Hard requirements remain explicit and are never silently relaxed to manufacture a match.
