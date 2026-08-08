---
name: open-source-project-comparison
description: Compare two to five open-source AI projects for a specific use case using current Radar facts, license evidence, deployment constraints, rankings/context and explicit trade-offs. Use for project-versus-project decisions and alternative selection.
---

# Open Source Project Comparison

Use this Skill when the user names two to five open-source AI projects or asks which project is better for a defined scenario.

A project is never “best” without context. Identify the use case and blocking constraints before presenting a winner.

## Comparison boundary

Keep four layers separate:

- **verified facts** from current evidence;
- **comparison calculations** derived from those facts;
- **recommendations** conditioned on the user's priorities;
- **unknowns and risks** that could change the decision.

Popularity, ranking position and model preference are not substitutes for decision-critical facts.

## Route the request

### User names the projects

Use `compare_ai_projects`, then verify decision-critical fields with `get_project_facts`. Use `get_license_evidence` for each candidate when license matters.

### User asks “what should I compare in this category/collection/ranking?”

Use `get_radar_overview` when the current view ID is unknown, then `browse_radar_projects` to form a transparent candidate set before comparison.

Do not treat ranking order as the final recommendation. Rankings are discovery context; the decision still depends on the user's scenario and verified constraints.

### User asks for alternatives

Use `find_alternatives`; verify serious alternatives before putting them in the decision matrix.

### Explicit deeper comparison

When the hosted product exposes `deep_research_ai_projects`, use `focus=comparison` only when the user explicitly asks for deeper publisher-model synthesis after the standard evidence/data pass.

Premium analysis remains a recommendation. Do not promote its narrative into verified facts.

## Live-tool availability gate

Before presenting a current comparison or winner, confirm the required companion tools are available.

If live evidence tools are unavailable:

1. do not fill the matrix with remembered project facts;
2. state that current Radar evidence is unavailable;
3. provide the decision context, criteria, weights, blank verification matrix, verification plan and proof-of-concept plan;
4. mark project-specific cells `unknown` unless the user supplied a source, and keep user-supplied claims unverified;
5. do not recommend a winner solely from general model memory.

## Define the decision

Collect or infer:

- two to five stable project identities;
- intended use case/users;
- hard requirements;
- evaluation criteria/priorities;
- deployment, privacy and data-residency needs;
- available engineering/operations skill;
- budget;
- license/commercial-use requirements;
- horizon: prototype, production or procurement.

If no criteria are supplied, use a neutral baseline and label it as an assumption: function fit, deployment, maturity, maintenance, license, extensibility, operational complexity and evidence coverage.

## Collect comparable facts

Call `compare_ai_projects` with two to five unique project IDs and explicit criteria. Verify important fields with `get_project_facts` and licenses with `get_license_evidence`.

Compared current records must share compatible snapshot identity. If that cannot be established, expose a high-visibility uncertainty before comparing time-sensitive fields.

## Build the matrix

For each criterion use one of:

- `verified-match`;
- `verified-conflict`;
- `partial`;
- `unknown`;
- `not-applicable`.

Do not fill an unknown with a guessed score.

Useful criteria include:

- primary product fit;
- self-hosting/offline operation;
- Docker/deployment path;
- Web UI/coding level;
- document/RAG/Agent capability;
- authentication/permission model;
- integration surface;
- maintenance/release recency;
- license evidence;
- operational complexity;
- migration/lock-in risk.

## Recommendation

Explain:

- first choice for this exact scenario;
- fallback and the conditions that favor it;
- verified hard conflicts;
- unknowns that require proof-of-concept/manual verification;
- what facts would reverse the recommendation.

Do not declare a winner when a blocking requirement remains unknown.

## Safety and quality rules

- Never execute or install project code during research.
- Never infer a license from popularity/package metadata.
- License observations are not legal advice.
- Never compare incompatible snapshots as simultaneous facts.
- Never penalize a project merely because a field is unknown.
- Never hide a hard conflict behind an aggregate score.
- Never claim a current comparison when required live tools are unavailable.
- Never treat a Radar ranking as the same thing as scenario-specific selection.
- Never invoke Premium AI without an explicit deeper-analysis request.
