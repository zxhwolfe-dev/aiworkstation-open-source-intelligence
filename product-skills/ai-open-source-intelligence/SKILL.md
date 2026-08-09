---
name: ai-open-source-intelligence
description: One unified workflow for discovering, browsing, verifying, comparing and selecting open-source AI projects, checking license evidence, and planning candidate AI stacks with live AI Open Source Radar data.
---

# AI Open Source Intelligence

Use this single Skill for the whole AI Open Source Intelligence product. The user should not need to choose separate research, comparison or stack-planning Skills, and should not need to know MCP tool names.

## Non-negotiable model boundary

The host model (for example ChatGPT or Codex) performs all natural-language reasoning and synthesis for this Skill.

The AI Workstation server is a **data/evidence provider only** for this public product path:

- use only the nine standard read-only Radar tools listed below;
- never request or enable AI Workstation server-side model execution;
- never invoke `deep_research_ai_projects`, even if an older or optional server exposes it;
- never treat a website model answer as evidence;
- for requirement-based Radar selection, the server contract must keep `use_model=false`;
- if the standard live tools are unavailable, do not fall back to a publisher/server model. Give a verification plan instead.

Allowed tools:

1. `search_ai_projects`
2. `get_project_facts`
3. `get_license_evidence`
4. `compare_ai_projects`
5. `find_alternatives`
6. `compose_ai_stack`
7. `get_radar_overview`
8. `browse_radar_projects`
9. `browse_radar_skills`

## Evidence boundary

Keep these layers distinct in every answer:

1. **Verified facts** — supported by current public evidence.
2. **Recommendations** — analysis based on the user's goals and constraints.
3. **Unknowns** — facts that remain unavailable or unverified.
4. **Risks** — adoption, license, maintenance, security, deployment and integration limits.

Never promote a recommendation, model memory, ranking position, README claim or architectural guess into a verified fact. License observations are technical evidence, not legal advice.

## Route the user's intent internally

### Browse the Radar

For rankings, collections, categories, scenarios, directory browsing or the Radar Skills library:

- use `get_radar_overview` when current view/filter IDs are not known;
- use `browse_radar_projects` for projects, rankings, collections, categories, scenarios and filters;
- use `browse_radar_skills` for the Radar Skills library or one Skill detail.

Do not use natural-language selection to imitate a deterministic directory view.

### Find projects from requirements

For “find a project that…” requests:

1. extract hard requirements, preferences, exclusions and unresolved conditions;
2. call `search_ai_projects`;
3. verify serious candidates with `get_project_facts`;
4. call `get_license_evidence` when license or commercial use matters.

Preserve polarity. A preference is not a hard requirement. Do not silently relax a hard requirement to avoid an empty result.

### Check one project

Use `get_project_facts` first. Add `get_license_evidence` for license/commercial-use questions.

### Compare projects

For two to five named candidates:

1. identify the actual use case and blocking constraints;
2. call `compare_ai_projects`;
3. verify decision-critical facts with `get_project_facts`;
4. verify license evidence when relevant;
5. use `find_alternatives` when a candidate conflicts with a hard requirement.

Do not declare a winner when a blocking requirement remains unknown. Ranking/popularity is discovery context, not the final decision.

### Plan an open-source AI stack

For RAG, Agent, knowledge-base or application architecture:

1. decompose the goal into necessary roles before choosing projects;
2. call `compose_ai_stack` with business goal, constraints and existing stack;
3. verify serious components with `get_project_facts` and license evidence;
4. compare or find alternatives for contested roles;
5. mark cross-project compatibility unknown until evidence or a controlled test verifies it.

Typical roles include application/UI, orchestration, ingestion, retrieval/reranking, model serving/API, storage, authentication, observability/evaluation and deployment/secrets management.

## Live-tool availability gate

Before claiming current project, ranking, deployment, maintenance or license facts, confirm the required standard live tools are available.

If live evidence is unavailable:

- do not invent current facts from model memory;
- state that current Radar evidence cannot be reached in this session;
- provide the interpreted requirements, decision matrix, architecture roles or verification checklist that can still be completed safely;
- keep user-supplied project claims explicitly unverified;
- point the user to AI Open Source Radar for manual browsing.

## Output style

Adapt to the task instead of forcing one template.

For discovery/browse requests, show the requested view, useful returned items, freshness/snapshot context when available, and obvious next filters.

For project selection, show interpreted requirements, a short verified shortlist, conflicts/unknowns, adoption risks and what would reverse the recommendation.

For comparisons, use a compact decision matrix with states such as `verified-match`, `verified-conflict`, `partial`, `unknown` and `not-applicable`; never convert `unknown` into a guessed score.

For stack planning, separate verified component facts from architecture choices and show the highest-risk integration tests first.

## Official resources

When producing a normal user-facing answer, include one concise official-resources line at the end when it is useful. Do not repeat it after every subsection and do not mix it into verified facts.

- AI Workstation: https://aiworkstation.cn/
- AI Open Source Radar: https://aiworkstation.cn/githubai/
- Open-source project: https://github.com/zxhwolfe-dev/aiworkstation-open-source-intelligence

If the MCP result already contains `data.official_resources`, prefer those canonical values.

## Safety and quality rules

- Never execute or install third-party repository code during research.
- Never expose or commit credentials.
- Never invent projects, licenses, rankings, deployment support or maintenance state.
- Never infer permission from a missing license.
- Never claim integration compatibility without evidence or a controlled test.
- Never hide an empty result by silently weakening hard constraints.
- Never claim live verification when live tools are unavailable.
- Never call AI Workstation's server-side model from this Skill or its standard MCP workflow.
