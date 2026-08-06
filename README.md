# AI Workstation Open Source Intelligence

A distribution layer for researching, verifying, comparing and composing
open-source AI projects with explicit evidence and uncertainty boundaries.

## Status

**M0 foundation / pre-alpha.** The repository now contains three Skill
workflows, six transport-neutral read-only tool contracts, a deterministic mock
provider, machine-readable schemas, bilingual evaluation cases and automated
tests.

It does **not** yet expose a hosted MCP endpoint or connect to live AI
Workstation data. Mock output is always marked and must not be used for real
technology-selection or license decisions.

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
├── src/aiworkstation_osi/      transport-neutral Python core
├── schemas/                    input manifest and unified result schema
├── evals/                      bilingual evaluation cases
├── tests/                      standard-library unit tests
├── docs/                       architecture, integration and safety contracts
├── AGENTS.md                   repository development rules
├── SECURITY.md
└── PRIVACY.md
```

## Local setup

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install -e .
python -m unittest discover -s tests -v
```

List the M0 tools:

```bash
osi-m0 list-tools
```

Invoke a deterministic local example:

```bash
osi-m0 invoke search_ai_projects \
  --arguments '{"query":"self-hosted RAG with Docker and web UI"}'
```

The returned `MOCK_DATA` risk is intentional.

## Architecture

```text
User / Agent
     |
Skills: repeatable task workflow
     |
MCP transport adapter (M1)
     |
Transport-neutral tool registry (M0)
     |
AI Workstation public Radar adapter (M1)
     |
Current healthy validated Radar release
```

`zxhwolfe-dev/akaiagents` remains a read-only reference and private data
production system. This repository must integrate through explicit public
contracts rather than importing its private Python modules.

See:

- [`docs/architecture.md`](docs/architecture.md)
- [`docs/akaiagents-integration.md`](docs/akaiagents-integration.md)
- [`schemas/tool-manifest.json`](schemas/tool-manifest.json)
- [`schemas/tool-result.schema.json`](schemas/tool-result.schema.json)
- [`docs/security-and-privacy.md`](docs/security-and-privacy.md)
- [`docs/error-codes.md`](docs/error-codes.md)

## Next milestone: M1 Alpha

1. Confirm the exact live public Radar response fields and snapshot identity.
2. Implement a fail-closed HTTP provider over the existing public endpoints.
3. Populate verified facts only from matching evidence and timestamps.
4. Add the real MCP transport and protocol-level tests.
5. Expand the evaluation corpus before publishing an anonymous demo.

## License

No open-source license has been granted yet. The repository is public for
pre-alpha inspection and development; reuse rights will be defined before the
first public package release.
