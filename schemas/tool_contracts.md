# AI Open Source Intelligence Tool Contracts

Machine-readable sources:

- [`tool-manifest.json`](tool-manifest.json) — nine standard read-only tools;
- [`hosted-tool-manifest.json`](hosted-tool-manifest.json) — hosted OAuth product plus Premium AI.

## Shared result boundary

Standard successful tool results separate:

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

A value in `data` is **not automatically a verified fact**.

The hardened live provider uses field states such as:

```text
verified_public_metadata
verified_direct_evidence
public_projection_only
unknown
```

License is stricter: a project-level label becomes a verified license only when direct public `License` evidence and a public excerpt are available. Missing/indirect/sentinel license values remain unknown and must never be treated as permission.

## Standard tool guarantees

The nine standard tools are:

- read-only with respect to caller-visible product state;
- non-destructive;
- idempotent with respect to writes;
- open-world reads because public project data can change;
- prohibited from executing/installing third-party repository code;
- bounded by explicit input contracts.

Hosted mode may rate-limit standard tools by authenticated OAuth identity. Standard tools do not consume Premium AI credits.

## Shared inputs

### `locale`

```text
en
zh
```

Default: `en`.

### `request_id`

Optional correlation ID, max 128 chars. Runtime telemetry never logs the raw request ID.

### Structured objects

Nested `constraints`, `context` and similar objects are JSON-compatible and bounded. The standard runtime limits include depth, node count, container size, key length and string length. Non-finite numbers/custom objects/binary/control-character keys are rejected.

## 1. `search_ai_projects`

Requirement-based project discovery.

Typical input:

```json
{
  "query": "Find a self-hosted RAG project with Docker and a Web UI.",
  "constraints": {
    "self_hosted": "required",
    "docker": "required",
    "web_ui": "required"
  },
  "locale": "en",
  "source_mode": "required"
}
```

Key rules:

- preserve hard/preferred/negative polarity;
- formal results and near matches stay separate;
- verified empty result has explicit no-match reason;
- live candidates share compatible snapshot identity;
- hydrated facts inherit project evidence rules.

Use this for requirements. Do not use it merely to reproduce a deterministic ranking/category/collection view.

## 2. `get_project_facts`

Get current public project data plus the subset that qualifies as verified facts.

Key rules:

- stable project identity;
- required snapshot identity;
- same-snapshot checks;
- repository/public metadata separated from editorial projection values;
- unknown required fields stay unknown;
- archived projects carry risk.

## 3. `get_license_evidence`

Get direct public license evidence.

Key rules:

- technical evidence, not legal advice;
- project-level label alone is insufficient;
- verified license requires direct public `License` evidence/excerpt;
- `NOASSERTION`, `UNKNOWN`, `UNLICENSED`, empty or indirect values remain unknown;
- non-standard labels carry manual-review risk;
- absence is never permission.

## 4. `compare_ai_projects`

Compare two to five projects in one explicit decision context.

Key rules:

- 2–5 unique projects;
- up to 12 unique criteria;
- compatible snapshot identity;
- unknown values do not receive guessed scores;
- final selection is recommendation, not verified fact.

## 5. `find_alternatives`

Find alternatives while preserving explicit constraints.

Key rules:

- source project is excluded after stable identity resolution;
- formal alternatives and near matches remain separate;
- no-match reasons remain explicit;
- alternatives inherit evidence/snapshot rules.

## 6. `compose_ai_stack`

Compose a candidate architecture from business goal/constraints/current project evidence.

Key rules:

- individual component facts can be verified;
- architecture/component-role/compatibility claims remain recommendations until separately tested;
- results carry integration-not-verified risk.

## 7. `get_radar_overview`

Discover the current navigation vocabulary of AI Open Source Radar.

Input:

```json
{
  "locale": "en"
}
```

Typical data includes current public dimensions such as:

```text
rankings
collections
categories
scenarios
resource types / topics / other navigation metadata
snapshot or publication context when exposed by the public contract
```

Use this when the user asks “what rankings/collections/categories are available?” or when a browse ID should be discovered rather than guessed.

The tool is not a static enum: Radar navigation may evolve with the public release.

## 8. `browse_radar_projects`

Browse/search the live Radar project directory.

Supported public inputs include:

```text
query
ranking
collection
category
scenario
role
topic
github_topic
radar_topic
use_case
resource_type
license
deployment
layer
limit
offset
locale
```

Runtime bounds:

- text query max 1,000 chars;
- filter strings max 256 chars;
- limit 1–50;
- offset 0–10,000.

Key rules:

- current project browse requires snapshot identity;
- filters are passed only through the explicit public allowlist;
- internal publication fields fail closed;
- pagination state is explicit;
- ranking/collection/category position is public browse context, not a scenario-specific recommendation.

## 9. `browse_radar_skills`

Browse/search/filter the Radar Skills library or open one Skill detail.

List inputs:

```text
query
category
kind
license
installable
sort
limit
offset
locale
```

Detail input:

```text
skill_id
locale
```

`skill_id` cannot be silently mixed with list filters. Missing Skill detail returns an explicit not-found/unknown state rather than an invented Skill.

## Hosted-only: `deep_research_ai_projects`

This tool is available only in the authenticated hosted product.

Input:

```json
{
  "query": "Compare the strongest self-hosted RAG choices for an enterprise knowledge base.",
  "focus": "comparison",
  "filters": {
    "deployment": "docker"
  },
  "locale": "en"
}
```

`focus`:

```text
research
comparison
stack
market_scan
```

### Important behavior

This tool is **not** declared read-only/idempotent because successful execution consumes a one-time Premium AI trial or AI credit.

It remains non-destructive with respect to third-party repositories/user content.

Flow:

1. authenticate OAuth user;
2. apply Premium application rate limit;
3. run rules-first Radar selection with publisher model disabled;
4. whitelist/bound public Radar context;
5. reserve free trial or AI credit;
6. run AI Workstation publisher model;
7. success keeps the reservation consumed;
8. model failure refunds the reservation;
9. return model narrative under recommendations, not verified facts.

When no trial/credit remains, the hosted tool returns an explicit upgrade state. For an unsubscribed user it may include an unpaid HTTPS checkout URL. It does not automatically complete a purchase.

## Hosted identity

The hosted MCP validates standard OAuth access and transforms verified `(issuer, subject)` into an opaque entitlement ID. Raw access tokens and raw OAuth subject values do not enter public tool results or payment custom data.

## Standard errors and states

Stable base errors include:

```text
INVALID_INPUT
UNKNOWN_TOOL
PROVIDER_UNAVAILABLE
UPSTREAM_CONTRACT_ERROR
```

Hosted layers additionally use states/errors such as:

```text
AUTH_REQUIRED
RATE_LIMITED
UPGRADE_REQUIRED
BACKEND_UNAVAILABLE
```

No-match, missing project, missing license, unknown compatibility and exhausted Premium entitlement are explicit states; they must not be replaced with fabricated data.
