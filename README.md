# AI Workstation Open Source Intelligence

A distribution layer for researching, verifying, comparing and composing
open-source AI projects with explicit evidence and uncertainty boundaries.

## Status

**M1 Alpha / pre-release.** The repository contains:

- three complete Skill workflows;
- a validated Skills-only Codex plugin package and repo-scoped marketplace;
- six read-only project-intelligence tools;
- a transport-neutral Python core;
- a deterministic offline mock provider;
- a fail-closed HTTP provider for AI Workstation's public Radar API;
- an MCP Python SDK v2 stdio server with server-wide safety instructions;
- live public-contract probes, sanitized capture, validation and offline replay;
- a deterministic Skills-only alpha ZIP builder with SHA-256 checksums;
- automated unit, plugin, MCP, workflow and packaging tests.

This is not yet a hosted public MCP service or a public-directory release. The
live HTTP provider is opt-in and must pass production contract validation before
an external release.

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
├── .codex-plugin/               Skills-only plugin manifest
├── .agents/plugins/             repo-scoped marketplace manifest
├── .github/workflows/           CI, live validation and alpha packaging
├── skills/                      reusable Skill workflows
├── src/aiworkstation_osi/       core, providers, MCP and validation tools
├── schemas/                     input manifest and unified result schema
├── evals/                       bilingual tool and workflow cases
├── tests/                       unit, provider, workflow and MCP tests
├── examples/                    invocation and Codex configuration examples
├── docs/                        architecture, setup and release runbooks
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
osi-validate-plugin --root .
```

## Install the local Skills plugin

Register the repository marketplace:

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

The plugin currently installs the three Skills only. It deliberately does not
claim a bundled or registered MCP connection. Connect the local stdio server
separately until a portable bundled command or hosted MCP endpoint is ready.

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
- rejects leaked internal selector fields and unsafe contract shapes;
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

The server exposes exactly six read-only tools. Its instructions lead with the
fact/recommendation boundary, prohibition on repository execution, license
caveat and recommended tool sequence. Tests connect in memory without opening a
subprocess or network port.

For Codex setup, see [`docs/codex-setup.md`](docs/codex-setup.md) and
[`examples/codex-config.toml`](examples/codex-config.toml).

## Validate the public contract

Run both language probes:

```bash
osi-probe --base-url https://aiworkstation.cn --locale en
osi-probe --base-url https://aiworkstation.cn --locale zh
```

Capture, validate and replay sanitized response shapes:

```bash
osi-capture-contracts \
  --base-url https://aiworkstation.cn \
  --locale en \
  --project-id infiniflow/ragflow \
  --output-dir tmp/public-validation/contracts-en

osi-validate-contracts --directory tmp/public-validation/contracts-en
osi-replay-contracts \
  --directory tmp/public-validation/contracts-en \
  --project-id infiniflow/ragflow \
  --locale en
```

The capture removes query text, credentials, client IDs and internal publication
fields; bounds strings and lists; and records fingerprints instead of prompts.

A manually triggered workflow performs the complete bilingual validation chain
and uploads an artifact only after validation, replay and sanitization succeed:

```text
.github/workflows/live-contract-validation.yml
```

See [`docs/live-validation-workflow.md`](docs/live-validation-workflow.md) and
[`docs/production-validation.md`](docs/production-validation.md).

## Build the Skills-only alpha package

Create a deterministic ZIP for invited Skills-only testers:

```bash
osi-build-alpha --root . --output-dir dist/alpha
(
  cd dist/alpha
  sha256sum --check SHA256SUMS
)
```

The archive contains the plugin manifests, three Skills, public documentation
and an embedded file manifest with individual SHA-256 hashes. It deliberately
excludes Python source, tests, CI workflows, `pyproject.toml` and the live MCP
server, so it does not imply live Radar access.

The manually triggered packaging workflow runs all release gates before
uploading the archive:

```text
.github/workflows/alpha-package.yml
```

See [`docs/alpha-tester-guide.md`](docs/alpha-tester-guide.md) and
[`docs/external-alpha-checklist.md`](docs/external-alpha-checklist.md).

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

## Main documentation

- [`docs/architecture.md`](docs/architecture.md)
- [`docs/m1-alpha.md`](docs/m1-alpha.md)
- [`docs/plugin-packaging.md`](docs/plugin-packaging.md)
- [`docs/akaiagents-integration.md`](docs/akaiagents-integration.md)
- [`docs/codex-setup.md`](docs/codex-setup.md)
- [`docs/live-validation-workflow.md`](docs/live-validation-workflow.md)
- [`docs/production-validation.md`](docs/production-validation.md)
- [`docs/alpha-tester-guide.md`](docs/alpha-tester-guide.md)
- [`docs/external-alpha-checklist.md`](docs/external-alpha-checklist.md)
- [`schemas/tool-manifest.json`](schemas/tool-manifest.json)
- [`schemas/tool-result.schema.json`](schemas/tool-result.schema.json)
- [`docs/security-and-privacy.md`](docs/security-and-privacy.md)
- [`docs/error-codes.md`](docs/error-codes.md)

## Remaining M1 validation

1. Observe successful standard CI runs on Python 3.10 and 3.12.
2. Run the manual live validation workflow against the intended production
   origin and review its English and Chinese artifacts.
3. Install and test the Skills plugin through the repo marketplace.
4. Test the stdio server from Codex using the project-scoped configuration.
5. Close any public-contract differences found in production responses.
6. Select a software license, public legal pages and support contact before a
   broad public launch.
7. Add hosted Streamable HTTP only after authentication, host validation, rate
   limiting, abuse controls and deployment policy are designed.

## License

No open-source license has been granted yet. The repository is public for
pre-release inspection and development; reuse rights will be defined before the
first public package release.
