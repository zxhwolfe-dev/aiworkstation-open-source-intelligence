# Release Readiness Report

`osi-readiness` produces a machine-readable report that separates repository readiness, Skills-only external-alpha readiness, hosted private-alpha readiness, and broad public-launch readiness.

For the preferred evidence-first release path, use `osi-evidence-readiness`, which derives CI/live/Codex gates from candidate-bound evidence artifacts instead of relying only on operator booleans.

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

The preferred machine path combines:

1. `ci-evidence.json` from the successful Python 3.10/3.12 CI matrix;
2. `validation-evidence.json` plus the protected bilingual live-contract artifact;
3. a real `osi-codex-acceptance` report and matching privacy-safe ledger;
4. a human artifact-review decision and reviewer identity.

See [`evidence-readiness.md`](evidence-readiness.md) for the exact command and candidate-binding checks.

The older `osi-readiness` attestation flags remain available for compatibility, but operator booleans do not replace real workflow artifacts in a release decision.

## Readiness levels

### `code_ready`

True only when repository structure, plugin package, version alignment, deployment scaffolding, public release documents, and deterministic Skills bundle pass their offline checks.

### `external_alpha_ready`

True only when `code_ready` is true and the current candidate has passing:

- English contract validation and provider replay;
- Chinese contract validation and provider replay;
- Python 3.10 CI;
- Python 3.12 CI;
- real Codex/MCP integration evidence;
- sanitized artifact review;
- recorded workflow/run identity;
- named human reviewer.

This level is appropriate for distributing the reviewed Skills-only alpha package to an invited cohort.

### `hosted_private_alpha_ready`

Requires the full Skills-only gate plus:

- a credential-free HTTPS MCP endpoint URL;
- successful remote MCP smoke testing;
- an authenticated gateway or trusted private-network protection attestation.

This is for invited hosted testing, not unrestricted Internet launch.

### `public_launch_ready`

Intentionally remains false until the **hosted/public service** gates are complete.

The public repository and first Skills-only package have now resolved earlier repository-level blockers:

- Apache-2.0 software license selected;
- public repository Privacy/Terms/Support/Security documents published;
- public Skills listing/submission metadata prepared.

Remaining broad public hosted-service blockers include:

- service-specific hosted privacy/terms/retention policy;
- final user identity/authentication and revocation model where required by product scope;
- production quotas, rate limiting, and abuse controls;
- canonical public MCP connection/domain review;
- actual public directory/platform submission approval and publish action.

Do not remove these blockers merely to make a readiness report green. Resolve the underlying product/infrastructure/platform gates.

## Public Skills release versus hosted MCP

These are separate release layers.

A Skills-only package can be prepared and submitted without pretending that a public hosted MCP is already available. Its Skills explicitly degrade to requirements/verification workflows when live tools are absent.

A combined Skills + hosted MCP release requires the additional hosted-service gates above.

## Report integrity

The v2 report separates:

- `code_blockers`;
- `operational_blockers`;
- `hosted_alpha_blockers`;
- `public_launch_blockers`;
- plugin warnings;
- individual checks/details;
- explicit operator attestations.

`osi-evidence-readiness` additionally records validated CI, Codex, and live-validation evidence summaries.

## CI behavior

The standard CI workflow runs readiness without external live/reviewer evidence. It requires `code_ready=true` while ordinary CI alone must not certify an External Alpha or hosted launch.

Use candidate-bound workflow evidence, real Codex acceptance, and human artifact review for release decisions.
