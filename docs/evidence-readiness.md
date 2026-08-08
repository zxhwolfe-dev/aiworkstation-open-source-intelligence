# Evidence-first release readiness

This is the preferred release-evidence path for the Skills-only External Alpha and the Hosted Private Alpha. It replaces manual claims about CI, live validation, Codex testing, remote MCP testing, and gateway protection with candidate-bound machine evidence wherever those facts are machine-verifiable. Human artifact review remains intentionally human.

## External Alpha evidence inputs

All machine artifacts must belong to the same Git commit as the local candidate checkout.

### 1. Standard CI evidence

The `ci` workflow runs the full repository suite on Python 3.10 and 3.12. Only after every matrix job succeeds does the `publish-ci-evidence` job upload:

```text
ci-evidence-<run-id>/ci-evidence.json
```

The manifest records the repository, candidate commit, run ID, exact Python matrix, and successful 3.10/3.12 gates. A stale artifact from an older commit is rejected.

### 2. Live contract-validation evidence

Run the `live-contract-validation` workflow against the intended public AI Workstation origin. It performs both English and Chinese probes, sanitized contract capture, validation, hardened replay, and forbidden-key scanning.

Only after those stages succeed does its artifact include:

```text
validation-evidence.json
```

The manifest binds the workflow run to the repository commit and public origin, points to the EN/ZH contract directories, and records SHA-256 for every protected file in the downloaded validation bundle. `osi-evidence-readiness` verifies those hashes before using the contracts.

### 3. Real Codex MCP acceptance evidence

From a clean checkout of the same candidate commit:

```bash
source .venv/bin/activate
osi-codex-acceptance \
  --root . \
  --provider http \
  --base-url https://aiworkstation.cn \
  --output tmp/codex-acceptance/live.json
```

The command starts `codex exec` non-interactively with an ephemeral session, read-only shell sandbox, no command-approval prompts, and a temporary required MCP server exposing the nine standard OSI tools. It does not rewrite the user's persistent Codex MCP configuration.

The acceptance result is not based on the model saying it used the tools. The MCP server writes a privacy-safe JSONL ledger containing only tool name, outcome, duration, level, timestamp, and error code. The report stores the ledger SHA-256. Readiness reopens the ledger, verifies the digest, recalculates the nine-tool success set, and checks that the report commit matches the current candidate.

## Human review

The live-validation artifact is deliberately sanitized, but a human still must review it before External Alpha. The reviewer should confirm at least:

- both probe reports passed;
- both contract manifests identify the intended locale and project;
- replay reports passed;
- no secrets, raw prompts, internal evidence IDs, source hashes, publication versions, or private data are present;
- unknown license evidence remains unknown instead of being inferred;
- the artifact corresponds to the intended candidate and public origin.

Record the reviewer's name only after that review is complete. Do not use a model or CI job to self-attest this gate.

## Final External Alpha readiness command

After downloading the CI and live-validation artifacts and completing the real Codex acceptance run:

```bash
osi-evidence-readiness \
  --root . \
  --ci-evidence /ABS/PATH/ci-evidence.json \
  --live-validation-evidence /ABS/PATH/validation-evidence.json \
  --codex-acceptance-report /ABS/PATH/codex-acceptance/live.json \
  --artifact-reviewed \
  --reviewer "REVIEWER NAME" \
  --expected-base-url https://aiworkstation.cn \
  --require-external-alpha \
  --output tmp/external-alpha-readiness.json
```

When live workflow evidence is supplied, the command derives the EN/ZH contract directories and workflow run ID from that manifest. When CI evidence is supplied, it derives the Python 3.10 and 3.12 gates from the manifest. Invalid supplied machine evidence fails closed and cannot be overridden by legacy manual boolean flags in the same invocation.

## Hosted Private Alpha evidence

Hosted Private Alpha adds one machine artifact to the already-complete External Alpha chain: a candidate-bound, OAuth-authenticated remote MCP report.

Generate it from the exact Hosted candidate checkout after DNS/TLS/gateway/WorkOS are configured:

```bash
osi-remote-smoke \
  --root . \
  --url https://mcp.aiworkstation.cn/mcp \
  --profile hosted \
  --auth-mode oauth \
  --expected-oauth-issuer https://<authkit-domain> \
  --locale en \
  --output tmp/hosted-remote.json
```

The hosted profile is intentionally stricter than the ordinary remote smoke. It must prove:

1. the endpoint is credential-free HTTPS `/mcp`;
2. unauthenticated MCP access returns `401 Unauthorized` with a Bearer `WWW-Authenticate` challenge;
3. `resource_metadata` stays on the same MCP origin and uses an RFC 9728 well-known path;
4. protected-resource metadata binds `resource` to the exact MCP endpoint and advertises the expected WorkOS issuer;
5. the MCP client authenticates through real OAuth (or, for controlled diagnostics, an environment-only bearer token);
6. exactly nine standard Radar tools plus `deep_research_ai_projects` are discovered;
7. standard tools remain read-only/idempotent while Premium is non-destructive but not declared read-only/idempotent;
8. one standard `search_ai_projects` invocation succeeds end to end;
9. the report records the local candidate commit and never records an access/refresh token.

The ordinary Hosted smoke never calls the Premium model and therefore does not consume the first-free Premium trial or an AI credit.

### Final Hosted Private Alpha readiness command

Reuse the same External Alpha CI/live/Codex evidence and the already-completed named human review, then add the hosted remote report:

```bash
osi-hosted-evidence-readiness \
  --root . \
  --ci-evidence /ABS/PATH/ci-evidence.json \
  --live-validation-evidence /ABS/PATH/validation-evidence.json \
  --codex-acceptance-report /ABS/PATH/codex-acceptance/live.json \
  --hosted-remote-evidence /ABS/PATH/hosted-remote.json \
  --artifact-reviewed \
  --reviewer "REVIEWER NAME" \
  --expected-base-url https://aiworkstation.cn \
  --expected-hosted-mcp-url https://mcp.aiworkstation.cn/mcp \
  --expected-oauth-issuer https://<authkit-domain> \
  --output tmp/hosted-private-alpha-readiness.json
```

This command exits `0` only when `hosted_private_alpha_ready=true`.

The Hosted wrapper deliberately **does not expose manual `--remote-mcp-tested` or `--hosted-gateway-protected` shortcuts**. Those two facts are derived from the hosted remote evidence. A wrong candidate SHA, wrong MCP URL, wrong issuer, missing 401 OAuth boundary, missing Premium tool, failed standard search, unauthenticated run, or failed report causes the gate to fail closed.

## What Hosted Private Alpha still does not claim

A passing Hosted Private Alpha report still does **not** claim broad public-launch readiness. Real-money billing, Premium credit semantics, service-specific legal/retention policy, revocation/rate-limit abuse testing at production settings, final platform connection identity, fresh-install acceptance, and directory/platform review remain separate launch decisions.
