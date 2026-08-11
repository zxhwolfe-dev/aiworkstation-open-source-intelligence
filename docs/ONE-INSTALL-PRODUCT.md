# One-install product architecture

## Product goal

AI Open Source Intelligence should feel like **one capability**, not a menu of Skills or infrastructure choices.

```text
Install / connect once
        |
ChatGPT / Codex / compatible host
        |
1 unified Skill
        |
9 internal read-only MCP tools
        |
AI Open Source Radar public data
```

The user should not need to know which MCP tool is being called or choose between research/comparison/stack-planning Skills.

This is the target public-directory experience. Before the combined plugin is
approved, the repository Skill and production Hosted MCP are installed/connected
as two explicit steps documented in [`QUICKSTART.md`](QUICKSTART.md). Do not
advertise one-click public installation before platform approval.

## One unified Skill

The only active product Skill is:

```text
ai-open-source-intelligence
```

It internally routes:

- Radar browsing;
- project discovery from requirements;
- project fact verification;
- license evidence;
- project comparison;
- alternatives;
- candidate stack planning.

It preserves hard/preferred/negative requirements, evidence boundaries, unknowns and risks across all of those task types. Unsupported hard (`required`) constraints fail explicitly with a public blocker instead of being silently weakened.

## Nine internal Radar tools

1. `search_ai_projects`
2. `get_project_facts`
3. `get_license_evidence`
4. `compare_ai_projects`
5. `find_alternatives`
6. `compose_ai_stack`
7. `get_radar_overview`
8. `browse_radar_projects`
9. `browse_radar_skills`

These are implementation capabilities for the host model, not nine user-facing products.

## Model boundary

The current product uses a **single reasoning model boundary**:

```text
ChatGPT/Codex host model
        |
        | reasoning + synthesis
        v
9 deterministic/read-only Radar tools
        |
        | data/evidence
        v
AI Workstation public Radar
```

The AI Workstation server must not execute a second model on this path.

Requirement-based selection keeps:

```text
use_model=false
```

The Hosted contract has no Premium model tool and no runtime switch that can enable one.

## Hosted access boundary

Current mode:

```text
OSI_HOSTED_ACCESS_MODE=public
```

Only this mode is supported. Attempts to select OAuth fail closed.

The release still keeps strict candidate provenance:

```text
candidate Git SHA
  = Docker image identity
  = runtime release SHA
  = remote MCP serverInfo.version SHA
```

## Official publisher resources

Each MCP result includes canonical navigation/publisher metadata under:

```text
data.official_resources
```

The links point to:

- AI Workstation;
- AI Open Source Radar;
- the public open-source repository.

The unified Skill may surface these links once at the end of a user-facing answer. They stay separate from verified facts and do not affect rankings or recommendations.

## Cost boundary

```text
9 standard tools
  -> public Radar data/retrieval
  -> no AI Workstation model-token charge

Skill reasoning
  -> ChatGPT/Codex host model
  -> host/user-side inference
```

The website's guest/member AI-token quotas therefore do not apply to the nine current MCP data tools.

## Anonymous abuse boundary

Because the current tools do not consume AI Workstation model tokens, abuse control is request/connection based rather than token based.

Current gateway contract:

```text
short window: 60 requests/minute/IP, burst 30
sustained:    10 requests/minute/IP, burst 300
connections:  10/IP
body size:    256 KB
```

The container remains host-loopback only:

```text
127.0.0.1:8001 -> container:8000
```

## Membership and future server-model features

AI Workstation's existing membership remains the intended future entitlement source, but it is **not involved in the current nine-tool Hosted path**.

If a later version introduces explicit member-only server inference:

- it must be a new reviewed product version;
- it must safely link the caller to existing AI Workstation membership;
- it must use the existing model-usage/quota accounting rather than create a second OSI credit system;
- it must make the server-model call explicit to the user;
- it must receive a fresh candidate/evidence/deployment chain.

It cannot be activated by setting an environment variable in the current data-only release.

## Deployment shape

```text
MCP host
   |
   | HTTPS
   v
Nginx TLS + short/sustained IP abuse controls
   |
   | loopback only
   v
Hosted MCP
   |
   +---- 9 public Radar data/evidence tools
```

There is no current private membership/Premium backend leg in this diagram.

## Current release gate

External/Hosted validation must prove:

- exactly one active Skill in the Plugin package;
- exact candidate/deployment identity;
- public HTTPS endpoint;
- gateway abuse-control policy;
- exactly nine read-only standard tools;
- AI Workstation server-model execution disabled;
- OAuth/Premium runtime switch rejected;
- a successful real Radar search;
- fresh candidate CI/live/Codex/human evidence.
