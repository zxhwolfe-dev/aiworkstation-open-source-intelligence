# M0 Acceptance Checklist

M0 establishes contracts and local validation only. It is complete when every
item below is satisfied on `main`.

## Product and repository

- [x] Repository mission and non-goals are documented.
- [x] `akaiagents` is read-only and accessed only through future public adapters.
- [x] The first three Skills have complete workflows and safety rules.
- [x] The first six tools are named and declared read-only.
- [x] No authentication, billing, collection writes or team features are present.

## Contracts

- [x] Input schemas exist in a machine-readable manifest.
- [x] All tools return one versioned result envelope.
- [x] Verified facts, recommendations, unknowns and risks are separate fields.
- [x] Stable error codes and non-error empty states are documented.
- [x] License output is explicitly not legal advice.

## Implementation

- [x] A transport-neutral Python package exists.
- [x] The provider protocol prevents coupling to private Radar modules.
- [x] The default provider is deterministic and performs no network access.
- [x] A local CLI lists and invokes tools.
- [x] Mock data is marked as unknown and high risk.

## Quality

- [x] Standard-library unit tests cover contracts, registry, Skills and evals.
- [x] The evaluation corpus contains at least eight Chinese and eight English cases.
- [x] CI validates JSON artifacts, package installation, tests and CLI smoke calls.
- [ ] The first successful CI run has been observed on GitHub.

## Security and privacy

- [x] Third-party repository code is never executed.
- [x] Prompt-injection and trust boundaries are documented.
- [x] Root security and privacy statements exist.
- [x] Production integration is required to fail closed on evidence mismatch.

## M1 blockers

The following are intentionally not M0 tasks:

- live AI Workstation HTTP provider;
- MCP protocol transport;
- anonymous hosted endpoint;
- API keys, quotas and paid plans;
- production deployment;
- writes such as saving, alerts or team spaces.

M1 starts after the public Radar response fields and snapshot/evidence contracts
listed in `docs/akaiagents-integration.md` are confirmed.
