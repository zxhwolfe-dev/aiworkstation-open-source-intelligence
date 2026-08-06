---
name: open-source-stack-planner
description: Design a candidate open-source AI technology stack from a business goal, deployment environment, privacy requirements, budget and engineering constraints. Use for RAG, Agent, internal knowledge-base and AI application architecture planning.
---

# Open Source Stack Planner

Use this Skill when the user wants a practical architecture assembled from
open-source AI projects rather than a single-project recommendation.

The generated architecture is a recommendation. Individual project facts may be
verified, but cross-project compatibility remains unknown until tested.

## Step 1: define the operating context

Collect the minimum decision inputs:

- business goal and success condition;
- users, scale and expected workload;
- data types and sensitivity;
- self-hosted, cloud, offline or hybrid requirement;
- existing infrastructure and technology stack;
- preferred languages or frameworks;
- available hardware;
- engineering and operations skill;
- budget and delivery horizon;
- authentication, permission and audit needs;
- license or commercial-use constraints.

Ask a focused clarification when deployment, data sensitivity or expected scale
is missing and would materially change the architecture. Otherwise declare a
conservative assumption.

## Step 2: decompose the system

Break the goal into necessary roles before choosing projects. Depending on the
scenario, roles may include:

- user interface;
- application or Agent orchestration;
- document ingestion and parsing;
- retrieval and reranking;
- model serving or model API;
- vector or relational storage;
- authentication and authorization;
- observability and evaluation;
- deployment and secrets management.

Do not add a component merely because it is popular. Every component must have a
clear job in the proposed system.

## Step 3: compose candidate components

Call `compose_ai_stack` with the business goal, structured constraints and
existing stack. For every proposed component:

1. call `get_project_facts` for decision-critical facts;
2. call `get_license_evidence` when licensing affects adoption;
3. use `find_alternatives` when the primary component conflicts with a hard
   requirement or lacks evidence;
4. use `compare_ai_projects` when two candidates remain viable for one role.

Do not claim that two projects integrate successfully merely because each
project is individually valid. Mark the integration as unverified unless current
evidence or a controlled test supports it.

## Step 4: design the architecture

Describe:

- components and their responsibilities;
- data flow and trust boundaries;
- deployment topology;
- persistent data and backup needs;
- external network dependencies;
- secrets and permission boundaries;
- likely cost and operational drivers;
- failure and fallback behavior.

Separate verified component facts from architectural choices and assumptions.

## Step 5: create an implementation path

Use incremental stages:

1. requirements and evidence verification;
2. isolated proof of concept;
3. integration and compatibility tests;
4. security, privacy and license review;
5. evaluation against a fixed test set;
6. staged deployment and observability;
7. rollback and replacement plan.

The proof of concept should test the highest-risk unknown first, not implement
the entire architecture.

## Output structure

### Assumptions and hard constraints

List what is known, assumed and still missing.

### Recommended architecture

Show a readable component and data-flow diagram in text or Mermaid, followed by
a short explanation.

### Component table

For each role include:

- primary project and stable ID;
- verified facts and evidence;
- why it was selected;
- alternative;
- unresolved compatibility or license issue.

### Implementation plan

Provide ordered stages, validation criteria and rollback points.

### Risks and unknowns

At minimum cover integration, operations, security, privacy, license, data
migration and project-maintenance risk.

### Recommendation

State whether the user should prototype, gather more evidence or avoid the
proposed stack under the current constraints.

## Safety and quality rules

- Never execute third-party project code as part of research.
- Never expose credentials or recommend committing secrets.
- Never present estimated compatibility as verified compatibility.
- Never hide missing evidence behind an architecture diagram.
- Never treat a license observation as legal advice.
- Prefer replaceable interfaces and staged adoption over irreversible coupling.
