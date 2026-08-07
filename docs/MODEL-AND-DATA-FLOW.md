# Skills, MCP, Online Data, and Model Usage

This document explains where reasoning happens, where live data comes from, and which component pays for model inference.

## Current architecture

```text
User
  |
ChatGPT / Codex / other MCP host model
  |
  +--> Skills: reusable workflow and decision rules
  |
  +--> MCP tools: structured live-data operations
              |
       AI Workstation public Radar API
              |
       validated public Radar release
```

## Skills-only mode

The three Skills contain research procedure, safety boundaries, output structure, and verification logic. The current Skills-only package does **not** contain a live connection to the AI Workstation database.

When the live tools are unavailable, the Skills are required to:

- interpret requirements;
- preserve hard/preferred/not-required constraint polarity;
- create a search or verification plan;
- provide a blank decision matrix or role-level architecture;
- clearly state that current project facts are unavailable;
- avoid naming a current winner from model memory alone.

## Why MCP is the live-data boundary

MCP provides explicit tools with named schemas and read-only annotations. It makes the data dependency inspectable by the host and allows the publisher to control:

- which operations exist;
- authentication/identity;
- quotas and rate limits;
- timeouts and retries;
- logging and privacy boundaries;
- versioned tool contracts;
- deprecation and rollout;
- per-tool cost policy.

A Skill can package supporting scripts in some hosts, but script execution and networking are environment-dependent. Using hidden Skill scripts as the primary production database connector would be less portable and less observable than MCP.

## Online data exposed by the current MCP

The current MCP is **not** a mirror of the whole AI Workstation website. It exposes six task-oriented read-only capabilities:

1. `search_ai_projects`
2. `get_project_facts`
3. `get_license_evidence`
4. `compare_ai_projects`
5. `find_alternatives`
6. `compose_ai_stack`

Additional website features become available to MCP clients only after an explicit tool/API contract is designed and implemented for them.

## Model usage today

The current public Radar provider sends selector requests with:

```json
{"use_model": false}
```

Therefore the live Open Source Intelligence tool path does not require the AI Workstation backend to call a separate LLM for selector/search reasoning.

There are still two distinct reasoning layers:

### Host-model reasoning

ChatGPT, Codex, or another MCP host model:

- understands the user's natural-language request;
- selects Skills and tools;
- decides tool-call order;
- interprets structured results;
- writes the final explanation.

This inference belongs to the host environment and its user/account plan.

### AI Workstation data/retrieval layer

The current backend:

- resolves the validated Radar release;
- parses structured requirements deterministically;
- filters/retrieves/ranks public project records;
- returns project/detail/license/snapshot/evidence contracts;
- does not need a publisher-funded LLM call for the current `use_model=false` path.

## Future optional backend-model mode

If AI Workstation later enables model-assisted retrieval or synthesis, it should be explicit rather than implicit. Recommended controls:

- default `use_model=false` for ordinary structured research;
- enable model assistance only for tasks that demonstrate measurable quality gain;
- select a bounded model tier by task type;
- per-user/per-plan quotas;
- per-request token and cost ceilings;
- concurrency and timeout limits;
- cache reusable analysis when safe;
- retry transient failures at most a small bounded number;
- never let model failure weaken evidence/license/no-match boundaries;
- record safe aggregate usage without storing full confidential prompts;
- expose a clear fallback to deterministic retrieval.

## Recommended commercial split

A scalable product can keep the cost model simple:

```text
User's ChatGPT/Codex model
    -> user/host-side inference

AI Workstation MCP
    -> publisher-side data retrieval/API cost

Optional AI Workstation enhancement model
    -> publisher-side metered premium capability
```

This prevents every ordinary project search from creating a second, hidden LLM bill for the publisher.
