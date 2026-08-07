# M1 Alpha

M1 connects the M0 contracts to AI Workstation's public Open Source Radar,
exposes them through local stdio and guarded Streamable HTTP MCP transports, and
packages the three workflows as a Skills-only plugin. All six product tools
remain read-only. Broad public hosting is not yet approved.

## Delivered

### Skills-only plugin package

The repository root contains:

- `.codex-plugin/plugin.json` with stable identity, install-surface metadata and
  the `./skills/` package path;
- `.agents/plugins/marketplace.json` for repo-scoped local installation;
- three complete Skill workflows;
- package validation, bilingual workflow evaluations and safe no-tool fallback
  behavior.

The plugin still does not declare `mcpServers` or `apps`. The local stdio server
requires a separately installed Python environment, while the hosted endpoint
has no final registered platform connection ID or native public authorization.
Adding a plugin connection mapping before those pieces are stable would create a
misleading or broken package.

### Deterministic Skills-only alpha package

`osi-build-alpha` creates a reproducible ZIP containing the plugin manifests,
three Skills, changelog, security/privacy/support documents and tester guidance.
It excludes Python runtime code, tests, CI and MCP server implementation.

The builder rejects symlinks, oversized/non-UTF-8 files and common
credential-like text, embeds per-file SHA-256 values and emits an external
`SHA256SUMS` file. The archive explicitly declares
`distribution_mode=skills-only` and `live_mcp_bundled=false`.

### Public Radar provider

`AIWorkstationHttpProvider` reads only the public project list/search, public
project detail and public selector surfaces. It never imports private
`akaiagents` modules, accesses maintenance routes or executes repository code.

Fail-closed rules cover snapshot identity, mixed snapshots, selector evidence,
near-match separation, internal publication fields, unknown/non-standard
licenses, retryable upstream failures, invalid JSON, oversized responses and
malformed contracts.

### Bounded tool inputs

Top-level schemas reject undeclared fields. Nested `constraints` and `context`
values are JSON-compatible and bounded by depth, node count, container size, key
length, string length and finite-number rules. Runtime validation and the
machine-readable tool manifest are tested for alignment.

### MCP stdio server

`osi-mcp` exposes exactly six tools:

- `search_ai_projects`
- `get_project_facts`
- `get_license_evidence`
- `compare_ai_projects`
- `find_alternatives`
- `compose_ai_stack`

All six are annotated read-only, non-destructive, idempotent and open-world.
Results use `osi.tool-result.v1`; stable public errors are surfaced without
leaking private exception details.

### Guarded Streamable HTTP server

`osi-mcp-http` exposes the same six tools over stateless JSON Streamable HTTP.
Safe defaults bind to `127.0.0.1:8000` and use the offline mock provider.

A non-loopback bind is refused unless the operator explicitly acknowledges a
private-network/reverse-proxy deployment, enables the live HTTP provider and
uses an allow-listed HTTPS Radar origin. The acknowledgement is not treated as
authentication; a fake "assume auth" switch is explicitly rejected.

The repository includes:

- `Dockerfile` running as a non-root user;
- `.dockerignore` that excludes local secrets and non-runtime surfaces;
- `compose.hosted.example.yml` mapping the container to host loopback only and
  dropping Linux capabilities;
- `osi-remote-smoke` for real Streamable HTTP tool discovery, annotation checks
  and optional read-only search calls;
- unit tests that verify transport arguments without opening a real socket;
- container-policy tests and CI container build/config validation.

This is a **private hosted-alpha scaffold**, not an unauthenticated public
Internet service. See `docs/hosted-mcp.md`.

### Public contract validation

`osi-probe`, `osi-capture-contracts`, `osi-validate-contracts` and
`osi-replay-contracts` form the public-contract validation chain. Replay derives
locale and project identity from each sanitized capture manifest so it tests the
exact captured contract.

The manual `live-contract-validation` workflow restricts target origins,
validates project identity, probes and captures English/Chinese contracts,
validates and replays them, scans forbidden JSON keys and uploads artifacts only
after all gates succeed.

### Consolidated readiness report

`osi-readiness` v2 distinguishes four levels:

- `code_ready`;
- `external_alpha_ready` for the Skills-only invited alpha;
- `hosted_private_alpha_ready` for a protected deployed MCP endpoint;
- `public_launch_ready`.

Ordinary CI can establish only code readiness. Skills-only alpha requires real
production captures, CI/Codex evidence and human review. Hosted private alpha
also requires a credential-free HTTPS MCP URL, successful remote MCP smoke test
and protected gateway/private-network attestation. Public-launch readiness stays
false until licensing, final legal pages, native per-user authorization,
revocation, quotas/rate limits/abuse controls and platform review are complete.

## Local commands

```bash
python -m pip install -e ".[mcp]"
python -m unittest discover -s tests -v
osi-validate-plugin --root .
osi-readiness --root .

# Offline stdio MCP
OSI_PROVIDER=mock osi-mcp

# Live read-only stdio MCP
OSI_PROVIDER=http \
AIWORKSTATION_RADAR_BASE_URL=https://aiworkstation.cn \
osi-mcp

# Safe local Streamable HTTP config/server
osi-mcp-http --check-config
OSI_PROVIDER=mock osi-mcp-http

# Remote MCP compatibility smoke
osi-remote-smoke --url http://127.0.0.1:8000/mcp

# Production contract probes
osi-probe --base-url https://aiworkstation.cn --locale en
osi-probe --base-url https://aiworkstation.cn --locale zh

# Skills-only archive
osi-build-alpha --root . --output-dir dist/alpha
```

## Alpha acceptance gates

### Code-side gates delivered

- [x] Three Skills and validated Skills-only plugin package.
- [x] Repo-scoped local marketplace.
- [x] Six bounded read-only tool contracts and unified result envelope.
- [x] Offline mock and fail-closed live Radar provider.
- [x] Snapshot, selector, near-match, internal-field and license boundaries.
- [x] stdio MCP server and read-only tool annotations.
- [x] Guarded Streamable HTTP server with loopback-safe defaults.
- [x] Non-root container and localhost-only compose example.
- [x] Remote MCP compatibility smoke command.
- [x] Bilingual probes, sanitized capture, validation and provider replay.
- [x] Deterministic Skills-only archive and checksum verification.
- [x] Manual live-validation and packaging workflows.
- [x] Four-level release-readiness report.
- [x] Security/privacy/support policy, issue intake, dependency monitoring and
  security-sensitive code ownership.

### Operational gates not yet observed

- [ ] Full local test suite succeeds after pulling current `main`.
- [ ] Standard GitHub Actions succeeds on Python 3.10.
- [ ] Standard GitHub Actions succeeds on Python 3.12, including container build.
- [ ] Skills plugin is installed through the repo marketplace.
- [ ] English production probe succeeds.
- [ ] Chinese production probe succeeds.
- [ ] Production captures validate, replay and pass manual review.
- [ ] stdio MCP is called successfully from Codex.
- [ ] `osi-readiness --require-external-alpha` succeeds with real evidence.
- [ ] Guarded Streamable HTTP is deployed behind a trusted protected gateway or
  private network.
- [ ] `osi-remote-smoke` succeeds against that deployed endpoint in English and
  Chinese.
- [ ] `osi-readiness --require-hosted-alpha` succeeds with real evidence.

## Not yet included

- native per-user MCP OAuth/authorization and token revocation;
- production quotas, rate limiting, abuse blocking and billing;
- final hosted MCP hostname/platform registration mapping in the plugin;
- broad public plugin-directory submission;
- final software license and public legal URLs;
- production observability/retention infrastructure;
- saved projects, alerts, team workspaces or other writes;
- server-side LLM generation inside this distribution repository;
- guarantees that proposed projects are mutually compatible.

## Next milestone

The remaining work is mostly observed runtime/infrastructure evidence rather
than more core feature code:

1. run local and GitHub CI gates;
2. run bilingual production contract validation and review artifacts;
3. install/test the Skills package and stdio MCP in Codex;
4. deploy the guarded HTTP container behind a protected gateway/private network;
5. run bilingual remote MCP smoke tests;
6. generate Skills-only and hosted-alpha readiness reports with real evidence;
7. fix only contract/runtime differences demonstrated by those runs;
8. make the explicit licensing, legal, authentication, quota and public-hosting
   decisions in `docs/public-launch-decisions.md` before broad launch.
