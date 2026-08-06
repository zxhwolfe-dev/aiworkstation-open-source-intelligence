# M1 Alpha

M1 connects the M0 contracts to AI Workstation's public Open Source Radar,
exposes them through a local MCP stdio server, and packages the three workflows
as a local skills-only plugin. It remains read-only and is not a public hosted
service.

## Delivered

### Skills-only plugin package

The repository root now contains:

- `.codex-plugin/plugin.json` with stable identity, install-surface metadata and
  the `./skills/` package path;
- `.agents/plugins/marketplace.json` for repo-scoped local installation;
- three complete Skill workflows;
- package tests that verify paths, frontmatter, capabilities and intentional
  omissions.

The plugin does not yet declare `mcpServers` or `apps`. The current stdio server
requires a separately installed Python environment, and no registered hosted MCP
technical ID exists yet. Adding either manifest field before its target is
portable and tested would create a broken package.

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
- Listing and detail snapshots must match.
- Comparisons and hydrated candidate sets must use one snapshot.
- Selector evidence must be `available`, or `partial` with a public notice.
- Near matches must have exactly one blocker and cannot coexist with formal
  recommendations.
- Internal publication fields in selector responses fail closed.
- Unknown license sentinels such as `NOASSERTION`, `UNKNOWN` and `UNLICENSED`
  never become verified licenses.
- Non-standard labels such as `OTHER` are observations, but carry a high-risk
  manual-review warning.
- HTTP 408, 425, 429 and 5xx responses are retryable provider failures.
- Invalid JSON, oversized responses and malformed public contracts fail closed.

### MCP stdio server

`osi-mcp` exposes exactly six synchronous read-only tools through MCP Python SDK
v2:

- `search_ai_projects`
- `get_project_facts`
- `get_license_evidence`
- `compare_ai_projects`
- `find_alternatives`
- `compose_ai_stack`

All six tools are annotated as read-only, non-destructive, idempotent and
open-world. Tools return structured `osi.tool-result.v1` data. Stable product
errors are converted into model-readable tool failures without exposing private
exception details.

### Public contract probe and fixtures

`osi-probe` performs three anonymous read-only checks against a configured Radar
origin:

1. resolve one named project and verify snapshot/evidence boundaries;
2. inspect license evidence or an explicit unknown state;
3. run one constrained search and require verified candidates or an explicit
   no-match reason.

`osi-capture-contracts` records bounded, sanitized response shapes. It removes
query text, credentials, client IDs and internal publication fields.

`osi-validate-contracts` verifies the captured list, detail, formal selector and
no-match selector contracts offline before manual review.

## Local commands

```bash
python -m pip install -e ".[mcp]"
python -m unittest discover -s tests -v

# Validate plugin package JSON
python -m json.tool .codex-plugin/plugin.json >/dev/null
python -m json.tool .agents/plugins/marketplace.json >/dev/null

# Offline MCP server
OSI_PROVIDER=mock osi-mcp

# Live read-only MCP server
OSI_PROVIDER=http \
AIWORKSTATION_RADAR_BASE_URL=https://aiworkstation.cn \
osi-mcp

# Contract probes
osi-probe --base-url https://aiworkstation.cn --locale en
osi-probe --base-url https://aiworkstation.cn --locale zh
```

## Alpha acceptance gates

- [x] Three Skills are packaged under a valid plugin manifest.
- [x] A repo-scoped local marketplace entry exists.
- [x] The manifest does not claim an ungranted license or unready MCP mapping.
- [x] Live provider requires explicit opt-in.
- [x] Default installation remains offline and deterministic.
- [x] Project facts require snapshot identity.
- [x] Mixed-snapshot comparisons fail closed.
- [x] License sentinels cannot become verified facts.
- [x] Near-match boundaries are enforced.
- [x] MCP server has in-memory list/call/error and annotation tests.
- [x] Public probe has deterministic evaluation tests.
- [x] Contract capture and offline fixture validation have deterministic tests.
- [ ] Full local test suite has been run successfully after pulling `main`.
- [ ] GitHub Actions success has been observed for Python 3.10 and 3.12.
- [ ] The local Skills plugin has been installed through the repo marketplace.
- [ ] English production probe passes.
- [ ] Chinese production probe passes.
- [ ] Representative production responses have been captured, validated and
      manually reviewed.
- [ ] The stdio MCP server has been called successfully from Codex.

## Not yet included

- plugin-bundled MCP configuration;
- registered hosted MCP mapping;
- hosted Streamable HTTP MCP;
- OAuth, API keys, quotas or billing;
- public plugin-directory submission;
- final privacy policy, terms, support URL, icons or screenshots;
- saved projects, alerts, team workspaces or other writes;
- server-side LLM generation inside the distribution repository;
- guarantees that any proposed projects are mutually compatible.

## Next milestone: M1 validation

The next task is operational validation, not feature expansion:

1. pull and run all tests locally;
2. install the skills-only package from the repo marketplace;
3. run both public probes from an environment that can reach production;
4. capture and validate the four sanitized response scenarios in both languages;
5. adjust the adapter only where real public fields differ from the documented
   contract;
6. connect and call the local stdio MCP server from Codex;
7. then decide between a portable bundled `.mcp.json` and a registered hosted
   `.app.json` mapping for the combined plugin.
