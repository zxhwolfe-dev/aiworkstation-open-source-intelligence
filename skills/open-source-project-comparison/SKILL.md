---
name: open-source-project-comparison
description: Compare two to five open-source AI projects for a specific use case using current facts, license evidence, deployment constraints and explicit trade-offs. Use for project-versus-project decisions and alternative selection.
---

# Open Source Project Comparison

Use this Skill when the user names two to five open-source AI projects or asks
which project is better for a defined scenario.

A project is never “best” without a context. Identify the user's use case and
blocking constraints before presenting a winner.

## Comparison boundary

Keep four layers separate:

- **verified facts** from current evidence;
- **comparison calculations** derived from those facts;
- **recommendations** conditioned on the user's priorities;
- **unknowns and risks** that could change the decision.

Do not convert popularity, marketing language or model preference into a fact.

## Live-tool availability gate

Before presenting a current comparison or winner, confirm that these companion
tools are available:

- `compare_ai_projects`;
- `get_project_facts`;
- `get_license_evidence` when license affects the decision.

The plugin can be installed as Skills-only. If the tools are unavailable:

1. do not fill the matrix with remembered or assumed project facts;
2. state that live evidence is unavailable in this session;
3. provide the decision context, criteria, weights, blank verification matrix
   and proof-of-concept plan;
4. mark all project-specific cells as `unknown` unless the user supplied a fact
   with a source, and keep user-supplied claims unverified;
5. direct the user to connect the companion read-only MCP server or use the AI
   Open Source Radar before requesting a winner.

Do not recommend one project over another solely from general model memory when
the live tools are absent.

## Step 1: define the decision

Collect or infer:

- two to five stable project IDs;
- intended use case and users;
- hard requirements;
- evaluation criteria;
- relative priority of criteria, when supplied;
- deployment, privacy and data-residency needs;
- available engineering skill and operating budget;
- license and commercial-use requirements;
- decision horizon: prototype, production or enterprise procurement.

If no criteria are given, use a neutral baseline and label it as an assumption:
function fit, deployment, maturity, maintenance, license, extensibility,
operational complexity and evidence coverage.

## Step 2: collect comparable facts

When available, call `compare_ai_projects` with two to five unique project IDs
and explicit criteria. Verify decision-critical fields with
`get_project_facts`. Call `get_license_evidence` for every candidate when
license affects adoption.

All compared records must come from one current snapshot or explicitly
compatible snapshots. If snapshot identity cannot be established, add a high
visibility uncertainty before comparing time-sensitive fields.

## Step 3: build the matrix

For each criterion use one of:

- `verified-match`;
- `verified-conflict`;
- `partial`;
- `unknown`;
- `not-applicable`.

Include evidence and observation time for verified cells. Do not fill an unknown
cell with a guessed score.

Useful criteria include:

- primary product fit;
- self-hosting and offline operation;
- Docker and supported deployment path;
- Web UI and required coding level;
- document, RAG or Agent capability;
- authentication and permission model;
- integration surface;
- maintenance activity and release recency;
- license evidence;
- operational complexity;
- likely migration or lock-in risk.

## Step 4: make a conditional recommendation

Explain:

- which project is the first choice for this specific scenario;
- which project is the fallback and under what changed conditions;
- hard conflicts that disqualify a project;
- unknowns requiring a proof of concept or manual verification;
- what facts would reverse the recommendation.

Do not declare a winner when a blocking requirement remains unknown. When live
tools are unavailable, recommend the verification sequence rather than a
project.

## Output structure

### Decision context

Summarize use case, hard constraints, criteria and assumptions.

### Comparison matrix

Use a compact table. Keep factual cells separate from commentary. Without live
tools, leave project-specific cells `unknown` and show the source needed to
resolve each cell.

### Key trade-offs

Explain only differences supported by evidence. If none are verified, describe
which differences must be investigated.

### Recommendation

Give a conditional first choice, fallback and reasons only when blocking facts
are verified. Otherwise provide a verification plan.

### Unknowns, risks and verification plan

Include evidence gaps, license caveats, compatibility tests and the smallest
proof-of-concept plan.

## Safety and quality rules

- Never execute or install project code during research.
- Never infer a license from repository popularity or package metadata alone.
- License observations are not legal advice.
- Never compare stale and current records as though they were simultaneous.
- Never penalize a project for a fact that is merely unknown.
- Never hide a hard conflict behind an aggregate score.
- Never claim a current comparison when the companion MCP tools are unavailable.
