# Release Readiness Report

`osi-readiness` produces a machine-readable report that separates repository readiness, Skills-only External Alpha readiness, Hosted Private Alpha readiness, and broad Public Launch readiness.

For release decisions, prefer the evidence-first wrappers:

- `osi-evidence-readiness` for External Alpha;
- `osi-hosted-evidence-readiness` for Hosted Private Alpha.

They derive machine-verifiable gates from candidate-bound evidence instead of trusting operator booleans.

## Candidate identity

Readiness evidence belongs to an exact Git commit. A previously reviewed candidate remains valid for that frozen build, but its CI/live/Codex artifacts do not certify a newer commit.

When Hosted work creates a new candidate SHA, generate fresh candidate-bound CI, bilingual live-validation, and Codex evidence for that SHA; review its sanitized live artifact; then add the Hosted remote OAuth/MCP evidence. Stale artifacts fail closed.

## Code readiness

From the repository root:

```bash
osi-readiness --root . --output tmp/readiness.json
```

The default exit status reflects `code_ready`. Ordinary CI can verify the source tree without falsely certifying production contracts, Codex testing, a hosted endpoint, or human review.

Code readiness validates:

- required source, Skill, workflow, schema, deployment, legal, and release files;
- the Skills-only plugin package;
- Python/plugin/changelog version alignment;
- two byte-identical deterministic Skills builds;
- Skills-only distribution scope and absence of a bundled live-MCP claim.

A healthy tree before external evidence is supplied is expected to look like:

```json
{
  "code_ready": true,
  "external_alpha_ready": false,
  "hosted_private_alpha_ready": false,
  "public_launch_ready": false
}
```

## Evidence-first External Alpha

The preferred path combines:

1. `ci-evidence.json` from the successful Python 3.10/3.12 CI matrix;
2. `validation-evidence.json` plus the protected bilingual live-contract artifact;
3. a real `osi-codex-acceptance` report and matching privacy-safe ledger covering all nine standard tools;
4. a human artifact-review decision and reviewer identity.

See [`evidence-readiness.md`](evidence-readiness.md) for the exact command and candidate-binding checks.

The older `osi-readiness` attestation flags remain available for compatibility and internal diagnostics, but operator booleans do not replace real machine artifacts in an evidence-first release decision.

## Readiness levels

### `code_ready`

True only when repository structure, plugin package, version alignment, deployment scaffolding, public release documents, and deterministic Skills bundle pass their offline checks.

### `external_alpha_ready`

True only when `code_ready` is true and the current candidate has passing:

- English contract validation and provider replay;
- Chinese contract validation and provider replay;
- Python 3.10 CI;
- Python 3.12 CI;
- real nine-standard-tool Codex/MCP integration evidence;
- sanitized artifact review;
- recorded workflow/run identity;
- named human reviewer.

This level is appropriate for distributing the reviewed Skills-only alpha package to an invited cohort.

### `hosted_private_alpha_ready`

Requires all External Alpha gates for the **same Hosted candidate commit**, plus machine evidence proving:

- the canonical endpoint is a credential-free HTTPS `/mcp` URL;
- an unauthenticated MCP request receives a Bearer `401` OAuth challenge;
- RFC 9728 protected-resource metadata binds the exact MCP resource and expected authorization server;
- a real authenticated MCP client connects successfully;
- exactly nine standard tools plus the Premium tool are discoverable with correct side-effect annotations;
- a standard read-only search succeeds end to end over the deployed endpoint.

Use `osi-hosted-evidence-readiness`. It intentionally does not expose manual remote-test/gateway-protection shortcuts.

This level is for invited hosted testing, not unrestricted Internet launch. It verifies the authentication and connectivity boundary without requiring the Premium model to be invoked or a payment to occur.

### `public_launch_ready`

Intentionally remains false until the **hosted/public service** gates are complete.

The public repository and Skills-only package have resolved repository-level blockers such as:

- Apache-2.0 software license;
- public repository Privacy/Terms/Support/Security documents;
- public Skills listing/submission metadata.

Remaining broad public hosted-service blockers include:

- service-specific hosted privacy/terms/retention policy;
- production identity/revocation behavior with the final OAuth account;
- production quotas, rate limiting, and abuse controls;
- Paddle/Premium billing and credit semantics;
- canonical public MCP connection/domain review;
- actual public directory/platform submission approval and publish action.

Do not remove these blockers merely to make a readiness report green. Resolve the underlying product/infrastructure/platform gates.

## Public Skills release versus Hosted MCP

These are separate release layers.

A Skills-only package can be prepared and distributed without pretending that a public Hosted MCP is already available. Its Skills explicitly degrade to requirements/verification workflows when live tools are absent.

A combined Skills + Hosted MCP release requires the additional hosted-service gates above.

## Report integrity

The v2 base report separates:

- `code_blockers`;
- `operational_blockers`;
- `hosted_alpha_blockers`;
- `public_launch_blockers`;
- plugin warnings;
- individual checks/details;
- explicit operator attestations.

`osi-evidence-readiness` records validated CI, Codex, and live-validation evidence summaries. `osi-hosted-evidence-readiness` adds validated Hosted remote OAuth/MCP evidence and replaces the legacy remote/gateway booleans with machine-derived results.

## CI behavior

The standard CI workflow runs readiness without external live/reviewer evidence. It requires `code_ready=true` while ordinary CI alone must not certify an External Alpha or Hosted/Public launch.

Use candidate-bound workflow evidence, real Codex acceptance, human artifact review, and—at the Hosted stage—authenticated remote OAuth/MCP evidence for release decisions.
