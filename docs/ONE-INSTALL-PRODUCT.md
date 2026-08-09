# One-install product architecture

## Product goal

AI Open Source Intelligence should feel like one useful capability, not a pile of infrastructure choices.

The first Hosted experience is intentionally frictionless:

```text
Install / connect product
      |
ChatGPT / Codex / compatible MCP host
      |
3 Skills + public Hosted MCP
      |
9 anonymous read-only Radar tools
      |
AI Open Source Radar
```

The user should not need to clone the repository, configure Python, copy API keys, create a WorkOS account, or understand the implementation split between Skill instructions and MCP tools.

## Skills

The three Skills define the decision process:

- `open-source-project-research`
- `open-source-project-comparison`
- `open-source-stack-planner`

They preserve hard/preferred/negative requirements, evidence boundaries, unknowns and risk disclosures.

## Nine standard Radar tools

1. `search_ai_projects`
2. `get_project_facts`
3. `get_license_evidence`
4. `compare_ai_projects`
5. `find_alternatives`
6. `compose_ai_stack`
7. `get_radar_overview`
8. `browse_radar_projects`
9. `browse_radar_skills`

These are the default public Hosted surface. They are read-only and use public Radar data/retrieval. They do not invoke a publisher-funded model on every call.

## Public Hosted access boundary

Default:

```text
OSI_HOSTED_ACCESS_MODE=public
```

Public mode has no user identity requirement. Abuse protection belongs at the HTTPS gateway and includes bounded per-IP request and connection controls.

The application still keeps strict deployment identity:

```text
candidate Git SHA
  = Docker image SHA identity
  = runtime release SHA
  = remote MCP serverInfo.version SHA
```

The public mode therefore removes login friction without making release provenance anonymous or unverifiable.

## Optional Premium server-model tool

OAuth compatibility mode retains:

```text
deep_research_ai_projects
```

Flow:

```text
explicit user request for deeper analysis
    |
rules-first Radar retrieval
    |
bounded public Radar context
    |
AI Workstation publisher model
    |
model analysis returned separately from verified facts
```

This tool is absent from the default public Hosted mode.

## Cost boundary

```text
Nine standard tools
    -> public Radar data/retrieval
    -> no publisher-model token cost

Normal Skill reasoning
    -> ChatGPT/Codex host model
    -> host/user-side inference

Future member-only deep research
    -> AI Workstation publisher model
    -> unified AI Workstation membership/quota policy
```

The final paid product should not introduce a confusing second OSI credit balance merely because MCP is a different entry point.

## Membership boundary

AI Workstation membership is the intended source of truth.

```text
                    AI Workstation membership
                              |
                  +-----------+-----------+
                  |                       |
              website                 Skills/MCP
                  |                       |
                  +-----------+-----------+
                              |
                    unified AI usage policy
```

Manual WeChat/email/offline payment and current membership activation may continue while scale is small.

A future payment provider is an automation adapter to that same membership, not a second entitlement database.

## Identity boundary for future member-only tools

Public tools need no identity.

Before member-only tools are enabled, an MCP client must have a secure way to prove which AI Workstation member it is linked to. That identity bridge can be OAuth or another reviewed approach, but the identity provider must remain separate from the membership truth source.

Never use:

- a reusable invite/activation code directly as an MCP bearer token;
- raw bearer tokens as membership database keys;
- client-supplied usernames as trusted membership identity;
- payment customer IDs as public MCP identities.

WorkOS is one optional OAuth provider, not a requirement.

## Rate limits

Public mode:

- Nginx per-IP request limit;
- Nginx per-IP connection limit;
- bounded request body;
- loopback-only MCP upstream;
- normal application/provider bounds remain intact.

Optional OAuth mode additionally retains per-authenticated-subject limits.

## Deployment components

### Public Hosted Private Alpha

```text
MCP host
   |
   | HTTPS
   v
Nginx TLS + IP abuse controls
   |
   | loopback
   v
Hosted MCP public mode
   |
   +---- public Radar API (9 standard tools)
```

### Future member/Premium mode

```text
MCP host
   |
secure member identity/linking
   |
Hosted MCP member-capable mode
   |
   +---- public Radar API
   |
   +---- narrow private AI Workstation membership/Premium contract
              |
              +---- existing membership source of truth
              +---- unified quota/usage accounting
              +---- publisher model
```

Payment automation, if any, updates the existing membership system separately.

## Current release gate

For Hosted Private Alpha, real external validation must prove:

- exact candidate/deployment identity;
- public HTTPS endpoint;
- gateway abuse-control policy;
- exactly nine read-only standard tools;
- a successful real Radar search;
- fresh candidate CI/live/Codex/human evidence.

OAuth, WorkOS and automated payment are not required for this free private-alpha milestone.

Before any paid/member-only launch, secure member linking and unified AI Workstation quota accounting become separate mandatory gates.
