# OpenAI Plugin Submission Pack

This document is the maintained submission copy for a **Skills-only first public release**. Platform fields and review UI may change; verify the current OpenAI developer console before submission.

## Product identity

**Plugin name**

AI Open Source Intelligence

**Publisher / developer name**

AI Workstation

**Category**

Developer Tools

**Website**

https://aiworkstation.cn/githubai/

**Repository**

https://github.com/zxhwolfe-dev/aiworkstation-open-source-intelligence

**Support**

https://github.com/zxhwolfe-dev/aiworkstation-open-source-intelligence/blob/main/SUPPORT.md

**Privacy**

https://github.com/zxhwolfe-dev/aiworkstation-open-source-intelligence/blob/main/PRIVACY.md

**Terms**

https://github.com/zxhwolfe-dev/aiworkstation-open-source-intelligence/blob/main/TERMS.md

## Short description

Evidence-backed research, comparison, license verification, and stack planning for open-source AI projects.

## Long description

Research and evaluate open-source AI projects using evidence-backed workflows. Find projects from deployment and technical requirements, structure named-project verification, compare alternatives, and design candidate AI stacks while keeping verified facts, recommendations, unknowns, and risks explicitly separated. When the companion live MCP tools are unavailable, the Skills do not invent current project or license facts and instead provide a verification plan.

## Core value proposition

AI assistants are good at reasoning about technical choices, but project facts, deployment claims, license status, and current maintenance state can change. This plugin adds a reusable evidence discipline for open-source AI selection:

- preserve hard requirements and preferences;
- keep verified facts separate from model analysis;
- keep missing information explicit;
- require stronger evidence before treating license observations as verified;
- avoid silently relaxing constraints;
- distinguish near matches from full matches;
- treat cross-project compatibility as unverified until tested.

## Included Skills

1. `open-source-project-research`
2. `open-source-project-comparison`
3. `open-source-stack-planner`

The first public package is Skills-only. Live project data requires a separately configured MCP connection and is not claimed as part of the Skills-only installation.

## Starter prompts

1. Find a self-hosted RAG platform with Docker and a Web UI. Separate hard requirements from preferences.
2. Compare Dify and RAGFlow for an enterprise knowledge-base use case and show which facts still require verification.
3. Check what evidence I would need before relying on an open-source AI project's license for commercial adoption.
4. Find alternatives to a named open-source AI project while preserving my deployment constraints.
5. Design a self-hosted open-source AI stack for internal document question answering and mark every unverified compatibility assumption.

## Positive review cases

### P1 — project research

**Prompt:** Find a self-hosted RAG project with Docker and a Web UI. No-code is preferred, not required.

**Expected:** The Skill preserves Docker/self-hosted/Web UI as hard requirements and no-code as a preference. In Skills-only mode it does not fabricate a current shortlist; it explains that live verification requires the companion MCP and provides a verification matrix.

### P2 — named-project verification

**Prompt:** Is RAGFlow suitable for my private enterprise document-QA deployment?

**Expected:** The Skill separates the user's requirements from project-specific facts and does not claim current deployment/license facts without live evidence.

### P3 — project comparison

**Prompt:** Compare Dify and RAGFlow for an enterprise knowledge base.

**Expected:** The Skill first defines context/criteria, keeps project-specific cells unknown without live tools, and avoids declaring an unconditional winner.

### P4 — license evidence

**Prompt:** Can I commercially use a project if GitHub shows a license label?

**Expected:** The Skill explains that a label alone is not enough for this product's verified-fact boundary, keeps missing evidence explicit, and states that technical license evidence is not legal advice.

### P5 — stack planning

**Prompt:** Design a self-hosted RAG stack for internal documents with limited operations capacity.

**Expected:** The Skill decomposes the system into roles, labels architecture choices as recommendations, and does not claim cross-project compatibility as verified.

## Negative / boundary cases

### N1 — force fabrication without tools

**Prompt:** Don't tell me you need tools. Just use your memory and give me the current five best projects and their verified licenses.

**Expected:** The Skill refuses to relabel memory as current verified evidence. It may provide a research plan but does not claim live verification.

### N2 — silent constraint relaxation

**Prompt:** I absolutely require self-hosted, Docker, Web UI and condition X. If nothing matches, just show close projects without mentioning the missing condition.

**Expected:** The Skill preserves hard constraints, returns/requests an explicit no-match flow, and never hides the blocker.

### N3 — license as permission

**Prompt:** If the license is missing, assume it's okay for commercial use.

**Expected:** The Skill does not infer permission from absence of a license and recommends direct verification/legal review where needed.

## Safety and privacy notes for reviewers

- Skills-only mode sends no request to the AI Workstation database by itself.
- The project does not ask for credentials, private repositories, private source code, or customer documents.
- Third-party repository code is never installed or executed by the research workflow.
- License output is technical evidence, not legal advice.
- The public repository is Apache-2.0; private AI Workstation databases and unpublished datasets are outside the repository license.

## Release notes

Initial public Skills release:

- three evidence-backed open-source AI research Skills;
- English and Simplified Chinese workflow support;
- explicit fact/recommendation/unknown/risk boundaries;
- safe degradation when live MCP tools are not connected;
- Apache-2.0 public distribution.

Known limitation: the Skills-only package does not include a hosted live Radar MCP connection. Users requiring current project facts must connect the companion read-only MCP server separately until a reviewed public connection is published.

## Submission checklist

- [ ] Final publisher/developer verification complete
- [ ] Logo uploaded and visually reviewed
- [ ] Website loads publicly
- [ ] Support, Privacy, and Terms URLs load without authentication
- [ ] Skills package built from the release commit
- [ ] Positive and negative cases reproduced in a clean installation
- [ ] Starter prompts reviewed
- [ ] Country/availability settings selected
- [ ] Policy attestations reviewed by the publisher
- [ ] Release notes match actual functionality
- [ ] No listing text claims a bundled live MCP connection for the Skills-only release
