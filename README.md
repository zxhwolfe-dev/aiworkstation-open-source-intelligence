# AI Workstation Open Source Intelligence

A distribution layer for researching, verifying, comparing and composing
open-source AI projects with explicit evidence and uncertainty boundaries.

## Status

**M1 Alpha / pre-release.** The repository contains:

- three complete Skill workflows;
- six read-only project-intelligence tools;
- a transport-neutral Python core;
- a deterministic offline mock provider;
- a fail-closed HTTP provider for AI Workstation's public Radar API;
- an MCP Python SDK v2 stdio server;
- machine-readable schemas, bilingual evaluations and automated tests.

This is not yet a hosted public MCP service. The live HTTP provider is opt-in and
still requires validation against representative production responses before a
public release.

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
├── skills/                     reusable Skill workflows
├── src/aiworkstation_osi/      core, HTTP provider and MCP server
├── schemas/                    input manifest and unified result schema
├── evals/                      bilingual evaluation cases
├── tests/                      unit, provider and in-memory MCP tests
├── examples/                   local invocation examples
├── docs/                       architecture, integration and safety contracts
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
- never infers a missing license;
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

The server is built with the current stable MCP Python SDK v2 line and exposes
only the six declared read-only tools. Tests connect to the server in memory,
without opening a subprocess or network port.

## Architecture

```text
User / MCP host
     |
Skills: repeatable task workflow
     |
MCP Python SDK v2 stdio transport
     |
Transport-neutral ToolRegistry
     |
Mock provider OR fail-closed AI Workstation HTTP provider
     |
Current healthy validated Radar release
```

`zxhwolfe-dev/akaiagents` remains a read-only reference and private data
production system. This repository integrates through explicit public HTTP
contracts rather than importing its private Python modules.

See:

- [`docs/architecture.md`](docs/architecture.md)
- [`docs/akaiagents-integration.md`](docs/akaiagents-integration.md)
- [`schemas/tool-manifest.json`](schemas/tool-manifest.json)
- [`schemas/tool-result.schema.json`](schemas/tool-result.schema.json)
- [`docs/security-and-privacy.md`](docs/security-and-privacy.md)
- [`docs/error-codes.md`](docs/error-codes.md)
- [`docs/m0-acceptance.md`](docs/m0-acceptance.md)

## Remaining M1 work

1. Validate the HTTP adapter against representative production responses.
2. Confirm exact transparency, observation-time and license-evidence fields.
3. Add recorded contract fixtures from the public API.
4. Add Streamable HTTP deployment only after host allowlists, authentication and
   rate limiting are designed.
5. Expand the evaluation corpus before publishing an anonymous demo.

## License

No open-source license has been granted yet. The repository is public for
pre-release inspection and development; reuse rights will be defined before the
first public package release.
