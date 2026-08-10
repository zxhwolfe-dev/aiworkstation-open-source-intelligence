# OSI 0.3 Tool Contracts

Machine-readable contracts are authoritative:

- `tool-manifest.json`: nine public tool names and input schemas;
- `hosted-tool-manifest.json`: anonymous data-only Hosted surface;
- `tool-result.schema.json`: `osi.tool-result.v2` output envelope.

## Inputs

All tools reject undeclared fields. Discovery, alternatives and stack planning
use typed constraints:

```json
[{"id":"deployment","value":"self-hosted","polarity":"required"}]
```

`polarity` is `required`, `preferred`, or `excluded`. Unknown/unresolved
conditions belong in result `unknowns`; they are not a polarity. `source_mode`
was removed in 0.3 because it did not change provider behavior.

## Successful results

Every tool returns `osi.tool-result.v2` with `data`, `verified_facts`,
`recommendations`, `unknowns`, `risks`, `execution`, `generated_at`, and
`request_id`. A value in `data` is not automatically a verified fact.

`execution.business_data_write` is always false. Search, alternatives and stack
planning may disclose `selector_task_create_or_cancel` as an ephemeral
control-plane effect; no user or third-party business data is modified.

## Errors

Every transport uses `osi.error.v2`:

```json
{"schema_version":"osi.error.v2","error":{"code":"INVALID_INPUT","message":"...","retryable":false,"details":{}}}
```

Transient capacity exhaustion uses `PROVIDER_OVERLOADED`, is retryable, and
HTTP transports return 503 with `Retry-After`. Internal exceptions and secrets
must not be exposed.

## Evidence boundary

Verified facts require current public evidence or validated repository metadata.
Editorial summaries, deployment claims, and compatibility remain analysis or
unknown unless directly supported. License results are technical evidence, not
legal advice. Tools never execute third-party repository code.
