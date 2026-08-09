# Skill, Hosted MCP, Online Data, and Model Usage

This document defines the current product boundary for model usage.

## Current architecture

```text
User
  |
  v
ChatGPT / Codex / compatible host model
  |
  | natural-language reasoning and synthesis
  v
1 unified Skill: ai-open-source-intelligence
  |
  | structured tool calls
  v
Hosted MCP — 9 read-only data/evidence tools
  |
  | public Radar HTTP contracts only
  v
AI Workstation / AI Open Source Radar
```

There is **no AI Workstation server-side model call** in the current standard Skill/MCP product path.

## One Skill

The single Skill contains the workflow, safety boundaries, decision logic and output guidance for:

- Radar browsing;
- requirement-based discovery;
- project fact verification;
- license evidence;
- project comparison;
- alternatives;
- candidate stack planning.

The user does not choose separate research/comparison/stack Skills.

## Nine standard live Radar tools

```text
search_ai_projects
get_project_facts
get_license_evidence
compare_ai_projects
find_alternatives
compose_ai_stack
get_radar_overview
browse_radar_projects
browse_radar_skills
```

All nine are read-only data/evidence tools.

## Where reasoning happens

The host model — ChatGPT, Codex, or another compatible MCP host — performs:

- understanding the request;
- choosing the tool sequence;
- turning user intent into structured inputs;
- interpreting returned evidence;
- comparison/architecture reasoning;
- final answer generation.

That inference belongs to the host/user environment.

## What AI Workstation does

The AI Workstation side:

- serves current public Radar overview/project/Skills data;
- serves project/detail/license/evidence contracts;
- performs deterministic filtering, ranking and selector logic;
- returns structured data to the MCP host;
- does not run a second publisher/server model for this product path.

Requirement-based selector requests explicitly send:

```json
{
  "use_model": false
}
```

A regression test records the outbound selector request and fails if this field is not exactly `false`.

## Fail-closed server-model policy

The current Hosted runtime supports only:

```text
OSI_HOSTED_ACCESS_MODE=public
```

Attempts to set:

```text
OSI_HOSTED_ACCESS_MODE=oauth
```

fail closed.

The current Hosted contract has:

```text
tool_count=9
premium_enabled=false
server_model_enabled=false
oauth_enabled=false
```

The public Compose definition contains no OAuth credentials, private backend token or Premium-model configuration.

There is no `deep_research_ai_projects` tool in the current Hosted tool contract.

## Why this boundary exists

Calling an AI Workstation model for an ordinary Skill/MCP request would:

- duplicate reasoning already performed by the host model;
- create hidden publisher inference cost;
- complicate free/paid accounting;
- create an unnecessary privacy/model-data boundary;
- make simple data retrieval slower and harder to scale.

The current scalable path is therefore:

```text
host model + deterministic/public Radar data
```

not:

```text
host model + AI Workstation server model
```

## Official resources

Every MCP tool result adds canonical publisher resources under:

```text
data.official_resources
```

These contain AI Workstation, AI Open Source Radar and the public repository URLs. They are publisher/navigation metadata, not verified research facts.

## Anonymous abuse controls

Because the nine tools do not consume AI Workstation model tokens, the Hosted gateway uses request/connection limits rather than the website's token quota:

```text
short window: 60 requests/minute/IP, burst 30
sustained:    10 requests/minute/IP, burst 300
connections:  10/IP
body size:    256 KB
```

The website's guest/member AI-token quotas apply to website model features, not to these nine data-only MCP tools.

## Future paid/server-model capabilities

A future member-linked server-model capability is not forbidden forever, but it is deliberately **not present in this release**.

If introduced later, it must:

1. ship as a new reviewed product version;
2. have a fresh release/evidence chain;
3. use the existing AI Workstation membership source of truth;
4. explicitly disclose that AI Workstation server inference is being used;
5. account for model usage through the existing AI quota/usage system;
6. never be re-enabled through a hidden environment switch in the current data-only release.
