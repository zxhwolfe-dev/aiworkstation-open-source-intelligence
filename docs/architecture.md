# Architecture

## Product goal

Convert AI Open Source Radar capabilities into reusable Skills and read-only
tools for evidence-backed project research, comparison and technology-stack
planning.

The distributable product is intentionally narrower than AI Workstation. It does
not reproduce the full website, data-production pipeline, administration system
or user account layer.

## Current layered design

```text
User / ChatGPT desktop / Codex CLI / Codex IDE / MCP client
                            |
                            v
Skills: trigger rules, workflow, tool ordering, output policy
                            |
                            v
MCP Python SDK v2 stdio server: protocol and server instructions only
                            |
                            v
ToolRegistry: strict validation and unified result envelope
                            |
                            v
ProjectIntelligenceProvider protocol
                 /                              \
M0 deterministic mock              M1 hardened public HTTP provider
                                                     |
                                                     v
AI Workstation public project list, detail and selector endpoints
                                                     |
                                                     v
Current healthy validated Radar release
```

## Responsibilities

### Skills

Skills define when to run a workflow, what information to collect, which tools
to call, how to handle empty or conflicting evidence, and how to present the
answer. They do not contain live project data.

First Skills:

- `open-source-project-research`
- `open-source-project-comparison`
- `open-source-stack-planner`

### MCP server

`src/aiworkstation_osi/mcp_server.py` exposes exactly six read-only tools through
the MCP Python SDK v2 stdio transport.

It owns:

- MCP tool registration;
- typed MCP input schemas derived from Python signatures;
- server-wide workflow and safety instructions;
- conversion of stable product errors into model-readable tool failures.

It does not own project search, comparison, evidence, recommendation or provider
logic.

### Tool core

`src/aiworkstation_osi/` owns:

- stable tool names;
- strict input validation;
- error normalization;
- the provider boundary;
- the unified result envelope;
- deterministic mock behavior for tests.

It has no implicit network access. The HTTP provider is selected only when
`OSI_PROVIDER=http` is explicitly configured.

### Provider adapters

The provider protocol permits multiple read-only data sources without changing
Skills or MCP definitions.

#### Mock provider

- deterministic;
- offline;
- clearly marked `MOCK_DATA`;
- suitable only for development and protocol tests.

#### Public HTTP provider

- calls public AI Workstation Radar endpoints only;
- does not import private `akaiagents` modules;
- requires matching public snapshot identity;
- validates selector evidence state and near-match boundaries;
- converts missing or sentinel licenses to explicit unknowns;
- rejects malformed, oversized or mixed-generation responses.

### Probe and contract capture

`osi-probe` validates one live project, license boundary and constrained search
without writing data.

`osi-capture-contracts` records sanitized public response shapes for regression
fixtures. It removes queries, credentials and internal publication fields,
bounds strings and arrays, and stores only query fingerprints.

## Unified result contract

Every successful tool returns `osi.tool-result.v1` with these first-class
boundaries:

- `data`: tool-specific structured output;
- `verified_facts`: facts with confidence and evidence;
- `recommendations`: analysis with rationale and assumptions;
- `unknowns`: missing or unverified conditions;
- `risks`: explicit adoption, license, security or integration limits.

This structure prevents model analysis from being presented as source truth.

## First tool set

| Tool | Purpose | Writes |
| --- | --- | ---: |
| `search_ai_projects` | Find candidates from requirements and constraints. | No |
| `get_project_facts` | Get current facts for one stable project ID. | No |
| `get_license_evidence` | Get observed license evidence without legal conclusions. | No |
| `compare_ai_projects` | Compare two to five projects in one decision context. | No |
| `find_alternatives` | Find constrained alternatives to a project. | No |
| `compose_ai_stack` | Compose a candidate architecture from verified components. | No |

## Snapshot rule

Time-sensitive comparisons and hydrated search candidates must use one current
public snapshot. The system fails closed rather than combining incompatible
project generations.

A project-detail response may use the snapshot identity from its matching public
list result only when both records resolve to the same stable project identity.

## Evidence rule

A public endpoint response is not automatically a verified fact. The adapter
must additionally establish:

- stable project identity;
- current snapshot identity;
- an observed public source URL and time;
- adequate coverage for the stated confidence;
- no unknown license sentinel or conflicting evidence state.

Recommendations, compatibility claims and architecture choices remain separate
from verified facts even when every component fact is valid.

## Trust model

- user input is untrusted;
- repository and web content is untrusted data;
- provider output is untrusted until validated;
- third-party code is never executed;
- a missing license is unknown, not permission;
- project compatibility is unknown until verified or tested;
- near matches are not formal recommendations;
- raw production responses are sanitized before becoming fixtures.

## Current M1 Alpha scope

Included:

- three complete Skill workflows;
- six tool contracts and registry;
- deterministic mock provider;
- hardened public HTTP provider;
- local MCP stdio server;
- server-wide MCP instructions;
- input manifest and result schema;
- bilingual evaluation corpus;
- live contract probe;
- sanitized contract capture;
- Codex setup guidance;
- unit, provider and in-memory MCP tests;
- security, privacy and integration documentation.

Not included:

- hosted Streamable HTTP MCP service;
- OAuth, API keys, billing or quotas;
- collection, alert or team writes;
- repository installation or execution;
- public plugin submission;
- production SLA or compatibility guarantees.

## M1 validation gates

Before an external alpha is announced:

1. run the full local test suite after pulling `main`;
2. observe successful GitHub Actions runs for supported Python versions;
3. run English and Chinese production probes;
4. capture sanitized list, detail, selector-result and selector-no-match fixtures;
5. confirm public transparency, update-time and license-evidence field shapes;
6. adjust only the adapter where real public fields differ;
7. test the stdio server from Codex using the project-scoped configuration.

Any missing upstream field becomes a documented minimal additive request for
`akaiagents`; this repository does not modify that project's main branch.
