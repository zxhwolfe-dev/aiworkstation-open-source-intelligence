# Architecture

## Product goal

Convert AI Open Source Radar capabilities into reusable Skills and read-only
tools for evidence-backed project research, comparison and technology-stack
planning.

The distributable product is intentionally narrower than AI Workstation. It does
not reproduce the full website, private data-production pipeline,
administration system or user-account layer.

## Current layered design

```text
User / ChatGPT / Codex / MCP client
                 |
                 v
Skills: trigger rules, workflow, tool ordering, output policy
                 |
                 v
       +---------+------------------+
       |                            |
MCP stdio transport        Guarded Streamable HTTP transport
(local development)        (local/private hosted alpha)
       |                            |
       +-------------+--------------+
                     v
ToolRegistry: strict validation + unified result envelope
                     |
                     v
ProjectIntelligenceProvider protocol
          /                              \
Deterministic mock             Hardened public HTTP provider
                                           |
                                           v
AI Workstation public list/detail/selector endpoints
                                           |
                                           v
Current healthy validated Radar release
```

A reverse proxy/private-network boundary sits in front of non-local Streamable
HTTP deployments. It is outside the MCP application process and must provide
real authentication/private-network protection before hosted alpha access.

## Responsibilities

### Skills

Skills define when to run a workflow, what information to collect, which tools
to call, how to handle empty/conflicting evidence and how to present the answer.
They contain no live project database.

First Skills:

- `open-source-project-research`
- `open-source-project-comparison`
- `open-source-stack-planner`

### MCP tool registration

`src/aiworkstation_osi/mcp_server.py` defines exactly six read-only tools and
owns:

- MCP tool registration and typed signatures;
- server-wide workflow and safety instructions;
- read-only/non-destructive/idempotent/open-world annotations;
- conversion of stable product errors into model-readable tool failures.

It does not own project search, evidence, comparison or provider logic.

### Transport entrypoints

`osi-mcp` runs the tool set over stdio and opens no network listener.

`osi-mcp-http` runs the same server over stateless JSON Streamable HTTP. It owns
only deployment configuration and fail-closed bind policy:

- safe default `127.0.0.1:8000`;
- non-loopback binds require explicit private-network/reverse-proxy
  acknowledgement;
- non-loopback mode requires the live HTTP provider;
- live Radar origin is restricted to allow-listed HTTPS origins;
- the bind acknowledgement is explicitly not authentication.

No business logic is duplicated between transports.

### Tool core

`src/aiworkstation_osi/tools.py` and adjacent contract modules own:

- stable tool names;
- strict top-level and nested input validation;
- error normalization;
- the provider boundary;
- the unified result envelope;
- deterministic mock behavior for tests.

There is no implicit live network access. Live Radar reads occur only when
`OSI_PROVIDER=http` is explicitly selected.

### Provider adapters

The provider protocol permits multiple read-only data sources without changing
Skills or MCP definitions.

#### Mock provider

- deterministic and offline;
- clearly marked `MOCK_DATA`;
- suitable for development/protocol tests only.

#### Public HTTP provider

- calls public AI Workstation Radar endpoints only;
- never imports private `akaiagents` modules;
- requires public snapshot identity;
- rejects mixed snapshots and unsafe selector states;
- keeps near matches separate;
- converts missing/sentinel licenses into unknowns;
- rejects malformed/oversized/internal-field responses.

### Validation and replay layer

`osi-probe` checks live facts/license/search behavior.

`osi-capture-contracts` creates bounded sanitized public response fixtures.

`osi-validate-contracts` verifies fixture invariants without network access.

`osi-replay-contracts` feeds those exact captured contracts through the same
hardened provider used by runtime entrypoints. Locale and project identity come
from the capture manifest.

`osi-remote-smoke` connects through a real MCP client to a deployed Streamable
HTTP endpoint, verifies the six-tool surface and annotations, and can optionally
perform one read-only search. Remote endpoints require credential-free HTTPS.

## Unified result contract

Every successful tool returns `osi.tool-result.v1` with first-class fields:

- `data`: tool-specific structured output;
- `verified_facts`: facts with confidence and evidence;
- `recommendations`: analysis with rationale and assumptions;
- `unknowns`: missing or unverified conditions;
- `risks`: explicit adoption, license, security or integration limits.

A transport cannot collapse these boundaries into an undifferentiated answer.

## Tool set

| Tool | Purpose | Writes |
| --- | --- | ---: |
| `search_ai_projects` | Find candidates from requirements and constraints. | No |
| `get_project_facts` | Get current facts for one stable project ID. | No |
| `get_license_evidence` | Get observed license evidence without legal conclusions. | No |
| `compare_ai_projects` | Compare two to five projects in one decision context. | No |
| `find_alternatives` | Find constrained alternatives to a project. | No |
| `compose_ai_stack` | Compose a candidate architecture from verified components. | No |

## Snapshot and evidence rules

Time-sensitive comparisons and hydrated candidates use one current public
snapshot. The system fails closed rather than combining incompatible project
generations.

A public response becomes a verified fact only after the adapter establishes
stable project identity, compatible snapshot identity, public observation source
and time, adequate coverage and a non-conflicting evidence/license state.

Recommendations, architecture choices and cross-project compatibility remain
analysis even when individual component facts are valid.

## Trust model

- user input is untrusted;
- repository/web text is untrusted data;
- provider output is untrusted until validated;
- third-party code is never executed;
- missing license is unknown, not permission;
- compatibility is unknown until verified/tested;
- near matches are not formal recommendations;
- production response fixtures are sanitized before retention;
- a network bind is not authentication;
- hosted gateway/private-network attestations are operator claims that must map
  to real infrastructure.

## Container/deployment boundary

The runtime image includes only the Python package and MCP dependency. It runs as
a non-root user. The example Compose deployment uses a read-only filesystem,
bounded tmpfs, dropped capabilities, `no-new-privileges`, resource limits and a
host-loopback port mapping.

Those controls are defense in depth. TLS, identity, rate limiting, abuse
blocking, production logging and public DNS remain infrastructure concerns.

## Current M1 Alpha scope

Included:

- three complete Skills;
- six bounded read-only tools;
- unified contracts and error model;
- deterministic mock provider;
- hardened public Radar provider;
- stdio MCP transport;
- guarded Streamable HTTP transport;
- non-root container/private-alpha Compose scaffold;
- local and remote MCP compatibility tests;
- bilingual evals and public-contract validation/replay;
- Skills-only plugin and deterministic alpha archive;
- four-level readiness report;
- security, privacy, support, deployment and release documentation.

Not included:

- native per-user OAuth/authorization and revocation;
- production quotas, billing, rate limits and abuse control;
- final hosted MCP platform connection mapping;
- public plugin-directory submission;
- production SLA/multi-region observability infrastructure;
- write tools, saved projects, alerts or teams;
- compatibility guarantees between third-party projects.

## Validation path

Before invited Skills-only alpha:

1. run local and GitHub CI;
2. run/review bilingual production contracts;
3. test the Skills package and stdio MCP from Codex;
4. generate `external_alpha_ready=true` with real evidence.

Before invited hosted private alpha:

5. deploy the guarded container behind an authenticated gateway or trusted
   private network;
6. run bilingual remote MCP smoke tests;
7. generate `hosted_private_alpha_ready=true` with real evidence.

Before broad public hosting:

8. implement the selected identity/OAuth, revocation, quota, rate-limit and
   abuse model;
9. publish final legal/support URLs and select the software license;
10. register/review the final platform connection.

Any missing upstream Radar field becomes a documented minimal additive request
for `akaiagents`; this repository does not modify that project's main branch.
