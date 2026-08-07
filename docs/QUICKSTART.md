# Quickstart

This guide covers the three supported ways to use AI Workstation Open Source Intelligence today.

## 1. Skills-only: fastest setup

Use this when you want the research/comparison/stack-planning workflows without live Radar data.

```bash
git clone https://github.com/zxhwolfe-dev/aiworkstation-open-source-intelligence.git
cd aiworkstation-open-source-intelligence
codex plugin marketplace add "$PWD"
codex plugin marketplace list
```

Skills-only installs:

- `open-source-project-research`
- `open-source-project-comparison`
- `open-source-stack-planner`

**Important:** Skills-only mode does not provide direct access to the live AI Workstation project database. If live MCP tools are unavailable, the Skills must produce requirements, verification plans, and architecture guidance without inventing current project facts.

## 2. Local MCP: full current research capability

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

Configure your MCP host according to [`codex-setup.md`](codex-setup.md).

The MCP server exposes exactly six tools:

- `search_ai_projects`
- `get_project_facts`
- `get_license_evidence`
- `compare_ai_projects`
- `find_alternatives`
- `compose_ai_stack`

## 3. CLI: scripting and automation

```bash
osi-m0 provider-info
osi-m0 list-tools
osi-m0 invoke search_ai_projects \
  --arguments '{"query":"Find a self-hosted RAG project with Docker and a Web UI.","locale":"en"}'
```

Enable live Radar data by setting `OSI_PROVIDER=http` and `AIWORKSTATION_RADAR_BASE_URL` as shown above.

## Recommended first prompts

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

Do not treat every value in `data` as a verified fact. License observations are technical evidence, not legal advice.

## Safety

Do not submit passwords, API keys, private source code, customer records, or confidential documents. The tools are read-only and never install or execute third-party repository code.
