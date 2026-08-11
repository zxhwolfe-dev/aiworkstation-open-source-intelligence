# Production Validation Runbook

This runbook validates the public AI Workstation Radar contract, local Skills and
MCP behavior, and an exact production Hosted MCP candidate. All current Radar
validation is anonymous and read-only.

## Preconditions

```bash
cd /path/to/aiworkstation-open-source-intelligence
git status
git pull origin main

python -m venv .venv
source .venv/bin/activate
python -m pip install -e ".[mcp]"
```

Do not proceed with uncommitted local edits unless they are intentional and
reviewed.

## 1. Run the complete local suite

```bash
python -m unittest discover -s tests -v
python -m json.tool schemas/tool-manifest.json >/dev/null
python -m json.tool schemas/tool-result.schema.json >/dev/null
python -m json.tool evals/cases.json >/dev/null
python -m json.tool evals/plugin-cases.json >/dev/null
osi-validate-plugin --root .
osi-readiness --root . --output tmp/readiness.json
```

A code-complete tree should report `code_ready=true`. Candidate-bound live and
Hosted states remain false until their evidence is supplied for that exact
source commit.

Smoke-test installed commands:

```bash
osi-m0 provider-info
osi-m0 list-tools
osi-mcp-http --check-config
osi-remote-smoke --help
osi-probe --help
osi-capture-contracts --help
osi-validate-contracts --help
osi-replay-contracts --help
osi-readiness --help
```

Record the commit under test:

```bash
git rev-parse HEAD
```

## 2. Run English and Chinese public probes

```bash
mkdir -p tmp/public-validation

osi-probe \
  --base-url https://aiworkstation.cn \
  --locale en \
  --project-id infiniflow/ragflow \
  --output tmp/public-validation/probe-en.json

osi-probe \
  --base-url https://aiworkstation.cn \
  --locale zh \
  --project-id infiniflow/ragflow \
  --output tmp/public-validation/probe-zh.json
```

Both reports should have `"ok": true`. Do not weaken adapter checks merely to
turn a failed probe green. Determine whether a failure is network/TLS,
production data availability, a changed public response shape, missing snapshot
identity, malformed selector evidence, an expected unknown license, or an
adapter defect.

## 3. Capture, validate and replay public contracts

```bash
osi-capture-contracts \
  --base-url https://aiworkstation.cn \
  --locale en \
  --project-id infiniflow/ragflow \
  --output-dir tmp/public-validation/contracts-en

osi-capture-contracts \
  --base-url https://aiworkstation.cn \
  --locale zh \
  --project-id infiniflow/ragflow \
  --output-dir tmp/public-validation/contracts-zh

osi-validate-contracts --directory tmp/public-validation/contracts-en
osi-validate-contracts --directory tmp/public-validation/contracts-zh

osi-replay-contracts \
  --directory tmp/public-validation/contracts-en \
  --output tmp/public-validation/replay-en.json

osi-replay-contracts \
  --directory tmp/public-validation/contracts-zh \
  --output tmp/public-validation/replay-zh.json
```

Replay derives locale and stable project identity from each sanitized capture's
`manifest.json`; do not supply separate replay identity flags that could diverge
from the captured request.

Each contract directory contains:

```text
manifest.json
project-list.json
project-detail.json
selector-formal.json
selector-no-match.json
```

The validator checks schema versions, bounded sanitized content, snapshot and
project identity, selector evidence state, formal/near-match separation and
explicit no-match behavior. A missing direct detail snapshot may be a warning
when exact project identity still matches the captured listing; other contract
violations fail closed.

Review the sanitized files manually before retaining or sharing them. They must
not contain credentials, user query text, private content or internal
publication identifiers.

The repository also provides a manual workflow that runs the bilingual probe,
capture, validation, replay and forbidden-key scan before uploading any
artifact:

```text
.github/workflows/live-contract-validation.yml
```

## 4. Review the response contracts

### Project list

Confirm a non-empty public snapshot ID, stable project identity, correct exact
project resolution and absence of internal publication fields.

### Project detail

Confirm the final item exists, identity matches the list result, snapshot is
compatible, decision fields use the shapes expected by the adapter, transparency
is public-safe and archived status is explicit.

### Selector formal result

Confirm `evidence_status` is `available`, or `partial` with a visible notice;
formal projects carry stable IDs; near matches are not mixed into formal
recommendations; internal fields do not leak.

### Selector no-match result

Confirm there is an explicit `no_match_reason`, any near match has exactly one
`conflict` or `unverified` blocker, no more than three near matches are exposed,
and hard requirements are never silently relaxed.

## 5. Test the local MCP workflow from Codex

Follow [`codex-setup.md`](codex-setup.md). Start with:

```text
OSI_PROVIDER=mock
```

Then use live read-only Radar data:

```text
OSI_PROVIDER=http
AIWORKSTATION_RADAR_BASE_URL=https://aiworkstation.cn
```

Confirm Codex discovers exactly nine tools and each advertises:

```text
read_only_hint = true
destructive_hint = false
idempotent_hint = true
open_world_hint = true
```

Exercise discovery, named-project fact and license verification, Dify/RAGFlow
comparison, alternatives, stack composition and an impossible requirement set.
The no-match fixture uses an explicit deterministic structured filter and must remain an honest no-match result.

## 6. Validate the complete-Plugin external alpha gate

After CI, Codex testing and human review are real and recorded:

```bash
osi-readiness \
  --root . \
  --contracts-en tmp/public-validation/contracts-en \
  --contracts-zh tmp/public-validation/contracts-zh \
  --ci-python310-passed \
  --ci-python312-passed \
  --codex-tested \
  --artifact-reviewed \
  --live-validation-run-id REAL_RUN_ID \
  --reviewer "REAL_REVIEWER" \
  --require-external-alpha \
  --output tmp/external-alpha-readiness.json
```

These flags are operator attestations, not automatically discovered proof. Use
real evidence only.

## 7. Deploy the guarded public data-only Hosted MCP

Read [`hosted-mcp.md`](hosted-mcp.md). A local/container configuration can be
checked without opening a socket:

```bash
osi-mcp-http --check-config
```

Build the exact candidate container:

```bash
docker build --build-arg OSI_IMAGE_COMMIT="$(git rev-parse HEAD)" -t aiworkstation-osi-mcp:0.3.0 .
docker compose -f compose.public-hosted.example.yml config
```

The public example maps the container to host loopback only. Production uses a
TLS/Nginx gateway with strict Host/path policy plus request-body, short-window,
sustained-window and connection controls. The current service is anonymous only
because it exposes public read-only data; future private/member data requires a
new authorization design.

For the production endpoint, use the credential-free HTTPS MCP URL and run:

```bash
osi-remote-smoke --url https://mcp.aiworkstation.cn/mcp
osi-remote-smoke \
  --url https://mcp.aiworkstation.cn/mcp \
  --invoke-search \
  --locale en
osi-remote-smoke \
  --url https://mcp.aiworkstation.cn/mcp \
  --invoke-search \
  --locale zh
```

Do not use a URL containing tokens, usernames, passwords, query parameters or
fragments.

## 8. Validate candidate-bound Hosted readiness

After the hosted endpoint has actually passed remote MCP smoke tests and the
operator has confirmed gateway protection:

```bash
osi-readiness \
  --root . \
  --contracts-en tmp/public-validation/contracts-en \
  --contracts-zh tmp/public-validation/contracts-zh \
  --ci-python310-passed \
  --ci-python312-passed \
  --codex-tested \
  --artifact-reviewed \
  --live-validation-run-id REAL_RUN_ID \
  --reviewer "REAL_REVIEWER" \
  --remote-mcp-tested \
  --remote-mcp-url https://mcp.aiworkstation.cn/mcp \
  --hosted-gateway-protected \
  --require-hosted-alpha \
  --output tmp/hosted-alpha-readiness.json
```

`hosted_private_alpha_ready=true` is the historical machine field for this
candidate gate. It does not prove public-directory approval, ongoing production
health, external tester retention or incident readiness.

## 9. Decide whether an upstream Radar change is necessary

A change to `akaiagents` is justified only when production evidence shows the
public contract cannot safely provide stable identity, snapshot identity,
public evidence and observation time, unambiguous missing-license state,
selector evidence state, explicit no-match reason or near-match blocker status.
Document the smallest additive API change first; do not import private modules
or modify `akaiagents` from this repository.

## 10. Public plugin distribution remains a separate gate

The runtime endpoint can be production-ready while the combined plugin remains
unlisted. Before public-directory submission, complete the remaining decisions
in [`public-launch-decisions.md`](public-launch-decisions.md): publisher and
policy review, monitoring baseline, fresh-install acceptance, domain scan,
platform review and staged rollout.
