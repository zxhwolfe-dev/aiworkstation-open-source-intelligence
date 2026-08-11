# Manual Live Contract Validation

The repository includes a manually triggered GitHub Actions workflow:

```text
.github/workflows/live-contract-validation.yml
```

It validates the current `main` branch against the public AI Workstation Radar
without adding credentials, write permissions or an automatic schedule.

## Why it is manual

Live contract validation makes external requests and captures sanitized public
response shapes. It should run deliberately when:

- the public Radar deployment changes;
- the adapter or contract code changes;
- a new alpha build is being prepared;
- a production probe failed and needs diagnosis.

It does not run on pull requests, pushes or a recurring schedule. This prevents
unnecessary traffic and avoids uploading response artifacts without an explicit
operator decision.

## Run it

In the repository on GitHub:

1. Open **Actions**.
2. Select **live-contract-validation**.
3. Choose **Run workflow**.
4. Select one of the allow-listed public origins.
5. Keep `infiniflow/ragflow` or enter another public `owner/repository` ID.
6. Start the run.

The workflow accepts only:

```text
https://aiworkstation.cn
https://useaistation.com
```

The project input must use `owner/repository` form. Inputs are validated before
any public request is made.

## Gates executed

The job runs in this order:

1. install the package with the MCP runtime;
2. run the full offline unit suite;
3. validate the unified Skill plus Hosted MCP plugin package;
4. run English and Chinese public probes;
5. capture sanitized English and Chinese response fixtures;
6. validate the fixture contract;
7. replay the fixtures through the hardened provider;
8. scan the captures for forbidden sensitive or internal fields;
9. write a GitHub Actions summary;
10. upload the sanitized validation bundle.

The artifact is uploaded only if every preceding gate succeeds. A failed
sanitization scan never uploads the captured directory.

## Artifact contents

A successful run uploads one artifact retained for 14 days. It contains:

```text
SUMMARY.md
probe-en.json
probe-zh.json
replay-en.json
replay-zh.json
contracts-en/
contracts-zh/
```

Each contract directory contains:

```text
manifest.json
project-list.json
project-detail.json
selector-formal.json
selector-no-match.json
```

The capture process removes query text, client IDs, credential-like fields and
internal publication identifiers. Long strings and lists are bounded. The
workflow then performs a second independent forbidden-key scan before upload.

## Interpreting failures

Do not weaken a contract check merely to make the workflow green.

Classify a failure as one of:

- package or unit-test regression;
- network, DNS or TLS failure;
- public API rate limit or temporary outage;
- changed project-list or project-detail shape;
- missing or mismatched snapshot identity;
- selector evidence state regression;
- near-match boundary violation;
- missing explicit no-match reason;
- license representation change;
- sanitization or artifact-safety failure.

For public-contract changes, compare the failed output with
[`akaiagents-integration.md`](akaiagents-integration.md). Document the smallest
additive upstream change required before modifying `akaiagents`.

## Release use

For an external alpha, record:

- workflow run ID;
- tested commit SHA;
- selected origin and project ID;
- whether both language probes passed;
- whether fixture validation and replay passed;
- manual reviewer and review date.

A successful workflow is necessary but not sufficient for release. The
operator must still review the sanitized artifact and complete the remaining
checks in [`production-validation.md`](production-validation.md).
