# One-install product architecture

## Product goal

The final AI Open Source Intelligence product should feel like one installation, not a collection of infrastructure parts.

```text
Install plugin
    |
OAuth sign-in once
    |
ChatGPT / Codex / compatible MCP host
    |
3 Skills + hosted MCP connection
    |
AI Open Source Radar
```

The user should not need to clone this repository, configure Python, copy API keys, know database details, or understand which answer came from a Skill versus a tool.

## Product surfaces

### Skills

The three Skills define the decision process:

- `open-source-project-research`
- `open-source-project-comparison`
- `open-source-stack-planner`

They preserve hard/preferred/negative requirements, evidence boundaries, unknowns and risk disclosures.

### Nine standard Radar tools

These cover the majority of useful AI Open Source Radar capabilities:

1. `search_ai_projects`
2. `get_project_facts`
3. `get_license_evidence`
4. `compare_ai_projects`
5. `find_alternatives`
6. `compose_ai_stack`
7. `get_radar_overview`
8. `browse_radar_projects`
9. `browse_radar_skills`

The three browse tools deliberately aggregate many website views into task-oriented operations.

`get_radar_overview` exposes discoverable navigation dimensions. The host can use it before a browse request rather than hard-coding ranking, collection, category or scenario IDs.

`browse_radar_projects` covers:

- rankings;
- collections;
- categories;
- scenarios/use cases;
- roles;
- topics;
- repository/Radar topics;
- resource type;
- license;
- deployment;
- content layer;
- text search;
- pagination.

`browse_radar_skills` covers:

- Skills-library search;
- category/kind/license filters;
- installable-only filtering;
- sort/pagination;
- single Skill detail by `skill_id`.

The website may continue to contain visualizations or UI-only conveniences that are not meaningful as MCP tools. MCP should expose user-value capabilities, not mirror every HTTP endpoint.

## Premium server-model tool

Hosted mode adds:

```text
deep_research_ai_projects
```

This is intentionally separate from ordinary data tools.

Flow:

```text
User asks for deep analysis
    |
rules-first Radar retrieval
    |
bounded public Radar context
    |
AI Workstation publisher model
    |
professional analysis returned as recommendation
```

The publisher model never becomes a substitute for the fact/evidence layer. Current project facts continue to come from the supplied Radar context.

## Cost boundary

```text
Nine standard tools
    -> public Radar data/retrieval
    -> no publisher AI credit

Normal Skill reasoning
    -> ChatGPT/Codex host model
    -> host/user-side inference

Premium deep research
    -> AI Workstation publisher model
    -> one free successful trial, then AI credits
```

This avoids a hidden second model bill on every ordinary project search.

## Identity boundary

Hosted mode requires OAuth. The MCP verifier receives a standard access token, validates issuer/resource/scope and derives an internal entitlement identity from:

```text
issuer + subject -> SHA-256 -> oidc_<opaque-id>
```

Only the opaque identity crosses the MCP-to-AI-Workstation backend boundary.

Do not use:

- IP address as the subscription identity;
- raw bearer tokens as database keys;
- client-supplied usernames;
- payment customer IDs as public MCP identities.

## Rate limits

Hosted mode applies per-authenticated-subject application limits. Initial code defaults are conservative launch values and remain configurable:

- standard tools: 60/minute and 300/hour;
- premium deep research: 5/minute, also subject to trial/credit entitlement.

A reverse proxy/gateway may additionally apply connection/IP abuse controls.

## Upgrade flow

For an unsubscribed user after the successful free premium task:

```text
premium call
  -> UPGRADE_REQUIRED
  -> hosted MCP asks backend for checkout
  -> model-visible result includes HTTPS checkout URL
  -> user pays in browser
  -> verified payment webhook updates the same opaque entitlement
  -> next premium call works without reinstalling the plugin
```

An active Pro/Enterprise user who exhausts monthly credits should not be offered a second subscription. A future one-time top-up product can be added separately.

## Deployment components

```text
OpenAI / MCP host
      |
      | OAuth bearer
      v
Hosted MCP (/mcp)
      |
      +---- public Radar API (9 standard tools)
      |
      +---- service-authenticated premium backend
                 |
                 +---- entitlement DB
                 +---- AI Workstation model runtime
                 +---- Paddle checkout/webhook adapter
```

The backend service credential is independent from user OAuth. Knowing a user subject is therefore insufficient to call premium backend APIs directly.

## Current release gate

The architecture is implemented as a candidate but should not be advertised as a live public hosted product until real OAuth, TLS, payment sandbox and remote MCP acceptance have passed.
