# Release readiness

A release decision is bound to one exact `main` commit. Local checks do not
claim that CI, human review, staging, or remote Hosted validation occurred.

## Code gate

- Python 3.10, 3.11 and 3.12 tests pass;
- Ruff, core type checks, compileall, dependency audit and schemas pass;
- runtime, wheel, Plugin and Changelog versions agree;
- all nine mock/fixture results validate against Draft 2020-12;
- the deterministic one-Skill ZIP is built and inspected;
- OAuth, Premium, billing and checkout modules are absent from the artifact.

## Candidate evidence

CI, bilingual live Radar fixtures, deterministic evals and Codex/Host acceptance
must record the same 40-character commit. Human review confirms sanitized
artifacts contain no query, credential, internal field, or private payload.

## Hosted gate

Deploy the candidate image to a temporary loopback port. Verify its baked image
SHA matches the runtime release SHA, then run the anonymous `hosted-public`
remote smoke: exact endpoint, exact SHA, exactly nine read-only tools, a real
search, v2 result contract, and gateway policy evidence. Controlled overload
and 429/recovery tests belong in staging, not as routine production traffic.

Public launch requires a maintenance-window cutover, post-cutover smoke, and the
previous image digest ready for rollback. Version/SHA mismatch, schema failure,
tool-set drift, search/browse failure, or gateway regression triggers rollback.
