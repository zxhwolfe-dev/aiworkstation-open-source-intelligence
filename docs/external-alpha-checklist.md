# External Alpha Release Checklist

Use this checklist before inviting anyone outside the core development workflow.
A checked box must be backed by a commit, workflow run, artifact or named manual
reviewer. Do not check an item based only on intent.

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
- [ ] `osi-validate-plugin --root .` succeeds.
- [ ] The bilingual core evaluation corpus passes structural checks.
- [ ] The bilingual plugin workflow corpus passes structural checks.
- [ ] In-memory MCP tests discover exactly six tools.
- [ ] All tools advertise read-only, non-destructive and idempotent hints.

## Live public contract

- [ ] The manual `live-contract-validation` workflow succeeds.
- [ ] English public probe succeeds.
- [ ] Chinese public probe succeeds.
- [ ] English contract capture validates and replays.
- [ ] Chinese contract capture validates and replays.
- [ ] Artifact forbidden-key scan succeeds.
- [ ] A human reviewer inspects the sanitized artifact.
- [ ] The validation workflow run ID is recorded.
- [ ] The tested AI Workstation origin is recorded.

## Data and decision boundaries

- [ ] Every verified fact has evidence and observation time.
- [ ] Recommendations are separate from verified facts.
- [ ] Unknown fields remain explicit.
- [ ] Missing and sentinel licenses remain unknown.
- [ ] Non-standard license labels require manual review.
- [ ] Near matches never appear as full matches.
- [ ] Impossible constraints return an explicit no-match state.
- [ ] Mixed-snapshot comparison fails closed.
- [ ] Proposed cross-project compatibility is not presented as verified.

## Security and privacy

- [ ] No tool writes to AI Workstation, GitHub or the local filesystem.
- [ ] No tool executes or installs third-party repository code.
- [ ] MCP server instructions preserve the untrusted-content boundary.
- [ ] No real credential is required for the anonymous alpha path.
- [ ] Logs and artifacts contain no full confidential prompts.
- [ ] `SECURITY.md` contains a usable private reporting route.
- [ ] `PRIVACY.md` matches the actual pre-release behavior.
- [ ] Security findings classified critical or high are closed or blocking.

## Distribution package

- [ ] Skills-only plugin package validates locally.
- [ ] Package does not claim a live MCP connection when none is bundled.
- [ ] Package does not claim an open-source license before one is selected.
- [ ] Included files have been reviewed for secrets and private internal data.
- [ ] Checksums are generated for distributed archives.
- [ ] Installation instructions were tested in a clean environment.
- [ ] Uninstallation or rollback instructions are documented.

## Tester readiness

- [ ] Invited tester count and target profile are documented.
- [ ] Test window and request-volume expectations are documented.
- [ ] Testers receive `alpha-tester-guide.md`.
- [ ] Required Chinese and English scenarios are assigned.
- [ ] Feedback template and severity definitions are provided.
- [ ] Critical findings have a private escalation path.
- [ ] A person is assigned to triage feedback during the test window.

## Commercial and legal readiness

These are not required for a private technical alpha but block a broad public
launch:

- [ ] Publisher identity is final.
- [ ] Software license is selected.
- [ ] Public privacy policy is published.
- [ ] Terms of service are published.
- [ ] Support contact is published.
- [ ] Data-source commercial-use review is complete.
- [ ] Public MCP authentication, quotas and abuse controls are designed.
- [ ] Country availability and platform submission attestations are decided.

## Release decision

Record one outcome:

```text
GO
Candidate commit:
Tag:
CI run:
Live validation run:
Artifact reviewer:
Tester count:
Known limitations:
```

or:

```text
NO-GO
Candidate commit:
Blocking items:
Owner for each blocker:
Next review date:
```

A failed live contract, evidence boundary, license boundary, security gate or
artifact sanitization gate is always a no-go condition.
