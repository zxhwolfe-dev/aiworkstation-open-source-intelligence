# Privacy Statement

## Current repository and alpha behavior

The default local configuration uses deterministic fixture data and performs no
network access.

When an operator explicitly selects `OSI_PROVIDER=http`, the tools send the
technical search query and structured constraints needed to answer the request
to AI Workstation's public Open Source Radar API. The repository does not need
account credentials, private repositories, customer documents or source-code
archives for these read-only research tasks.

The codebase can also expose a guarded Streamable HTTP MCP endpoint for
local/private-alpha deployment. The repository does not currently provide a
public multi-user account service, billing system or native OAuth identity
layer. Operators must not describe a private-alpha deployment as a finished
public service.

GitHub may process repository visits, clones, issues, workflow activity and other
platform events under GitHub's own terms and privacy practices.

## Data minimization

Tool inputs should contain only:

- the research task;
- public project identifiers;
- technical/deployment constraints;
- non-sensitive decision context needed for comparison or stack planning.

Do not submit:

- API keys, passwords, bearer tokens or cookies;
- personal/customer records;
- proprietary source code or documents;
- private repository contents;
- secrets embedded in URLs or issue reports.

The contract-capture tooling removes query/prompt text, client/request IDs,
credential-like fields, raw content and internal publication identifiers before
fixtures are retained for review.

## Logging and hosted deployments

This repository does not prescribe a production logging backend or retention
period yet. A private hosted-alpha operator should log the minimum operational
metadata needed for reliability/security and should avoid retaining complete
prompts or authorization credentials.

Before a broad hosted service is launched, the publisher must decide and publish:

- data categories and purposes;
- legal basis where applicable;
- processors and hosting regions;
- log and evaluation-sample retention periods;
- deletion/export/correction channels;
- whether any submitted data is used for model training;
- international-transfer safeguards where required;
- incident/security contact and final support channel.

## Public-service gate

The current repository policy is a pre-release engineering statement, not a
substitute for a final service-specific privacy policy. Final public privacy and
terms URLs are explicit release blockers in `osi-readiness` and
`docs/public-launch-decisions.md`.
