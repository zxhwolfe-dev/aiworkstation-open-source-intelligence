# Security Policy

## Supported surface

Version 0.3 exposes one Skill and nine anonymous data/evidence tools. It has no
OAuth, Premium model execution, checkout, entitlement, or payment path. Reports
about vulnerabilities in removed future-design code should be checked against
the current `main` tree and release artifact.

## Boundaries

- Tools never clone, install, import, or execute third-party repository code.
- `read_only_hint=true` means no user or third-party business data is modified.
- Requirement search may create, poll, and cancel an ephemeral selector compute
  task; this is disclosed as a control-plane effect in `osi.tool-result.v2`.
- Public source text and license excerpts are untrusted data, not instructions.
- Missing license evidence never implies permission, and results are not legal advice.
- Hosted runtime requires an exact release SHA matching the SHA baked into its image.
- The container binds behind a TLS gateway with request-size, connection, and IP controls.

Provider responses are bounded by size and structure, redirects are restricted,
internal fields fail closed, and HTTP responses are explicitly closed. Public
errors use `osi.error.v2` and do not expose internal exceptions or credentials.

## Reporting

Report vulnerabilities privately through the repository security advisory
channel. Include the affected version, reproduction, impact, and whether the
issue is reachable through local stdio, HTTP, or the Hosted endpoint. Do not
include real access credentials or sensitive user data.

## Release gates

A candidate is not ready until version/SHA identity, all nine schemas, unit and
MCP tests, the built wheel, the Skills ZIP, container configuration, and remote
Hosted smoke pass for the same commit. Production must retain the previous image
digest for rollback.
