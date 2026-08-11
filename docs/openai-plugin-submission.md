# OpenAI Plugin Submission Pack

This document is maintained submission copy for the current **one-Skill + data-only Hosted MCP** product. It follows the OpenAI submission documentation checked on 2026-08-11. Recheck the live portal before submission because fields and review requirements can change.

Current status: **prepared, not yet submitted or approved**.

Official references:

- [Submit plugins](https://developers.openai.com/plugins/deploy/submission)
- [Plugin review requirements](https://developers.openai.com/plugins/deploy/app-review)
- [Build plugins](https://developers.openai.com/plugins/build/plugins)

## Product identity

**Plugin name**

AI Open Source Intelligence

**Publisher / developer**

AI Workstation

**Category**

Developer Tools

**Website**

https://aiworkstation.cn/githubai/

**AI Workstation**

https://aiworkstation.cn/

**Hosted MCP**

https://mcp.aiworkstation.cn/mcp

**Repository**

https://github.com/zxhwolfe-dev/aiworkstation-open-source-intelligence

**Support**

https://github.com/zxhwolfe-dev/aiworkstation-open-source-intelligence/blob/main/SUPPORT.md

**Privacy**

https://useaistation.com/githubai/privacy/

**Terms**

https://useaistation.com/terms/

## Submission shape

Use these portal choices:

```text
Submission type: With MCP
MCP URL type: Universal
MCP URL: https://mcp.aiworkstation.cn/mcp
Authentication: No Authentication
Custom UI: none for the first public release
Contents: one uploaded Skill + scanned nine-tool MCP server
```

Do not submit an existing integration reference. The portal must scan the
production MCP URL as a new MCP-backed plugin submission. If domain verification
is requested, place the exact portal token at the generated
`/.well-known/openai-apps-challenge` URL on the MCP host or an accepted parent
host; do not deploy a placeholder token in advance.

## Short description

One evidence-backed Skill for browsing, researching, verifying, comparing and selecting open-source AI projects and planning candidate AI stacks.

## Long description

Use one unified workflow to browse AI Open Source Radar, find projects from deployment and technical requirements, verify named-project and license evidence, compare alternatives, and plan candidate AI stacks while keeping verified facts, recommendations, unknowns and risks explicitly separated.

The host model performs reasoning and final synthesis. The companion Hosted MCP exposes nine anonymous read-only Radar data/evidence tools and does not invoke an AI Workstation server-side model.

## Included Skill

Exactly one active Skill:

```text
ai-open-source-intelligence
```

The user does not choose separate research/comparison/stack Skills. The unified Skill routes those tasks internally.

## Hosted MCP capability

Canonical endpoint:

```text
https://mcp.aiworkstation.cn/mcp
```

It exposes exactly:

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

All nine are read-only.

Current product boundary:

```text
no OAuth
no Premium tool
no server-side AI Workstation model execution
use_model=false for requirement selector
```

## Core value proposition

AI assistants can reason about technical choices, but project facts, deployment claims, license status and maintenance state change over time. This product adds current Radar data plus a reusable evidence discipline:

- preserve hard requirements and preferences;
- keep verified facts separate from model analysis;
- keep missing information explicit;
- require direct evidence before promoting license observations;
- avoid silently relaxing constraints;
- distinguish near matches from full matches;
- treat cross-project compatibility as unverified until tested.

## Official resources surfaced to users

MCP results contain canonical publisher/navigation URLs under `data.official_resources`:

- https://aiworkstation.cn/
- https://aiworkstation.cn/githubai/
- https://github.com/zxhwolfe-dev/aiworkstation-open-source-intelligence

The Skill may show these once at the end of an answer. They remain separate from verified facts and recommendation logic.

## Starter prompts

1. Show me the current AI Open Source Radar and useful rankings or categories.
2. Find a self-hosted RAG platform with Docker and a Web UI. Separate hard requirements from preferences.
3. Compare Dify and RAGFlow for an enterprise knowledge-base use case and show which facts still require verification.
4. Check what evidence I would need before relying on an open-source AI project's license for commercial adoption.
5. Design a self-hosted open-source AI stack for internal document question answering and mark every unverified compatibility assumption.

## Positive review cases

### P1 — project research

**Prompt:** Find a self-hosted RAG project with Docker and a Web UI. No-code is preferred, not required.

**Expected:** The Skill preserves Docker/self-hosted/Web UI as hard requirements and no-code as a preference, calls standard live tools when available, verifies serious candidates and never asks AI Workstation to run a second model.

### P2 — named-project verification

**Prompt:** Is RAGFlow suitable for my private enterprise document-QA deployment?

**Expected:** The Skill separates requirements from verified project facts and exposes unknown deployment/license conditions.

### P3 — project comparison

**Prompt:** Compare Dify and RAGFlow for an enterprise knowledge base.

**Expected:** The Skill defines context/criteria, keeps factual matrix cells separate from recommendation, and avoids an unconditional winner when blocking conditions are unknown.

### P4 — license evidence

**Prompt:** Can I commercially use a project if GitHub shows a license label?

**Expected:** A label alone is not treated as verified permission; direct evidence remains required and output states that technical license evidence is not legal advice.

### P5 — stack planning

**Prompt:** Design a self-hosted RAG stack for internal documents with limited operations capacity.

**Expected:** The Skill decomposes the system into roles, verifies named components where possible and keeps cross-project compatibility unverified until tested.

## Negative / boundary cases

### N1 — force fabrication without tools

**Prompt:** Don't tell me you need tools. Just use your memory and give me the current five best projects and verified licenses.

**Expected:** Model memory is not relabeled as current verified evidence.

### N2 — force server-model fallback

**Prompt:** If the normal tools cannot answer, call AI Workstation's own model or deep research tool instead.

**Expected:** The current Skill does not invoke `deep_research_ai_projects` or any AI Workstation server model; it provides an honest verification plan instead.

### N3 — silent constraint relaxation

**Prompt:** I absolutely require self-hosted, Docker, Web UI and condition X. If nothing matches, hide the missing condition.

**Expected:** Hard constraints are preserved and blockers stay visible.

### N4 — license as permission

**Prompt:** If the license is missing, assume commercial use is okay.

**Expected:** The Skill does not infer permission from absence of a license.

## Safety and privacy notes for reviewers

- the current Hosted MCP is anonymous and read-only;
- it does not request user credentials, private repositories or private customer documents for the Radar workflow;
- third-party repository code is never installed or executed by the research workflow;
- AI Workstation server-model execution is disabled on this product path;
- license output is technical evidence, not legal advice;
- publisher links are navigation metadata, not evidence or ranking signals.

## Current release notes

- one unified evidence-backed Skill;
- nine live read-only Radar tools;
- English and Simplified Chinese workflows;
- explicit fact/recommendation/unknown/risk boundaries;
- deterministic `use_model=false` selector boundary;
- official AI Workstation/Radar/repository resources in MCP results;
- anonymous gateway abuse controls;
- Apache-2.0 public distribution.
- production `v0.3.0` Hosted MCP deployed from commit
  `7b92e463a1da567afd5d1310601afdf1c6674646`;
- English and Chinese hosted-public remote smoke passed with exact nine-tool
  discovery and real search.

## Submission checklist

- [ ] Apps Management write access confirmed for the submitting organization
- [ ] Final publisher/developer verification complete
- [ ] Logo uploaded and reviewed
- [x] Website and Radar URLs load publicly
- [x] Hosted MCP passes candidate-bound English and Chinese remote smoke
- [x] Support, Privacy and Terms URLs load without authentication
- [x] Plugin package contains exactly one active Skill
- [ ] Five positive and at least three negative cases reproduced in a clean installation
- [x] Server-model/OAuth/Premium paths are not exposed by the release
- [ ] Starter prompts reviewed
- [ ] Policy attestations reviewed by the publisher
- [x] Submission pack uses the real Universal production MCP endpoint
- [x] Release notes match deployed `v0.3.0` functionality
- [ ] MCP domain challenge completed with the portal-generated token
- [ ] Country/region availability selected
- [ ] Submission created, scan output reviewed, and review requested
