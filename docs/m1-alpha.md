# M1 Alpha

M1 connects the M0 contracts to AI Workstation's public Open Source Radar,
exposes them through a local MCP stdio server, and packages the three workflows
as a Skills-only plugin. It remains read-only and is not a public hosted service.

## Delivered

### Skills-only plugin package

The repository root contains:

- `.codex-plugin/plugin.json` with stable identity, install-surface metadata and
  the `./skills/` package path;
- `.agents/plugins/marketplace.json` for repo-scoped local installation;
- three complete Skill workflows;
- package validation, bilingual workflow evaluations and safe no-tool fallback
  behavior.

The plugin does not declare `mcpServers` or `apps`. The current stdio server
requires a separately installed Python environment, and no final registered
hosted MCP technical ID exists. Adding either manifest field before its target
is portable and tested would create a broken package.

### Deterministic alpha package

`osi-build-alpha` builds a reproducible Skills-only ZIP containing only reviewed
plugin manifests, Skills and public documentation.

The package:

- excludes Python source, tests, CI and the MCP server;
- rejects symlinks, oversized files, non-UTF-8 files and credential-like text;
- embeds per-file SHA-256 values;
- emits an external `SHA256SUMS` file;
- declares `distribution_mode=skills-only` and `live_mcp_bundled=false`.

The manual `alpha-package` workflow runs tests, plugin validation, checksum and
archive-surface checks before uploading an artifact.

### Public HTTP provider

`AIWorkstationHttpProvider` uses only these public read surfaces:

- project list and keyword search;
- public project detail;
- public selector.

The provider does not import `akaiagents`, read its filesystem, access its
maintenance routes or execute repository code.

### Fail-closed rules

- A project list must contain public `snapshot_id` before a detail can become a
  verified fact.
- Listing and detail snapshots must match when both are present.
- Comparisons and hydrated candidate sets must use one snapshot.
- Selector evidence must be `available`, or `partial` with a public notice.
- Near matches must have exactly one blocker and cannot coexist with formal
  recommendations.
- Internal publication fields in selector responses fail closed.
- Unknown license sentinels such as `NOASSERTION`, `UNKNOWN` and `UNLICENSED`
  never become verified licenses.
- Non-standard labels such as `OTHER` are observations, but carry high-risk
  manual-review warnings.
- HTTP 408, 425, 429 and 5xx responses are retryable provider failures.
- Invalid JSON, oversized responses and malformed public contracts fail closed.

### Bounded tool inputs

Top-level schemas reject undeclared fields. Nested `constraints` and `context`
objects accept JSON-compatible values only and enforce:

- depth at most 6;
- at most 200 total nodes;
- at most 50 entries/items per container;
- keys at most 128 characters without control characters;
- nested strings at most 1,000 characters;
- finite numbers only.

The limits are published in `schemas/tool-manifest.json` and covered by runtime
and schema-alignment tests.

### MCP stdio server

`osi-mcp` exposes exactly six synchronous read-only tools:

- `search_ai_projects`
- `get_project_facts`
- `get_license_evidence`
- `compare_ai_projects`
- `find_alternatives`
- `compose_ai_stack`

All six tools are annotated as read-only, non-destructive, idempotent and
open-world. Tools return structured `osi.tool-result.v1` data. Stable product
errors become model-readable tool failures without exposing private exception
details.

### Public contract validation

`osi-probe` performs anonymous read-only checks for project facts, license state
and constrained search.

`osi-capture-contracts` records bounded, sanitized project-list, project-detail,
formal-selector and no-match-selector response shapes.

`osi-validate-contracts` verifies the captured contracts offline.

`osi-replay-contracts` passes the captures through the same hardened provider
used by MCP and CLI entrypoints.

The manual `live-contract-validation` workflow:

- accepts only allow-listed HTTPS AI Workstation origins;
- validates the project identity input;
- runs English and Chinese probes;
- captures, validates and replays both languages;
- scans forbidden JSON keys;
- uploads artifacts only after every gate succeeds.

### Consolidated readiness report

`osi-readiness` distinguishes:

- `code_ready`;
- `external_alpha_ready`;
- `public_launch_ready`.

Ordinary CI verifies code readiness without claiming live validation, Codex
integration or human review. External-alpha readiness requires both validated
contract directories plus explicit CI, Codex, workflow-run and reviewer
evidence. Public-launch readiness remains false until licensing, legal/support
pages and hosted-service protections are complete.

## Local commands

```bash
python -m pip install -e ".[mcp]"
python -m unittest discover -s tests -v
osi-validate-plugin --root .
osi-readiness --root .

# Offline MCP server
OSI_PROVIDER=mock osi-mcp

# Live read-only MCP server
OSI_PROVIDER=http \
AIWORKSTATION_RADAR_BASE_URL=https://aiworkstation.cn \
osi-mcp

# Contract probes
osi-probe --base-url https://aiworkstation.cn --locale en
osi-probe --base-url https://aiworkstation.cn --locale zh

# Skills-only archive
osi-build-alpha --root . --output-dir dist/alpha
```

## Alpha acceptance gates

### Code-side gates

- [x] Three Skills are packaged under a validated plugin manifest.
- [x] A repo-scoped local marketplace entry exists.
- [x] The manifest does not claim an ungranted license or unready MCP mapping.
- [x] Live provider requires explicit opt-in.
- [x] Default execution remains offline and deterministic.
- [x] Project facts require snapshot identity.
- [x] Mixed-snapshot comparisons fail closed.
- [x] License sentinels cannot become verified facts.
- [x] Near-match and internal-field boundaries are enforced.
- [x] Nested structured inputs are bounded and JSON-compatible.
- [x] MCP server has list/call/error/annotation tests.
- [x] Probe, capture, validation and replay have deterministic tests.
- [x] Deterministic alpha packaging and checksum behavior have tests.
- [x] Manual live-validation and packaging workflows have policy tests.
- [x] A consolidated release-readiness command exists.
- [x] Structured alpha bug and contract-change issue forms exist.
- [x] Dependency monitoring and security-sensitive code ownership are defined.

### Operational gates not yet observed

- [ ] Full local test suite succeeds after pulling current `main`.
- [ ] Standard GitHub Actions succeeds on Python 3.10.
- [ ] Standard GitHub Actions succeeds on Python 3.12.
- [ ] The Skills plugin is installed through the repo marketplace.
- [ ] English production probe succeeds.
- [ ] Chinese production probe succeeds.
- [ ] Production captures validate, replay and pass manual review.
- [ ] The stdio MCP server is called successfully from Codex.
- [ ] `osi-readiness --require-external-alpha` succeeds with real evidence.

## Not yet included

- plugin-bundled MCP configuration;
- registered hosted MCP mapping;
- hosted Streamable HTTP MCP;
- OAuth, API keys, quotas or billing;
- public plugin-directory submission;
- final software license, privacy policy, terms, support URL, icons or
  screenshots;
- saved projects, alerts, team workspaces or other writes;
- server-side LLM generation inside this distribution repository;
- guarantees that proposed projects are mutually compatible.

## Next milestone: operational M1 validation

The code-side M1 Alpha scope is complete. The next work depends on observed
runtime evidence:

1. pull current `main` and run all tests locally;
2. observe standard CI on Python 3.10 and 3.12;
3. run the manual live validation workflow;
4. review the bilingual sanitized artifact;
5. install the Skills-only package through the marketplace;
6. call the six-tool stdio MCP server from Codex;
7. generate the external-alpha readiness report with real evidence;
8. fix only contract differences demonstrated by those runs.

Hosted MCP and broad public submission remain a separate milestone and must not
start by weakening the current read-only, evidence and unknown-state boundaries.
