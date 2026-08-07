# AI Open Source Intelligence

**Evidence-backed research, comparison, license verification, and stack planning for open-source AI projects.**

[简体中文](README.zh-CN.md) · [Quickstart](docs/QUICKSTART.md) · [FAQ](docs/FAQ.md) · [Website](https://aiworkstation.cn/githubai/)

> 3 Skills · 6 read-only MCP tools · English & Chinese · Apache-2.0

AI Open Source Intelligence is AI Workstation's research and technology-selection layer for the open-source AI ecosystem. It helps developers, technical leaders, and AI builders discover, verify, compare, and compose open-source projects while keeping **verified facts, recommendations, unknowns, and risks** explicitly separated.

## What can it do?

- **Find projects** from deployment, privacy, budget, and technical constraints.
- **Verify a project** using current public project/detail evidence.
- **Check license evidence** without treating a label or missing license as permission.
- **Compare projects** in one explicit decision context.
- **Find alternatives** without silently relaxing hard requirements.
- **Compose a candidate stack** while keeping cross-project compatibility unverified until tested.

## Why not just ask a general AI model?

General models are excellent at reasoning, but open-source project metadata, deployment claims, maintenance state, and license information change over time. This project adds a maintained evidence contract and a disciplined selection workflow.

### Verified facts are not the same as analysis

Every tool result separates:

```text
data
verified_facts
recommendations
unknowns
risks
```

A value appearing in `data` does not automatically become a verified fact.

### Field-level evidence states

The live provider distinguishes:

```text
verified_public_metadata
verified_direct_evidence
public_projection_only
unknown
```

### License verification is deliberately strict

A visible license label alone is not enough to enter `verified_facts`. Missing, indirect, or ambiguous license evidence remains unknown and can raise `LICENSE_UNVERIFIED`. License output is technical evidence, not legal advice.

### Hard requirements stay hard

When nothing satisfies every required constraint, the correct result is an explicit no-match. Near matches remain separate and disclose their blocker.

### Comparisons preserve snapshot consistency

Time-sensitive project records are not compared as though they were simultaneous when their public snapshot identities are incompatible.

## Three Skills

### `open-source-project-research`

Discover or verify open-source AI projects from a user's task, deployment, privacy, budget, license, and engineering constraints.

### `open-source-project-comparison`

Compare two to five projects for a concrete use case while separating current evidence, trade-offs, unknowns, and conditions that could reverse the recommendation.

### `open-source-stack-planner`

Decompose a system into roles, then design a candidate open-source AI stack. Individual project facts can be verified; cross-project compatibility remains a recommendation until tested.

## Six read-only MCP tools

| Tool | Purpose |
| --- | --- |
| `search_ai_projects` | Find projects from a task and constraints |
| `get_project_facts` | Fetch current public project facts and evidence state |
| `get_license_evidence` | Inspect direct public license evidence |
| `compare_ai_projects` | Compare 2–5 named projects |
| `find_alternatives` | Find alternatives while preserving constraints |
| `compose_ai_stack` | Compose a candidate open-source AI stack |

All current product tools are read-only. They do not modify GitHub and do not install or execute third-party repository code.

## Use it in three ways

### A. Skills-only — fastest setup

```bash
codex plugin marketplace add zxhwolfe-dev/aiworkstation-open-source-intelligence --ref main
codex plugin marketplace list
```

**Skills-only does not directly connect to the live AI Workstation project database.**

Without live MCP tools, the Skills can still structure requirements, preserve hard/preferred constraints, create verification matrices, and design vendor-neutral architectures. They must not claim current project or license facts from model memory alone.

### B. Local MCP — current full research capability

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install -e ".[mcp]"
```

Start offline:

```bash
OSI_PROVIDER=mock osi-mcp
```

Enable the public read-only Radar provider:

```bash
OSI_PROVIDER=http \
AIWORKSTATION_RADAR_BASE_URL=https://aiworkstation.cn \
osi-mcp
```

See [`docs/codex-setup.md`](docs/codex-setup.md).

### C. CLI — scripting and automation

```bash
osi-m0 provider-info
osi-m0 list-tools
osi-m0 invoke search_ai_projects \
  --arguments '{"query":"Find a self-hosted RAG project with Docker and a Web UI.","locale":"en"}'
```

## Does search call another AI Workstation model?

For the current M1 live provider, selector requests are sent with `use_model=false`. The normal six-tool research path therefore does not require an additional AI Workstation-funded LLM call for search/retrieval.

ChatGPT, Codex, or another MCP host model still interprets the user request, decides which Skills/tools to use, and synthesizes the final answer. The AI Workstation MCP/data layer provides structured retrieval and evidence.

See [`docs/MODEL-AND-DATA-FLOW.md`](docs/MODEL-AND-DATA-FLOW.md).

## Does MCP expose the whole AI Workstation website?

No. MCP exposes only capabilities explicitly implemented as tools. The current six tools cover the core Open Source Intelligence / Open Source Radar research workflow; they do not expose every AI Workstation product, UI page, account feature, private database operation, maintenance task, or internal API.

New online capabilities should be added through explicit, reviewed tool contracts rather than by treating the website backend as an unrestricted API surface.

## Quickstart

See [`docs/QUICKSTART.md`](docs/QUICKSTART.md).

## FAQ

See [`docs/FAQ.md`](docs/FAQ.md).

## Development

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install -e ".[mcp]"
python -m compileall -q src tests
python -m unittest discover -s tests -v
osi-validate-plugin --root .
```

CI covers Python 3.10 and 3.12.

## Repository layout

```text
.codex-plugin/               Skills-only plugin manifest
.agents/plugins/             repo-scoped marketplace manifest
.github/workflows/           CI, validation, packaging, and publishing workflows
skills/                      reusable Skill workflows
src/aiworkstation_osi/       core, providers, MCP, and validation tools
schemas/                     tool and result contracts
evals/                       bilingual evaluation cases
tests/                       automated tests
docs/                        architecture, setup, deployment, and release docs
```

## Distribution and release

- Skills-only plugin package for ChatGPT/Codex-style plugin distribution
- local stdio MCP for Codex and other MCP hosts
- CLI for scripting
- guarded Streamable HTTP MCP for local/private-alpha deployment
- PyPI and GHCR publishing workflows prepared for versioned public releases

The guarded HTTP transport is **not yet approved as an unrestricted public multi-user MCP service**. Broad hosted release still requires final identity/authentication, revocation, quotas, rate limiting, abuse controls, monitoring, and service-specific operational/legal decisions.

See [`ROADMAP.md`](ROADMAP.md), [`docs/plugin-packaging.md`](docs/plugin-packaging.md), and [`docs/public-launch-decisions.md`](docs/public-launch-decisions.md).

## OpenAI submission preparation

The maintained Skills-only listing copy, starter prompts, five positive cases, three negative/boundary cases, privacy notes, and release checklist are in [`docs/openai-plugin-submission.md`](docs/openai-plugin-submission.md).

## Security and privacy

- [Security policy](SECURITY.md)
- [Privacy statement](PRIVACY.md)
- [Terms](TERMS.md)
- [Support](SUPPORT.md)

Do not submit passwords, API keys, private source code, customer records, or confidential documents.

## Contributing

See [`CONTRIBUTING.md`](CONTRIBUTING.md) and [`CODE_OF_CONDUCT.md`](CODE_OF_CONDUCT.md). Use the structured issue templates for bugs, evidence problems, public-contract regressions, project requests, and feature proposals.

## License

This public repository is licensed under the [Apache License 2.0](LICENSE).

**Scope note:** Apache-2.0 covers this public repository. It does not automatically license AI Workstation's private databases, unpublished datasets, private backend systems, hosted infrastructure, or trademarks.
