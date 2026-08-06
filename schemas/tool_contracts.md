# MCP Tool Contracts v0.1

This document describes the six M1 Alpha tools. The machine-readable source of
truth is [`tool-manifest.json`](tool-manifest.json); all successful tools return
[`tool-result.schema.json`](tool-result.schema.json).

## Shared guarantees

All tools are:

- read-only;
- non-destructive;
- idempotent with respect to caller-visible writes;
- open-world reads because public project data can change;
- bounded by strict input sizes and output contracts;
- prohibited from executing or installing third-party repository code.

Every successful response separates:

```text
data
verified_facts
recommendations
unknowns
risks
generated_at
request_id
schema_version
```

A value in `data` is not automatically a verified fact. Only entries in
`verified_facts` carry the fact/evidence contract.

## Shared inputs

### `locale`

Accepted values:

```text
en
zh
```

Default: `en`.

### `request_id`

Optional caller-provided correlation ID, maximum 128 characters. It is not
silently truncated.

### Structured objects

`constraints` and `context` accept JSON-compatible objects only. Runtime limits:

| Limit | Value |
| --- | ---: |
| Maximum nesting depth | 6 |
| Maximum total nodes | 200 |
| Maximum entries/items per object or array | 50 |
| Maximum object-key length | 128 |
| Maximum nested string length | 1,000 |

Non-finite numbers, sets, custom objects, binary values, control characters in
keys and oversized structures are rejected with `INVALID_INPUT`.

### `source_mode`

Accepted search hints:

```text
required
preferred
off
```

M1 Alpha remains fail-closed in every mode. `source_mode=off` is not permission
to invent or relabel facts, and it does not disable project, license, snapshot or
unknown-state protections. The current public provider may return the same
verified result in all three modes; future releases can introduce differentiated
retrieval behavior only without weakening the result boundary.

## `search_ai_projects`

Find candidate projects from a task and explicit constraints.

### Input

```json
{
  "query": "Find a self-hosted RAG project with Docker and a Web UI.",
  "constraints": {
    "self_hosted": "required",
    "docker": "required",
    "web_ui": "required",
    "no_code": "preferred"
  },
  "locale": "en",
  "source_mode": "required",
  "request_id": "example-search"
}
```

### Contract

- Query length: 1–4,000 characters.
- Hard-condition polarity must be preserved.
- Formal projects and near matches cannot coexist.
- Near matches are separate and have exactly one `conflict` or `unverified`
  blocker.
- A verified empty result includes an explicit `no_match_reason`.
- Live candidates are hydrated from public project details and must share a
  compatible public snapshot.

### Typical `data`

```text
projects
total
result_kind
evidence_status
notice
no_match_reason
near_matches
snapshot_id
selector_url
observed_at
```

## `get_project_facts`

Return current public facts for one stable project identity.

### Input

```json
{
  "project_id": "infiniflow/ragflow",
  "locale": "en",
  "request_id": "example-facts"
}
```

### Contract

- `project_id` length: 1–256 characters.
- Project aliases are resolved through the public list before detail lookup.
- Project-list snapshot identity is required.
- Detail and list snapshot identities must match when both are present.
- Missing project, deployment, update time or license evidence remains explicit.
- Archived projects carry `PROJECT_ARCHIVED` risk.

### Typical `data`

```text
project
found
snapshot_id
coverage_level
transparency
source_url
observed_at
```

## `get_license_evidence`

Return the observed public license value and supporting fact evidence.

### Input

```json
{
  "project_id": "infiniflow/ragflow",
  "locale": "en"
}
```

### Contract

- License output is technical evidence, not legal advice.
- Empty values and sentinels such as `NOASSERTION`, `UNKNOWN` and `UNLICENSED`
  become an explicit unknown and `LICENSE_UNVERIFIED` risk.
- Non-standard labels such as `OTHER`, `CUSTOM` or `PROPRIETARY` remain
  observations but carry `NON_STANDARD_LICENSE` risk.
- Absence of a license is never permission to use, modify or redistribute.

### Typical `data`

```text
project_id
license
found
snapshot_id
source_url
observed_at
```

## `compare_ai_projects`

Compare two to five named projects against explicit criteria.

### Input

```json
{
  "project_ids": ["langgenius/dify", "infiniflow/ragflow"],
  "criteria": ["private deployment", "document processing", "license"],
  "context": {
    "organization_size": 100,
    "deployment": "self-hosted"
  },
  "locale": "en"
}
```

### Contract

- Two to five unique project IDs.
- Up to 12 unique criteria; each string is limited to 256 characters.
- All found project details must share one compatible snapshot.
- Missing fields remain unknown rather than receiving guessed scores.
- The matrix is tool data; final selection remains a recommendation.

### Typical `data`

```text
projects
criteria
comparison_matrix
snapshot_id
```

## `find_alternatives`

Find alternatives while preserving explicit constraints.

### Input

```json
{
  "project_id": "langgenius/dify",
  "constraints": {
    "self_hosted": "required",
    "lighter_weight": "preferred"
  },
  "locale": "en"
}
```

### Contract

- The named source project is resolved to its stable identity.
- The source project is excluded even when the caller used an alias.
- Formal alternatives are hydrated and verified like search candidates.
- Near matches remain separate and disclose their blocker.
- No-match reasons remain explicit.

### Typical `data`

```text
source_project_id
alternatives
total
no_match_reason
near_matches
snapshot_id
```

## `compose_ai_stack`

Compose a candidate architecture from a business goal and verified components.

### Input

```json
{
  "business_goal": "Build an internal document question-answering service.",
  "constraints": {
    "self_hosted": "required",
    "docker": "required",
    "budget": "limited"
  },
  "existing_stack": ["PostgreSQL", "Kubernetes"],
  "locale": "en"
}
```

### Contract

- Business-goal length: 1–4,000 characters.
- Up to 20 unique existing-stack strings; each is limited to 256 characters.
- Individual component facts can be verified.
- Architecture, component roles and cross-project compatibility are
  recommendations until a controlled integration test verifies them.
- Results carry `INTEGRATION_NOT_VERIFIED` risk.

### Typical `data`

```text
business_goal
components
solution
solution_blueprint
project_roles
gaps
snapshot_id
```

## Errors and empty states

Stable errors:

```text
INVALID_INPUT
UNKNOWN_TOOL
PROVIDER_UNAVAILABLE
UPSTREAM_CONTRACT_ERROR
```

The following are successful empty/unknown states, not provider exceptions:

- a project is absent from the current public snapshot;
- no project satisfies all hard constraints;
- license evidence is missing or ambiguous;
- compatibility is not verified;
- a required public fact is unavailable.

Tools must never replace these states with fabricated projects or inferred
permission.
