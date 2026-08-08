# Privacy Statement

## Status

AI Open Source Intelligence is currently a **hosted public-product candidate**, not yet a broadly launched hosted service. This document describes the implemented data boundaries and the intended hosted behavior. Final service-specific privacy/retention terms must be published before real-money/public directory launch.

## Standard Radar tools

The nine standard tools are designed for public open-source project research and Radar browsing. Typical inputs contain only:

- research/search task;
- public project identifiers;
- ranking/collection/category/scenario IDs;
- technical/deployment/license constraints;
- non-sensitive decision context;
- output locale.

Do not submit through these tools:

- passwords/API keys/bearer tokens/cookies;
- private repository contents;
- proprietary source code/documents;
- customer/personal records;
- confidential production prompts not needed for public project research.

The standard live path reads public AI Open Source Radar data and does not need user documents or GitHub private-repository access.

## OAuth hosted identity

The final hosted MCP requires OAuth authorization.

The MCP verifies the access token against the configured authorization server and uses its verified issuer/subject for identity. Before identity crosses into AI Workstation entitlement/billing services, it is transformed into an opaque value:

```text
(issuer, subject) -> SHA-256 -> oidc_<opaque-id>
```

The product is designed so that:

- raw bearer tokens are not stored as entitlement IDs;
- raw OAuth subjects are not sent to the Premium model;
- raw OAuth subjects are not placed in payment checkout metadata;
- public Tool results do not include the raw subject/token;
- application rate limits use the opaque authenticated identity rather than a client-supplied username.

The authorization provider may independently process login/account data under its own privacy terms.

## Premium AI research

`deep_research_ai_projects` is an explicit hosted premium capability.

The publisher model receives only what is needed for the requested analysis:

- the user's Premium research task;
- bounded public Radar result context produced by rules-first retrieval;
- locale/focus needed to answer the request.

The model prompt must not contain:

- OAuth bearer tokens;
- raw OAuth subject;
- backend service credentials;
- Paddle customer/subscription IDs;
- private selector continuation tokens;
- internal publication/source hashes;
- private repository/customer documents unless a future product explicitly adds and discloses such a feature.

Premium model usage is recorded through the shared operational usage ledger with a privacy-preserving identity fingerprint. The current design does not require storing the raw OAuth subject in that model-usage event.

## Billing and payment data

The private entitlement backend may retain provider-side identifiers required for billing reconciliation, such as payment-provider customer/subscription IDs and event references.

These are private server data and are excluded from:

- public Radar APIs;
- MCP Tool results;
- Premium model prompts;
- OAuth entitlement IDs;
- public validation artifacts.

Checkout metadata uses the opaque entitlement ID rather than a raw OAuth subject.

The selected payment provider processes payment instrument, billing and tax information under its own terms. AI Open Source Intelligence should not handle raw card numbers itself.

## Service-to-service secrets

The hosted MCP uses a separate server credential when calling private Premium/billing backend endpoints. This credential is never intended for:

- browser JavaScript;
- Skill files;
- Tool output;
- OAuth claims;
- checkout custom data;
- logs/artifacts.

## Contract capture and release evidence

Public contract-capture tooling removes query/prompt text, client/request IDs, credential-like fields, raw content and internal publication identifiers before fixtures are retained for review.

Release artifacts are scanned for forbidden/private keys before upload. New Radar browse validation artifacts contain public navigation IDs/counts/snapshot metadata rather than private user requests.

## Logging and retention

The repository implements data minimization but does not yet declare final public-service retention periods.

Before broad hosted launch the publisher must publish final decisions for:

- OAuth/account identifier retention;
- entitlement/payment event retention;
- operational/security log retention;
- Premium model usage/evaluation retention;
- IP/user-agent handling at the gateway;
- deletion/export/correction channels;
- incident/security contact;
- subprocessors/hosting regions;
- whether any submitted data is used for model training.

Do not treat an unset retention policy as permission to keep data indefinitely.

## Local developer mode

Local `OSI_PROVIDER=mock` uses deterministic fixture data and performs no Radar network access.

Local `OSI_PROVIDER=http` sends the public project research/browse request needed to answer the task to the public Radar APIs. Local stdio mode does not contain the hosted OAuth/Paddle Premium flow.

## Public-service gate

The hosted candidate must not be described as a finished public paid service until real OAuth, payment sandbox, remote MCP security, final legal pages and retention/deletion processes have passed review.
