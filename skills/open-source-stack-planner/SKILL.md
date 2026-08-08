---
name: open-source-stack-planner
description: Design a candidate open-source AI technology stack from business goals, deployment/privacy/budget constraints and live AI Open Source Radar evidence. Use for RAG, Agent, knowledge-base and AI application architecture planning.
---

# Open Source Stack Planner

Use this Skill when the user wants a practical architecture assembled from open-source AI projects rather than a single-project recommendation.

The generated architecture is a recommendation. Individual project facts may be verified; cross-project compatibility remains unknown until tested.

## Route the request

### Architecture roles first

Before choosing projects, decompose the goal into necessary roles such as:

- UI/application surface;
- Agent/orchestration;
- document ingestion/parsing;
- retrieval/reranking;
- model serving/API;
- vector/relational storage;
- authentication/authorization;
- observability/evaluation;
- deployment/secrets management.

Do not add a component just because it is popular.

### Discover candidate components

Use `get_radar_overview` + `browse_radar_projects` when the user wants candidates from a specific current category, collection, scenario or ranking context.

Use `compose_ai_stack` for a business-goal/constraints-driven candidate composition. Verify serious components with `get_project_facts` and `get_license_evidence`; use `find_alternatives` or `compare_ai_projects` when a role has competing candidates.

### Explicit deeper architecture analysis

If `deep_research_ai_projects` is available, use `focus=stack` only when the user explicitly requests a deeper publisher-model architecture brief after standard Radar evidence has been gathered.

Premium narrative remains analysis, not verified compatibility.

## Live-tool availability gate

Before naming current projects as architecture components, confirm the required live tools are available.

If live tools are unavailable:

1. Do not populate the roles with remembered project names; use neutral role names instead.
2. state that live project evidence is unavailable;
3. produce a vendor-neutral reference architecture using role names;
4. specify the facts, interfaces and compatibility tests required before selecting each role;
5. label user-supplied project examples as unverified.

A generic architecture can still be useful, but it must not imply that a named project currently satisfies the requirements.

## Define operating context

Collect the minimum useful inputs:

- business goal/success condition;
- users, scale and workload;
- data types/sensitivity;
- self-hosted/cloud/offline/hybrid requirement;
- existing infrastructure/stack;
- preferred languages/frameworks;
- available hardware;
- engineering/operations skill;
- budget/delivery horizon;
- authentication, permission and audit needs;
- license/commercial-use constraints.

Ask a focused clarification when deployment, data sensitivity or expected scale is missing and would materially change the architecture. Otherwise state a conservative assumption.

## Compose and verify components

When `compose_ai_stack` is available:

1. call it with the business goal, structured constraints and existing stack;
2. call `get_project_facts` for decision-critical facts;
3. call `get_license_evidence` when licensing affects adoption;
4. use `find_alternatives` when a candidate conflicts with a hard requirement or lacks evidence;
5. use `compare_ai_projects` when two candidates remain viable for one role.

Do not claim two projects integrate successfully merely because each is individually valid. Mark integration unverified unless evidence or a controlled test supports it.

## Design the architecture

Describe:

- components/roles and responsibilities;
- data flow/trust boundaries;
- deployment topology;
- persistent data/backup needs;
- external network dependencies;
- secrets/permission boundaries;
- likely cost/operational drivers;
- failure/fallback behavior.

Separate verified component facts from architectural choices and assumptions.

## Implementation path

Use incremental stages:

1. requirements/evidence verification;
2. isolated proof of concept;
3. integration/compatibility tests;
4. security/privacy/license review;
5. evaluation against a fixed test set;
6. staged deployment/observability;
7. rollback/replacement plan.

Test the highest-risk unknown first rather than implementing the whole architecture.

## Output

### Assumptions and hard constraints

List what is known, assumed and missing.

### Recommended architecture

Show a readable component/data-flow diagram and concise explanation. Without live tools, use neutral role names rather than remembered project names.

### Component table

For verified candidates include:

- role;
- primary project/stable ID;
- verified facts/evidence;
- reason selected;
- alternative;
- unresolved compatibility/license issue.

### Implementation plan

Give ordered stages, validation criteria and rollback points.

### Risks and unknowns

Cover integration, operations, security, privacy, license, data migration and maintenance.

### Recommendation

State whether to prototype, gather more evidence or avoid the stack under current constraints.

## Safety and quality rules

- Never execute third-party project code as part of research.
- Never expose/commit credentials.
- Never present estimated compatibility as verified compatibility.
- Never hide missing evidence behind an architecture diagram.
- Never treat a license observation as legal advice.
- Never claim a current named-project stack when required live tools are unavailable.
- Prefer replaceable interfaces and staged adoption.
- Never invoke Premium AI without an explicit deeper-analysis request.
