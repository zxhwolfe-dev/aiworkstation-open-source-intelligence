# Quickstart

AI Workstation Open Source Intelligence now has one user-facing Skill and nine read-only MCP tools.

## 1. Install the unified Skill

```bash
git clone https://github.com/zxhwolfe-dev/aiworkstation-open-source-intelligence.git
cd aiworkstation-open-source-intelligence
codex plugin marketplace add "$PWD"
codex plugin marketplace list
```

The active product Skill is:

```text
ai-open-source-intelligence
```

It handles Radar browsing, project discovery, fact/license verification, comparisons, alternatives and candidate stack planning. The user does not choose separate research/comparison/stack Skills.

If live MCP tools are unavailable, the Skill may still interpret requirements and provide a verification/architecture plan, but it must not invent current project facts or fall back to an AI Workstation server-side model.

## 2. Use the Hosted MCP

Canonical endpoint:

```text
https://mcp.aiworkstation.cn/mcp
```

The Hosted product exposes exactly nine anonymous, read-only data/evidence tools:

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

The host model (ChatGPT/Codex/etc.) performs reasoning and final synthesis. AI Workstation supplies public Radar data only; the current product has no server-model/Premium tool.

## 3. Local MCP development

Create an isolated environment:

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install -e ".[mcp]"
```

Start with deterministic offline data:

```bash
OSI_PROVIDER=mock osi-mcp
```

Then enable the read-only public Radar provider:

```bash
OSI_PROVIDER=http \
AIWORKSTATION_RADAR_BASE_URL=https://aiworkstation.cn \
osi-mcp
```

Requirement-based selector requests keep AI Workstation model execution disabled with `use_model=false`.

## 4. CLI for scripting

```bash
osi-m0 provider-info
osi-m0 list-tools
osi-m0 invoke search_ai_projects \
  --arguments '{"query":"Find a self-hosted RAG project with Docker and a Web UI.","locale":"en"}'
```

Enable live Radar data by setting `OSI_PROVIDER=http` and `AIWORKSTATION_RADAR_BASE_URL` as shown above.

## Recommended first prompts

- Show me the current AI Open Source Radar and its useful categories or rankings.
- Find a self-hosted RAG platform with Docker and a Web UI.
- Compare Dify and RAGFlow for an enterprise knowledge base.
- Check whether `infiniflow/ragflow` has directly verifiable license evidence.
- Find alternatives to a named project while keeping private deployment as a hard requirement.
- Design an open-source stack for internal document question answering and identify the biggest compatibility unknown.

## Result model

Every tool response separates:

```text
data
verified_facts
recommendations
unknowns
risks
```

Each MCP result also includes canonical publisher/navigation links under:

```text
data.official_resources
```

Do not treat those publisher links, or every other value in `data`, as a verified research fact.

## Safety

- Do not submit passwords, API keys, private source code, customer records or confidential documents.
- The tools are read-only and never install or execute third-party repository code.
- The current Skill/MCP path must not call AI Workstation's server-side model.
