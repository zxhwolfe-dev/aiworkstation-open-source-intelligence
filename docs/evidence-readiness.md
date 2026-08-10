# Evidence readiness

Readiness is evidence-first and candidate-bound. Every CI, live-contract,
deterministic-eval, Codex/Host acceptance, package review and Hosted report must
belong to the same exact Git commit.

Generate ordinary evidence from a clean checkout. Live contract capture is
sanitized and replayed offline; it must never contain queries, request IDs,
credentials, cookies, internal publication fields, or private source text.

For Hosted validation run:

```bash
osi-remote-smoke \
  --profile hosted-public \
  --url https://mcp.example.com/mcp \
  --invoke-search \
  --output hosted-remote.json
```

The report must prove the exact deployment SHA, anonymous access, nine tools,
read-only annotations, `osi.tool-result.v2`, a real search, and declared gateway
protection. No OAuth issuer, Premium tool, payment, or bearer token is part of
the current evidence chain.

`osi-hosted-evidence-readiness` combines this remote report with CI, live
validation, Codex acceptance and artifact review. Missing or stale evidence
fails closed; it is not equivalent to a product defect by itself.
