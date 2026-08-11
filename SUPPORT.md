# Support

## Pre-release support scope

AI Workstation Open Source Intelligence is in pre-release alpha. Support is
focused on:

- plugin installation and Skill discovery;
- MCP tool discovery and read-only calls;
- public Radar contract compatibility;
- incorrect fact/recommendation/unknown/risk separation;
- bilingual workflow regressions;
- packaging and deployment defects.

General consulting about arbitrary third-party repositories is outside the
project support channel unless it demonstrates a product defect.

## Bug reports

Use the repository issue templates for ordinary alpha defects. Before posting,
remove:

- API keys, bearer tokens and cookies;
- private source code or proprietary documents;
- personal or customer data;
- full production prompts when a minimal reproduction is enough;
- unsanitized public-contract captures.

Include the smallest safe reproduction, the project version or commit, the MCP
host/client version, and whether the mock or HTTP provider was used.

## Public contract changes

Use the dedicated public-contract issue template when a Radar response shape no
longer satisfies the documented adapter contract. Attach only sanitized fixture
material and describe the smallest public field difference that reproduces the
problem.

## Security reports

Do not report exploitable security issues in a public issue. Follow
[`SECURITY.md`](SECURITY.md) and use the private contact path described there.

## Service-level expectations

There is no guaranteed response or resolution time during Alpha. The production
Hosted MCP is provided on an as-available basis; a formal support channel and
service-level policy must be published before any paid or SLA-backed offering.
