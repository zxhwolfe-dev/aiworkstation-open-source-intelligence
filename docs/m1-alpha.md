# M1 Alpha

M1 connects the M0 contracts to AI Workstation's public Open Source Radar and
exposes them through a local MCP stdio server. It remains read-only and is not a
public hosted service.

## Delivered

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

Tools return structured `osi.tool-result.v1` data. Stable product errors are
converted into model-readable tool failures without exposing private exception
details.

### Public contract probe

`osi-probe` performs three anonymous read-only checks against a configured Radar
origin:

1. resolve one named project and verify snapshot/evidence boundaries;
2. inspect license evidence or an explicit unknown state;
3. run one constrained search and require verified candidates or an explicit
   no-match reason.

The report is sanitized and suitable for CI artifacts or deployment checks. It
does not include credentials or full private prompts.

## Local commands

```bash
python -m pip install -e ".[mcp]"
python -m unittest discover -s tests -v

# Offline MCP server
OSI_PROVIDER=mock osi-mcp

# Live read-only MCP server
OSI_PROVIDER=http \
AIWORKSTATION_RADAR_BASE_URL=https://aiworkstation.cn \
osi-mcp

# Contract probe
osi-probe --base-url https://aiworkstation.cn --locale en
osi-probe --base-url https://aiworkstation.cn --locale zh
```

## Alpha acceptance gates

- [x] Live provider requires explicit opt-in.
- [x] Default installation remains offline and deterministic.
- [x] Project facts require snapshot identity.
- [x] Mixed-snapshot comparisons fail closed.
- [x] License sentinels cannot become verified facts.
- [x] Near-match boundaries are enforced.
- [x] MCP server has in-memory list/call/error tests.
- [x] Public probe has deterministic evaluation tests.
- [ ] Full local test suite has been run successfully after pulling `main`.
- [ ] GitHub Actions success has been observed for Python 3.10 and 3.12.
- [ ] English production probe passes.
- [ ] Chinese production probe passes.
- [ ] Representative production responses have been saved as sanitized contract
      fixtures.

## Not yet included

- hosted Streamable HTTP MCP;
- OAuth, API keys, quotas or billing;
- public plugin-directory submission;
- saved projects, alerts, team workspaces or other writes;
- server-side LLM generation inside the distribution repository;
- guarantees that any proposed projects are mutually compatible.

## Next milestone: M1 validation

The next task is operational validation, not feature expansion:

1. pull and run all tests locally;
2. run both public probes from an environment that can reach the production
   domain;
3. save sanitized fixtures for project list, detail, selector no-match and
   selector formal-result responses;
4. adjust the adapter only where real public fields differ from the documented
   contract;
5. then prepare a local Codex MCP configuration and a small external tester
   release.
