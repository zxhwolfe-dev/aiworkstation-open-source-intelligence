# AI Workstation Open Source Intelligence

A distribution layer for researching, verifying, comparing and composing
open-source AI projects with explicit evidence and uncertainty boundaries.

## Status

**M1 Alpha / pre-release.** The repository now contains:

- three complete Skill workflows;
- a validated Skills-only Codex plugin package and repo-scoped marketplace;
- six read-only project-intelligence tools;
- a transport-neutral Python core;
- a deterministic offline mock provider;
- a fail-closed HTTP provider for AI Workstation's public Radar API;
- strict field-level evidence boundaries for repository metadata, analysis
  projection fields and direct license evidence;
- stdio and guarded Streamable HTTP MCP transports;
- privacy-minimized structured tool telemetry;
- live public-contract probes, sanitized capture, validation and offline replay;
- a deterministic Skills-only alpha ZIP builder with SHA-256 checksums;
- a consolidated four-level release-readiness report;
- a non-root container and localhost-only hosted-alpha compose example;
- remote MCP compatibility smoke tests;
- automated unit, plugin, MCP, workflow, packaging and deployment-policy tests.

This is **not yet a broad public hosted MCP service or public-directory
release**. The hosted transport is ready for local/private-alpha deployment
behind a trusted private network or authenticated TLS gateway. Native public
OAuth, production quotas/rate limiting/abuse controls, legal publication gates
and platform registration remain deliberately unresolved.

## Product boundaries

Every tool result separates:

1. verified source facts;
2. analysis and recommendations;
3. unknown or unverified information;
4. risks and limitations.

A value being present in `data.project` does not automatically make it a verified
fact. The live hardened provider distinguishes:

```text
verified_public_metadata
verified_direct_evidence
public_projection_only
unknown
```

Stable repository/public-release metadata can cross the fact boundary after
same-snapshot validation. Summary, deployment classification, categories and use
cases remain `public_projection_only` unless a future field-specific evidence
contract verifies them. License is stricter: a license label is verified only
when public transparency includes a direct `License` source and excerpt.

The first release is read-only. It does not execute repository code, mutate
GitHub projects, save collections, authenticate end users or process payments.

## Skills

- `open-source-project-research`
- `open-source-project-comparison`
- `open-source-stack-planner`

## Tools

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
├── docs/                        architecture, deployment and release runbooks
├── Dockerfile
├── compose.hosted.example.yml
├── CHANGELOG.md
├── SECURITY.md
├── PRIVACY.md
└── SUPPORT.md
```

## Local setup

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install -e ".[mcp]"
python -m unittest discover -s tests -v
osi-validate-plugin --root .
osi-readiness --root .
```

Before real operational evidence exists, the expected readiness state is:

```text
code_ready=true
external_alpha_ready=false
hosted_private_alpha_ready=false
public_launch_ready=false
```

`code_ready=true` is a target of the repository checks; do not claim it has been
observed until the current local/CI suite actually runs green.

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

The plugin package installs the three Skills only. It deliberately does not yet
claim a bundled or registered live MCP connection. Configure the stdio MCP
server separately until the hosted connection identity and authorization model
are stable.

See [`docs/plugin-packaging.md`](docs/plugin-packaging.md).

## Offline mock usage

The default provider performs no network access:

```bash
osi-m0 provider-info
osi-m0 list-tools
osi-m0 invoke search_ai_projects \
  --arguments '{"query":"self-hosted RAG with Docker and web UI"}'
```

`MOCK_DATA` warnings are intentional and prevent fixture output from being
mistaken for current verified project intelligence.

## Public Radar HTTP provider

Enable the live read-only adapter explicitly:

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

- requires public snapshot identity;
- rejects mixed snapshots and unsafe selector contracts;
- rejects upstream redirects instead of silently following them;
- keeps near matches outside formal recommendations;
- exposes `field_evidence_status` for project-detail fields;
- requires direct public `License` evidence before a license enters
  `verified_facts`;
- converts missing/indirect/sentinel licenses into explicit unknowns;
- flags non-standard license labels for manual review;
- never imports private `akaiagents` modules.

## stdio MCP server

Run a local MCP server for Codex or another stdio-capable host:

```bash
OSI_PROVIDER=mock osi-mcp
```

Use live Radar data:

```bash
OSI_PROVIDER=http \
AIWORKSTATION_RADAR_BASE_URL=https://aiworkstation.cn \
osi-mcp
```

The server exposes exactly six annotated read-only tools and preserves the
fact/recommendation/unknown/risk boundary.

Runtime telemetry defaults to warnings/errors on **stderr** so stdio protocol
output is not polluted. Set `OSI_LOG_LEVEL=INFO` to record successful tool name,
outcome, duration and safe aggregate counts. Tool arguments, queries, project IDs
and raw request IDs are not logged; request IDs are reduced to a short SHA-256
fingerprint.

See [`docs/codex-setup.md`](docs/codex-setup.md).

## Guarded Streamable HTTP MCP

Validate the default local configuration without opening a socket:

```bash
osi-mcp-http --check-config
```

Run a loopback-only development endpoint:

```bash
OSI_PROVIDER=mock osi-mcp-http
```

The endpoint is:

```text
http://127.0.0.1:8000/mcp
```

Verify it with a real MCP client:

```bash
osi-remote-smoke --url http://127.0.0.1:8000/mcp --invoke-search --locale en
```

A non-loopback bind requires all of the following:

```text
OSI_PROVIDER=http
OSI_MCP_HTTP_PUBLIC_BIND_ACK=reverse-proxy-or-private-network
AIWORKSTATION_RADAR_BASE_URL=https://aiworkstation.cn
OSI_MCP_HTTP_ALLOWED_HOSTS=mcp.example.com,mcp.example.com:*
```

The server also caps MCP request bodies at 256 KiB by default. Browser clients
must additionally use explicit HTTPS `OSI_MCP_HTTP_ALLOWED_ORIGINS` plus matching
narrow CORS policy.

The Host/origin allowlists are passed into MCP transport security for
DNS-rebinding/Host-header protection. The public-bind acknowledgement is **not
authentication**. Do not expose the endpoint directly to the Internet without a
trusted authenticated TLS gateway or future native OAuth.

Container/private-alpha example:

```bash
docker build -t aiworkstation-osi-mcp:0.1.0 .
docker compose -f compose.hosted.example.yml up --build
```

The example maps only `127.0.0.1:8000` on the host, runs non-root, uses a
read-only filesystem and drops Linux capabilities. See
[`docs/hosted-mcp.md`](docs/hosted-mcp.md).

## Validate the public Radar contract

Run both language probes:

```bash
osi-probe --base-url https://aiworkstation.cn --locale en
osi-probe --base-url https://aiworkstation.cn --locale zh
```

Capture, validate and replay one language:

```bash
osi-capture-contracts \
  --base-url https://aiworkstation.cn \
  --locale en \
  --project-id infiniflow/ragflow \
  --output-dir tmp/public-validation/contracts-en

osi-validate-contracts \
  --directory tmp/public-validation/contracts-en

osi-replay-contracts \
  --directory tmp/public-validation/contracts-en \
  --output tmp/public-validation/replay-en.json
```

Replay derives locale and project identity from the sanitized capture manifest.
The probe requires a reported license either to have direct verified evidence or
to remain an explicit unknown. The manual `live-contract-validation` workflow
runs the bilingual chain and uploads artifacts only after validation, replay and
forbidden-key scanning pass.

See [`docs/production-validation.md`](docs/production-validation.md).

## Build the Skills-only alpha package

```bash
osi-build-alpha --root . --output-dir dist/alpha
(
  cd dist/alpha
  sha256sum --check SHA256SUMS
)
```

The archive contains the plugin manifests, three Skills, changelog, security,
privacy, support and tester documentation plus an embedded per-file SHA-256
manifest. It excludes Python runtime code and the live MCP server so the package
does not imply live-data access by itself.

The manual `.github/workflows/alpha-package.yml` workflow runs release gates
before uploading the archive.

## Readiness levels

`osi-readiness` distinguishes:

```text
code_ready
external_alpha_ready
hosted_private_alpha_ready
public_launch_ready
```

For a Skills-only invited alpha, supply real bilingual contract captures plus
CI, Codex and review evidence. For a hosted private alpha, additionally supply a
credential-free HTTPS `/mcp` endpoint, successful remote smoke-test attestation
and protected gateway/private-network attestation.

See [`docs/release-readiness.md`](docs/release-readiness.md).

## Architecture

```text
User / plugin / MCP host
          |
Three Skills
          |
  +-------+----------------+
  |                        |
stdio MCP             Streamable HTTP MCP
  |                 (guarded private alpha)
  +-----------+------------+
              |
       ToolRegistry
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
- [`docs/release-readiness.md`](docs/release-readiness.md)
- [`docs/hosted-mcp.md`](docs/hosted-mcp.md)
- [`docs/public-launch-decisions.md`](docs/public-launch-decisions.md)
- [`docs/alpha-tester-guide.md`](docs/alpha-tester-guide.md)
- [`docs/external-alpha-checklist.md`](docs/external-alpha-checklist.md)
- [`schemas/tool-manifest.json`](schemas/tool-manifest.json)
- [`schemas/tool-result.schema.json`](schemas/tool-result.schema.json)
- [`schemas/tool_contracts.md`](schemas/tool_contracts.md)
- [`docs/security-and-privacy.md`](docs/security-and-privacy.md)
- [`docs/error-codes.md`](docs/error-codes.md)

## What still requires real-world execution or publisher decisions

Code-side M1 Alpha is now substantially complete. Remaining gates are:

1. observe successful local tests and GitHub Actions on Python 3.10/3.12;
2. run and review bilingual production contract validation against the real
   Radar responses;
3. install the Skills package and test stdio MCP from Codex;
4. deploy the guarded HTTP service behind a protected gateway/private network;
5. run English and Chinese `osi-remote-smoke` against the deployed endpoint;
6. generate real external/hosted-alpha readiness reports;
7. fix only production contract/runtime differences demonstrated by those runs;
8. choose software license and publish final legal/support URLs;
9. implement the chosen per-user OAuth/identity, revocation, quota, rate-limit
   and abuse-control model before broad public hosting;
10. register and review the final hosted MCP/plugin connection with the target
    distribution platform.

The decisions that cannot safely be invented in code are documented in
[`docs/public-launch-decisions.md`](docs/public-launch-decisions.md).

## License

No open-source license has been granted yet. The repository is public for
pre-release inspection and development; reuse rights will be defined before the
first broad public package release.
