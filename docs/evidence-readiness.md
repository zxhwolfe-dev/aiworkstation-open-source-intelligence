# Evidence-first external-alpha readiness

This is the preferred release-evidence path for the Skills-only external alpha.
It replaces manual claims about CI, live validation, and Codex testing with
candidate-bound machine evidence. Human review remains intentionally human.

## Evidence inputs

All three machine artifacts must belong to the same Git commit as the local
candidate checkout.

### 1. Standard CI evidence

The `ci` workflow runs the full repository suite on Python 3.10 and 3.12. Only
after every matrix job succeeds does the `publish-ci-evidence` job upload:

```text
ci-evidence-<run-id>/ci-evidence.json
```

The manifest records the repository, candidate commit, run ID, exact Python
matrix, and successful 3.10/3.12 gates. A stale artifact from an older commit is
rejected.

### 2. Live contract-validation evidence

Run the `live-contract-validation` workflow against the intended public AI
Workstation origin. It performs both English and Chinese probes, sanitized
contract capture, validation, hardened replay, and forbidden-key scanning.

Only after those stages succeed does its artifact include:

```text
validation-evidence.json
```

The manifest binds the workflow run to the repository commit and public origin,
points to the EN/ZH contract directories, and records SHA-256 for every protected
file in the downloaded validation bundle. `osi-evidence-readiness` verifies those
hashes before using the contracts.

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

The command starts `codex exec` non-interactively with an ephemeral session,
read-only shell sandbox, no command-approval prompts, and a temporary required
MCP server exposing exactly the six OSI tools. It does not rewrite the user's
persistent Codex MCP configuration.

The acceptance result is not based on the model saying it used the tools. The
MCP server writes a privacy-safe JSONL ledger containing only tool name, outcome,
duration, level, timestamp, and error code. The report stores the ledger SHA-256.
Readiness reopens the ledger, verifies the digest, recalculates the six-tool
success set, and checks that the report commit matches the current candidate.

## Human review

The live-validation artifact is deliberately sanitized, but a human still must
review it before external alpha. The reviewer should confirm at least:

- both probe reports passed;
- both contract manifests identify the intended locale and project;
- replay reports passed;
- no secrets, raw prompts, internal evidence IDs, source hashes, publication
  versions, or private data are present;
- unknown license evidence remains unknown instead of being inferred;
- the artifact corresponds to the intended candidate and public origin.

Record the reviewer's name only after that review is complete. Do not use a model
or CI job to self-attest this gate.

## Final readiness command

After downloading the CI and live-validation artifacts and completing the real
Codex acceptance run:

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

When live workflow evidence is supplied, the command derives the EN/ZH contract
directories and workflow run ID from that manifest. When CI evidence is supplied,
it derives the Python 3.10 and 3.12 gates from the manifest. Invalid supplied
machine evidence fails closed and cannot be overridden by the legacy manual
boolean flags in the same invocation.

A passing external-alpha report still does **not** claim public-launch readiness.
Software licensing, public legal/privacy terms, per-user identity and revocation,
production quotas/rate limiting/abuse controls, and public directory review
remain separate launch decisions.
