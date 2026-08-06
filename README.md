# AI Workstation Open Source Intelligence

A distribution layer for researching, verifying, comparing and composing
open-source AI projects with explicit evidence and uncertainty boundaries.

## Status

**M1 Alpha / pre-release.** The repository contains:

- three complete Skill workflows;
- a validated skills-only `.codex-plugin/plugin.json` package;
- a repo-scoped local plugin marketplace;
- six read-only project-intelligence tools;
- a transport-neutral Python core;
- a deterministic offline mock provider;
- a fail-closed HTTP provider for AI Workstation's public Radar API;
- an MCP Python SDK v2 stdio server with server-wide safety instructions;
- a live public-contract probe, sanitized fixture capture and offline fixture validator;
- machine-readable schemas, bilingual evaluations and automated tests;
- Codex CLI, plugin and project-scoped MCP configuration guidance.

This is not yet a hosted public MCP service or a universal-directory release.
The live HTTP provider is opt-in and must pass production contract validation
before an external release.

## Product boundaries

Every tool result separates:

1. verified source facts;
2. analysis and recommendations;
3. unknown or unverified information;
4. risks and limitations.

The first release is read-only. It does not execute repository code, mutate
GitHub projects, save collections, authenticate users or process payments.

## First Skills

- `open-source-project-research`
- `open-source-project-comparison`
- `open-source-stack-planner`

## First tools

- `search_ai_projects`
- `get_project_facts`
- `get_license_evidence`
- `compare_ai_projects`
- `find_alternatives`
- `compose_ai_stack`

## Repository layout

```text
.
├── .codex-plugin/plugin.json   installable skills-only plugin manifest
├── .agents/plugins/            repo-scoped local marketplace
├── skills/                     reusable Skill workflows
├── src/aiworkstation_osi/      core, providers, MCP, probe and capture tools
├── schemas/                    input manifest and unified result schema
├── evals/                      bilingual evaluation cases
├── tests/                      unit, package, provider and MCP tests
├── examples/                   local invocation and Codex config examples
├── docs/                       architecture, packaging and validation runbooks
├── AGENTS.md
├── SECURITY.md
└── PRIVACY.md
```

## Local setup

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install -e ".[mcp]"
python -m unittest discover -s tests -v
```

## Install the local Skills plugin

The repository root is a skills-only plugin package. Register its marketplace:

```bash
codex plugin marketplace add zxhwolfe-dev/aiworkstation-open-source-intelligence --ref main
codex plugin marketplace list
```

For a local clone:

```bash
codex plugin marketplace add /ABSOLUTE/PATH/TO/aiworkstation-open-source-intelligence
```

Restart the ChatGPT desktop app, open the Plugins Directory, choose
`AI Workstation Local Plugins`, and install `AI Open Source Intelligence`.

The plugin package currently installs the three Skills only. It deliberately
does not claim a bundled or registered MCP connection yet. Connect the local
stdio MCP server separately until a portable bundled command or registered
hosted MCP endpoint is ready.

See [`docs/plugin-packaging.md`](docs/plugin-packaging.md).

## Offline mock usage

The default provider performs no network access:

```bash
osi-m0 provider-info
osi-m0 list-tools
osi-m0 invoke search_ai_projects \
  --arguments '{"query":"self-hosted RAG with Docker and web UI"}'
```

The returned `MOCK_DATA` risk is intentional.

## Public Radar HTTP provider

Enable the public AI Workstation adapter explicitly:

```bash
export OSI_PROVIDER=http
export AIWORKSTATION_RADAR_BASE_URL=https://aiworkstation.cn
export OSI_HTTP_TIMEOUT_SECONDS=30
export OSI_HYDRATE_LIMIT=5

osi-m0 provider-info
osi-m0 invoke get_project_facts \
  --arguments '{"project_id":"infiniflow/ragflow","locale":"en"}'
```

The adapter:

- uses public read endpoints only;
- requires public snapshot identity for project facts;
- rejects mixed-snapshot comparisons;
- requires selector evidence status to be `available` or disclosed `partial`;
- keeps near matches outside formal recommendations;
- converts missing and sentinel license values to explicit unknowns;
- flags non-standard license labels for manual review;
- never imports private `akaiagents` modules.

## MCP server

Run a local stdio MCP server for Codex or another MCP host:

```bash
OSI_PROVIDER=mock osi-mcp
```

Use the public HTTP provider:

```bash
OSI_PROVIDER=http \
AIWORKSTATION_RADAR_BASE_URL=https://aiworkstation.cn \
osi-mcp
```

The server uses the MCP Python SDK v2 line and exposes only the six declared
read-only tools. Its server instructions lead with the fact/recommendation
boundary, prohibition on repository execution, license caveat and recommended
tool sequence. Tests connect in memory without opening a subprocess or port.

For Codex setup, see [`docs/codex-setup.md`](docs/codex-setup.md) and
[`examples/codex-config.toml`](examples/codex-config.toml).

## Validate the public contract

Run both language probes:

```bash
osi-probe --base-url https://aiworkstation.cn --locale en
osi-probe --base-url https://aiworkstation.cn --locale zh
```

Capture sanitized response shapes for review:

```bash
osi-capture-contracts \
  --base-url https://aiworkstation.cn \
  --locale en \
  --project-id infiniflow/ragflow \
  --output-dir tmp/public-validation/contracts-en

osi-validate-contracts \
  --directory tmp/public-validation/contracts-en
```

The capture stores four public response fixtures and a manifest. It removes
queries, credentials, client IDs and internal publication fields; bounds long
strings and lists; and records query fingerprints instead of query text. The
offline validator checks identity, snapshot, evidence, no-match and near-match
contracts before manual review.

Follow [`docs/production-validation.md`](docs/production-validation.md) before
inviting external testers.

## Architecture

```text
User / plugin or MCP host
     |
Three packaged Skills
     |
MCP Python SDK v2 stdio server
     |
Transport-neutral ToolRegistry
     |
Mock provider OR hardened AI Workstation HTTP provider
     |
Current healthy validated Radar release
```

`zxhwolfe-dev/akaiagents` remains a read-only reference and private data
production system. This repository integrates through explicit public HTTP
contracts rather than importing its private Python modules.

See:

- [`docs/architecture.md`](docs/architecture.md)
- [`docs/m1-alpha.md`](docs/m1-alpha.md)
- [`docs/plugin-packaging.md`](docs/plugin-packaging.md)
- [`docs/akaiagents-integration.md`](docs/akaiagents-integration.md)
- [`docs/codex-setup.md`](docs/codex-setup.md)
- [`docs/production-validation.md`](docs/production-validation.md)
- [`schemas/tool-manifest.json`](schemas/tool-manifest.json)
- [`schemas/tool-result.schema.json`](schemas/tool-result.schema.json)
- [`docs/security-and-privacy.md`](docs/security-and-privacy.md)
- [`docs/error-codes.md`](docs/error-codes.md)

## Remaining M1 validation

1. Pull `main` and run the complete local suite.
2. Observe successful GitHub Actions runs on Python 3.10 and 3.12.
3. Install and test the local Skills plugin through the repo marketplace.
4. Run English and Chinese production probes.
5. Capture, validate and manually review sanitized production fixtures.
6. Confirm exact transparency, observation-time and license-evidence fields.
7. Test the stdio server from Codex with the project-scoped configuration.
8. Add plugin MCP wiring only after a portable bundled server or registered
   hosted MCP connection exists.
9. Add Streamable HTTP only after host allowlists, authentication, rate limiting
   and deployment controls are designed.

## License

No open-source license has been granted yet. The repository is public for
pre-release inspection and development; reuse rights will be defined before the
first public package release.
