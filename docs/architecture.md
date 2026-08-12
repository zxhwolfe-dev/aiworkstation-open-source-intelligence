# Architecture

## Product goal

AI Open Source Intelligence converts public AI Open Source Radar capabilities
into one reusable Skill and nine read-only tools for evidence-backed project
research, comparison and technology-stack planning.

It is intentionally narrower than AI Workstation. It does not reproduce the
private data-production pipeline, account system, payments, administration or
server-side model products.

## Current product shape

```text
User in ChatGPT / Codex / compatible MCP host
                    |
                    v
        ai-open-source-intelligence Skill
                    |
                    v
              9 MCP tools
          /                    \
 local stdio MCP        public Hosted MCP
 mock or HTTP provider  mcp.aiworkstation.cn
          \                    /
                    v
       hardened public Radar provider
                    |
                    v
        AI Workstation public Radar APIs
```

The host model performs natural-language reasoning and final synthesis. The
current AI Workstation path supplies data/evidence only and fixes selector
requests to `use_model=false`.

## Unified Skill

The only active product Skill is:

```text
ai-open-source-intelligence
```

It routes Radar browsing, project discovery, fact/license verification,
comparison, alternatives and stack planning. The Skill contains no live project
database and must not substitute model memory when current evidence is
unavailable.

## Nine-tool surface

`src/aiworkstation_osi/mcp_server.py` registers exactly nine MCP tools:

| Tool | Purpose | Writes business data |
| --- | --- | ---: |
| `search_ai_projects` | Find candidates from typed requirements. | No |
| `get_project_facts` | Get current facts for one stable project ID. | No |
| `get_license_evidence` | Inspect direct license evidence without legal conclusions. | No |
| `compare_ai_projects` | Compare two to five projects in one decision context. | No |
| `find_alternatives` | Find alternatives while preserving hard requirements. | No |
| `compose_ai_stack` | Build a candidate architecture and expose unknown compatibility. | No |
| `get_radar_overview` | Discover current Radar views and navigation dimensions. | No |
| `browse_radar_projects` | Browse rankings, collections, categories and filtered projects. | No |
| `browse_radar_skills` | Browse or inspect the public Radar Skills library. | No |

All tools advertise read-only, non-destructive, idempotent and open-world MCP
annotations. They never install or execute third-party repository code.
Requirement selection may create, poll or cancel a short-lived upstream task;
that control-plane effect is disclosed and is not a user/third-party business
data write.

## Transport entrypoints

### Local stdio

`osi-mcp` opens no network listener. It uses deterministic mock data unless
`OSI_PROVIDER=http` is selected explicitly.

### Local / self-hosted Streamable HTTP

`osi-mcp-http` defaults to `127.0.0.1:8000`. Non-loopback binds require explicit
Host policy, an approved public Radar origin and a deployment acknowledgement.
The acknowledgement is not authentication.

### Production Hosted MCP

`osi-mcp-hosted` runs the anonymous data-only server at the canonical public
endpoint:

```text
https://mcp.aiworkstation.cn/mcp
```

The container listens only through host loopback `127.0.0.1:8001` behind
Nginx/TLS. The dedicated hostname proxies `/mcp`, returns `404` elsewhere,
enforces strict Host behavior, limits request bodies and applies per-IP short,
sustained and concurrent-connection controls.

The current Hosted access mode is only:

```text
OSI_HOSTED_ACCESS_MODE=public
```

OAuth/Premium configuration fails closed. There is no checkout, credits,
membership lookup or AI Workstation server-model tool in this release.

## Provider boundary

`FullToolRegistry` extends the six selection/evidence operations with three
Radar browsing operations. Both registry layers depend on a read-only
`ProjectIntelligenceProvider` protocol.

### Mock provider

- deterministic and offline;
- clearly marked `MOCK_DATA`;
- suitable only for development and protocol tests.

### Public HTTP provider

- calls anonymous public Radar routes only;
- never imports private `akaiagents` modules;
- validates project and snapshot identity;
- rejects mixed snapshots and internal-field leakage;
- requires safe selector evidence states;
- keeps formal matches separate from near matches;
- converts missing/sentinel licenses into unknowns;
- rejects malformed, deep, oversized or unsafe responses.

## Result contract

Every success uses `osi.tool-result.v2` and keeps these boundaries first-class:

- `data`: tool-specific structured output;
- `verified_facts`: source-backed facts with observation context;
- `recommendations`: analysis with rationale and assumptions;
- `unknowns`: missing or unverified conditions;
- `risks`: license, maintenance, deployment, security or integration limits.

Every expected product error uses `osi.error.v2`. Transports must not collapse
these structures into an undifferentiated answer.

## Trust and evidence rules

- user input and retrieved repository/web text are untrusted;
- provider output is untrusted until adapter validation passes;
- missing license evidence is unknown, not permission;
- hard requirements are not silently weakened;
- near matches never become formal matches;
- compatibility remains unverified until evidence or controlled testing exists;
- contract captures are sanitized before retention;
- operator deployment attestations must map to real infrastructure evidence.

## Release and deployment identity

Every production candidate binds:

```text
source commit
  = release target commit
  = OCI revision / OSI_IMAGE_COMMIT
  = OSI_RELEASE_COMMIT
  = remote serverInfo.version commit
```

Candidate-bound CI, bilingual contract validation, Codex nine-tool acceptance,
human artifact review, exact-image deployment and bilingual remote smoke must be
repeated for a changed runtime candidate.

The `v0.3.1` Plugin/package candidate does not mutate the existing `v0.3.0` tag
or deployed image. If operators later deploy a `v0.3.1` runtime image, the full
candidate-bound runtime evidence chain above must be repeated first.

## Current scope and deferred work

Included now:

- one unified Skill;
- nine anonymous read-only tools;
- mock and hardened public HTTP providers;
- stdio and guarded Streamable HTTP transports;
- public production Hosted MCP with gateway controls;
- deterministic Skill archive and Python package;
- bilingual validation, replay and release evidence tooling.

Deferred until real usage justifies a new reviewed version:

- server-side model inference, login, membership and billing;
- saved projects, alerts, teams and write-capable tools;
- compatibility guarantees for independent third-party projects;
- multi-region/SLA infrastructure.

Public plugin-directory approval, fresh-install user acceptance and External
Alpha retention measurement are release/operations work, not hidden runtime
capabilities.
