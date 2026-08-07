# Error Codes

All transports must expose the same `osi.error.v1` envelope. HTTP status codes,
MCP errors and CLI exit codes are adapters around this contract, not separate
business semantics.

```json
{
  "schema_version": "osi.error.v1",
  "error": {
    "code": "INVALID_INPUT",
    "message": "query is required",
    "retryable": false,
    "details": {"field": "query"}
  }
}
```

## M0 codes

| Code | Meaning | Retryable | Caller action |
| --- | --- | ---: | --- |
| `INVALID_INPUT` | Required fields, types, lengths or cardinalities are invalid. | No | Correct the request. |
| `UNKNOWN_TOOL` | The requested tool is not in the six-tool M0 manifest. | No | Use a declared tool name. |
| `PROVIDER_UNAVAILABLE` | The injected project-intelligence provider failed or timed out. | Yes | Retry with backoff; do not invent results. |
| `UPSTREAM_CONTRACT_ERROR` | The provider returned data that does not satisfy the adapter contract. | No | Quarantine the response and investigate the adapter. |

## Non-error empty states

The following conditions are successful tool results with explicit `unknowns`,
not exceptions:

- a project is absent from the current healthy public snapshot;
- no candidate satisfies every hard constraint;
- license evidence is unavailable or ambiguous;
- a compatibility claim has not been verified;
- source data is stale but still within an explicitly allowed serving window.

Empty states must never be replaced with guessed facts or fabricated projects.
