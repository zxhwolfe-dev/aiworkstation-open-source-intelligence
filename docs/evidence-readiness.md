# Evidence-first release readiness

This is the preferred release-evidence path for the Skills-only External Alpha and the Hosted Private Alpha. It replaces manual claims about CI, live validation, Codex testing, remote MCP testing, and gateway protection with candidate-bound machine evidence wherever those facts are machine-verifiable. Human artifact review remains intentionally human.

## Candidate identity rule

Every release stage is evaluated against the **exact Git commit being released**.

The completed External Alpha candidate `d338faf0...` and its reviewed artifacts remain valid evidence for that frozen External Alpha build. They do **not** automatically certify a later Hosted candidate whose source tree has a different commit SHA.

Whenever Hosted work changes code, configuration, tests, or release documents and produces a new candidate SHA, regenerate the candidate-bound CI, live-validation, and Codex evidence for that new SHA. Review the new sanitized live artifact and record the reviewer again. Readiness intentionally rejects stale evidence from an older commit.

Hosted deployment adds a second identity boundary: the remote service itself must prove it is running that same candidate. The deployment receives the exact SHA through `OSI_RELEASE_COMMIT`; Hosted MCP publishes it in `serverInfo.version`; the remote validator extracts it as `deployment_commit`; final readiness requires:

```text
local candidate commit == remote report commit == remote deployment_commit
```

This prevents a clean local checkout from certifying an older or different deployed image.

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

The live-validation artifact is deliberately sanitized, but a human still must review it before the candidate can pass the stage gate. The reviewer should confirm at least:

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

Hosted Private Alpha uses the **same types of External Alpha evidence, regenerated for the exact Hosted candidate SHA**, plus one new machine artifact: a candidate-bound, OAuth-authenticated remote MCP report.

Deploy that exact candidate with:

```text
OSI_RELEASE_COMMIT=<exact-40-character-hosted-candidate-sha>
```

After the Hosted candidate's fresh CI/live/Codex evidence is green and its sanitized live artifact has been reviewed, configure DNS/TLS/gateway/WorkOS and generate the Hosted remote report from that same candidate checkout:

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
4. protected-resource metadata returns HTTP 200, binds `resource` to the exact MCP endpoint, advertises the expected WorkOS issuer, and supports bearer tokens through the Authorization header;
5. the MCP client completes the real OAuth flow; `bearer-env` is diagnostic-only and cannot certify Hosted Private Alpha;
6. remote `serverInfo.version` encodes an exact deployment commit and that SHA equals the local candidate;
7. exactly nine standard Radar tools plus `deep_research_ai_projects` are discovered;
8. standard tools remain read-only/idempotent while Premium is non-destructive but not declared read-only/idempotent;
9. one standard `search_ai_projects` invocation succeeds end to end;
10. the report records the local candidate commit and remote deployment commit while never recording an access/refresh token.

The ordinary Hosted smoke never calls the Premium model and therefore does not consume the first-free Premium trial or an AI credit.

### Final Hosted Private Alpha readiness command

Use the **fresh CI/live/Codex evidence for the Hosted candidate**, the review decision for that candidate's live artifact, and the Hosted remote report:

```bash
osi-hosted-evidence-readiness \
  --root . \
  --ci-evidence /ABS/PATH/HOSTED-CANDIDATE/ci-evidence.json \
  --live-validation-evidence /ABS/PATH/HOSTED-CANDIDATE/validation-evidence.json \
  --codex-acceptance-report /ABS/PATH/HOSTED-CANDIDATE/codex-acceptance.json \
  --hosted-remote-evidence /ABS/PATH/HOSTED-CANDIDATE/hosted-remote.json \
  --artifact-reviewed \
  --reviewer "REVIEWER NAME" \
  --expected-base-url https://aiworkstation.cn \
  --expected-hosted-mcp-url https://mcp.aiworkstation.cn/mcp \
  --expected-oauth-issuer https://<authkit-domain> \
  --output tmp/hosted-private-alpha-readiness.json
```

This command exits `0` only when `hosted_private_alpha_ready=true`.

The Hosted wrapper deliberately **does not expose manual `--remote-mcp-tested` or `--hosted-gateway-protected` shortcuts**. Those facts are derived from the hosted remote evidence. A wrong local candidate SHA, wrong deployed SHA, wrong MCP URL, wrong issuer, missing 401 OAuth boundary, diagnostic bearer-only run, missing Premium tool, failed standard search, or failed report causes the gate to fail closed.

## What Hosted Private Alpha still does not claim

A passing Hosted Private Alpha report still does **not** claim broad public-launch readiness. Real-money billing, Premium credit semantics, service-specific legal/retention policy, revocation/rate-limit abuse testing at production settings, final platform connection identity, fresh-install acceptance, and directory/platform review remain separate launch decisions.
