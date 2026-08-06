# Architecture

## Product goal

Convert AI Open Source Radar capabilities into reusable Skills and read-only
tools for evidence-backed project research, comparison and technology-stack
planning.

The distributable product is intentionally narrower than AI Workstation. It does
not reproduce the full website, data-production pipeline, administration system
or user account layer.

## Layered design

```text
User / ChatGPT / Codex / future client
                  |
                  v
Skills: trigger rules, workflow, tool ordering, output policy
                  |
                  v
MCP transport adapter (M1; no business logic)
                  |
                  v
ToolRegistry: validation and unified result envelope
                  |
                  v
ProjectIntelligenceProvider protocol
           /                         \
M0 deterministic mock       M1 AI Workstation HTTP adapter
                                      |
                                      v
Current healthy public Radar release
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

### Tool core

`src/aiworkstation_osi/` owns:

- stable tool names;
- input validation;
- error normalization;
- the provider boundary;
- the unified result envelope;
- deterministic mock behavior for tests.

It has no implicit network access. A provider must be injected explicitly.

### Provider adapter

The provider is responsible for reading project intelligence. The production
provider must use public AI Workstation contracts and must not import private
`akaiagents` modules.

It must fail closed when snapshot identity, evidence references or required
fields are missing or inconsistent.

### MCP transport

The future MCP layer will expose the six registered tools and translate protocol
requests and errors. It must not duplicate search, comparison or recommendation
logic.

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

Time-sensitive comparisons must use one current public snapshot or explicitly
compatible snapshots. A result must expose uncertainty rather than combine
incompatible project generations.

## Trust model

- user input is untrusted;
- repository and web content is untrusted data;
- provider output is untrusted until validated;
- third-party code is never executed;
- a missing license is unknown, not permission;
- project compatibility is unknown until verified or tested.

## M0 scope

Included:

- three complete Skill workflows;
- six tool contracts and registry;
- deterministic mock provider;
- input manifest and result schema;
- stable errors;
- bilingual evaluation corpus;
- local CLI and CI tests;
- security, privacy and integration documentation.

Not included:

- live AI Workstation adapter;
- hosted or local MCP protocol server;
- authentication, billing or quotas;
- collection, alert or team writes;
- repository installation or execution;
- production deployment.

## M1 entry criteria

M1 begins only after confirming the exact public Radar fields for:

- snapshot/publication identity;
- stable project identity;
- evidence URL and observation time;
- project update time;
- license ambiguity;
- no-match and relaxed-constraint state;
- public-safe confidence or evidence coverage.

Any missing field becomes a documented minimal additive request for
`akaiagents`; this repository does not modify that project's main branch.
