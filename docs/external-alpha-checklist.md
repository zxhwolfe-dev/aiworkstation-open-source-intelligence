# External Alpha Release Checklist

Use this checklist before inviting anyone outside the core development workflow. A checked box must be backed by the current candidate commit, a workflow artifact, a real Codex acceptance report, or a named human reviewer.

The preferred machine-evidence flow is documented in [`evidence-readiness.md`](evidence-readiness.md).

## Source and build identity

- [ ] `main` is the intended release source of truth.
- [ ] The working tree used for local validation was clean.
- [ ] The candidate commit SHA is recorded.
- [ ] Plugin and Python package versions agree.
- [ ] A pre-release tag has been selected but not force-moved.
- [ ] Release notes describe limitations as well as features.

## Automated validation

- [ ] The standard `ci` workflow succeeds on Python 3.10.
- [ ] The standard `ci` workflow succeeds on Python 3.12.
- [ ] The successful matrix produces `ci-evidence.json` for the same candidate commit.
- [ ] `osi-validate-plugin --root .` succeeds.
- [ ] The bilingual evaluation corpora pass.
- [ ] In-memory MCP tests discover exactly six tools.
- [ ] All tools advertise read-only, non-destructive and idempotent hints.

## Real Codex MCP acceptance

- [ ] `osi-codex-acceptance` runs from the same candidate commit.
- [ ] The acceptance uses the intended live HTTP provider/origin.
- [ ] Codex completes successfully in the ephemeral read-only acceptance session.
- [ ] The privacy-safe ledger records at least one successful invocation for each of the six tools.
- [ ] The report SHA-256 matches the ledger file.
- [ ] `osi-evidence-readiness` accepts the candidate-bound Codex report.

## Live public contract

- [ ] `live-contract-validation` succeeds for the same candidate commit.
- [ ] English public probe succeeds.
- [ ] Chinese public probe succeeds.
- [ ] English capture validates and replays.
- [ ] Chinese capture validates and replays.
- [ ] Artifact forbidden-key scan succeeds.
- [ ] `validation-evidence.json` is present and protected-file SHA-256 checks pass.
- [ ] The tested AI Workstation origin is the intended origin.
- [ ] A human reviewer inspects the sanitized artifact.
- [ ] Reviewer identity is recorded.

## Data and decision boundaries

- [ ] Every verified fact has evidence and observation time.
- [ ] Recommendations are separate from verified facts.
- [ ] Unknown fields remain explicit.
- [ ] Missing/sentinel licenses remain unknown.
- [ ] Non-standard license labels require manual review.
- [ ] Near matches never appear as full matches.
- [ ] Impossible constraints return explicit no-match.
- [ ] Mixed-snapshot comparison fails closed.
- [ ] Cross-project compatibility is not presented as verified without testing.

## Security and privacy

- [ ] Product tools remain read-only.
- [ ] No tool executes or installs third-party repository code.
- [ ] MCP instructions preserve the untrusted-content boundary.
- [ ] No real credential is required for the anonymous alpha provider path.
- [ ] Acceptance ledger contains no tool arguments, project IDs, queries, prompts, results or raw request IDs.
- [ ] Live contract artifacts contain no forbidden/private internal fields.
- [ ] `SECURITY.md`, `PRIVACY.md`, `TERMS.md`, and `SUPPORT.md` match the release scope.
- [ ] Critical/high findings are closed or explicitly block release.

## Distribution package

- [ ] Skills-only plugin package validates locally.
- [ ] Package does not claim a live MCP connection when none is bundled.
- [ ] Apache-2.0 `LICENSE` is included.
- [ ] `TERMS.md`, privacy, support and security docs are included.
- [ ] English/Chinese onboarding is included.
- [ ] Included files have been reviewed for secrets/private internal data.
- [ ] Checksums are generated for distributed archives.
- [ ] Installation instructions were tested in a clean environment.

## Tester readiness

- [ ] Invited tester count and target profile are documented.
- [ ] Test window and request-volume expectations are documented.
- [ ] Testers receive `alpha-tester-guide.md`.
- [ ] Required Chinese and English scenarios are assigned.
- [ ] Feedback template and severity definitions are provided.
- [ ] Critical findings have a private escalation path.
- [ ] A person is assigned to triage feedback.

## Public Skills release preparation

- [x] Public repository license selected: Apache-2.0.
- [x] Public repository privacy statement published.
- [x] Public Terms published.
- [x] Public Support/Security routes published.
- [x] English/Chinese README and Quickstart prepared.
- [x] Structured issue intake prepared.
- [x] OpenAI Skills-only submission copy and 5+3 review cases prepared.
- [x] GitHub/PyPI/GHCR publishing workflows prepared.
- [ ] Publisher/developer identity verification complete on target platform.
- [ ] Final logo/social preview uploaded.
- [ ] Cohort feedback complete and release candidate revalidated.
- [ ] Platform submission reviewed/approved.

## Hosted public MCP — separate gate

The following do not block the first Skills-only public package, but they block a broad hosted MCP release:

- [ ] Canonical public MCP hostname and deployment owner finalized.
- [ ] Service-specific privacy/terms/retention policy finalized.
- [ ] Identity/authentication and revocation finalized as required by product scope.
- [ ] Production quotas, rate limiting and abuse controls delivered.
- [ ] Monitoring/incident response delivered.
- [ ] Remote bilingual MCP validation passed.
- [ ] Platform connection/domain review completed.

## Release decision

The final machine gate should be generated with `osi-evidence-readiness`.

```text
GO
Candidate commit:
Tag:
CI evidence run:
Live validation run:
Codex acceptance report:
Artifact reviewer:
Tester count:
Known limitations:
```

A failed candidate-binding check, live contract, six-tool Codex acceptance, evidence/license/security boundary, or artifact sanitization gate is always a no-go condition.
