# Security Policy

## Supported status

AI Open Source Intelligence is pre-release. Security fixes target the latest `main` candidate unless a published release states otherwise.

The repository now contains a **public-hosted candidate architecture** with OAuth resource-server verification, per-user application limits, service-to-service backend authentication, provider-neutral Premium entitlements and a Paddle billing adapter on the private AI Workstation backend.

This code existing is **not** the same as a security approval for an Internet launch. Real OAuth, TLS, gateway, payment sandbox, revocation, logging/retention and platform review remain mandatory observed gates.

## Reporting a vulnerability

Do not open a public issue for vulnerabilities involving:

- OAuth token/issuer/audience/configured-scope verification bypass;
- access-token/refresh-token confusion;
- account/entitlement mix-up between users;
- backend service-token bypass;
- payment/webhook signature or replay bypass;
- duplicate subscription/credit corruption;
- credentials/tokens/private data;
- Host/origin/gateway bypass;
- prompt injection crossing a trust boundary;
- remote code execution or third-party repository execution;
- unsafe write behavior;
- data leakage from Radar responses/artifacts;
- false promotion of analysis/indirect evidence into verified facts;
- container/MCP isolation failures.

Until a dedicated security mailbox is published, use the private contact method on the AI Workstation website and include affected commit/version, reproduction, impact and deployment mode. Do not include real secrets/customer data/weaponized payloads that can harm third parties.

## Standard tool guarantees

The nine ordinary Radar tools are designed to be:

- read-only;
- non-destructive;
- idempotent with respect to product writes;
- unable to execute/install third-party repository code;
- fail-closed on required evidence/snapshot contracts;
- bounded by input/output contracts.

Hosted application limits are keyed by a verified opaque OAuth identity, not IP/raw access token/client-supplied username.

## Premium tool boundary

`deep_research_ai_projects` is different by design:

- non-destructive to GitHub/third-party/user content;
- **not** marked read-only/idempotent because a successful call consumes a free trial or AI credit;
- rules-first Radar retrieval occurs before publisher-model analysis;
- model failure refunds the reserved trial/credit;
- model narrative remains recommendation/analysis, not verified fact.

Do not change its annotations to “read-only” merely to make a platform review look simpler.

## OAuth boundary

Hosted MCP uses standard resource-server auth configuration with token verification. WorkOS AuthKit/Connect is the initial production provider.

It validates at least:

- active bearer token;
- access-token type when the introspection provider reports token type;
- exact configured issuer;
- subject/client identity presence;
- expiration when present;
- exact MCP resource/audience;
- any resource-server scopes only when they are explicitly configured for a provider that actually issues and exposes them.

For the documented WorkOS MCP flow, the exact Resource Indicator/audience is the primary authorization boundary and `OSI_OAUTH_REQUIRED_SCOPES` is empty. Do not invent a custom `osi:use` requirement that is absent from WorkOS's current authorization metadata/introspection contract.

The verifier sends `token_type_hint=access_token` and rejects an introspection result explicitly identifying the presented bearer credential as a refresh token. Missing issuer is rejected rather than inferred from local configuration.

The verified issuer+subject is transformed into an opaque entitlement ID before private backend/payment/model use.

Hosted access must fail closed when OAuth configuration or verification fails. Never add anonymous fallback to the same public endpoint.

## Backend service authentication

Premium/billing backend endpoints require a separate server credential in addition to the opaque authenticated user identity.

Knowing/guessing another user's entitlement ID must not be sufficient to use that entitlement.

Service credential requirements:

- high entropy;
- server-only environment secret;
- constant-time comparison;
- never in browser/Skill/Tool/payment metadata/log artifacts;
- rotatable independently from user OAuth.

## Payment security

The initial Paddle adapter must:

- create checkout server-side;
- place only opaque entitlement/product metadata in custom data;
- verify webhook raw body/signature/timestamp before processing JSON;
- require the configured Pro price before provisioning credits;
- enforce unique `(provider,event_id)` processing;
- handle out-of-order subscription lifecycle events;
- prevent replay from resetting spent credits;
- never expose payment provider IDs in public Tool output.

Real-money launch requires sandbox tests for purchase, renewal, failure, cancellation, duplicate delivery, stale delivery and invalid signature.

## Public Radar trust boundary

- public repository/web content is untrusted data;
- HTTP redirects away from configured origins are rejected;
- repository/public metadata is separated from editorial projections before `verified_facts`;
- license verification requires direct public License evidence;
- no missing license is inferred as permission;
- near matches are not promoted to formal matches;
- mixed snapshots fail closed.

## Hosted transport boundary

- local/default HTTP remains loopback-safe;
- non-loopback binds require explicit reverse-proxy/private-network acknowledgement and allowed Hosts;
- public hosted mode additionally requires OAuth and backend service auth;
- public MCP resource must be credential-free HTTPS `/mcp`;
- request bodies are bounded;
- browser CORS is enabled only with explicit narrow origins;
- example public compose maps the container back to host loopback and runs read-only/non-root with dropped capabilities.

## Rate-limit boundary

Initial hosted application rate limiting is in-process and suitable only for the documented single-process first deployment.

Do not horizontally scale the hosted MCP while claiming globally consistent per-user limits until the limiter moves to a shared transactional store.

Gateway/IP connection limits are defense-in-depth and do not replace OAuth-identity application quotas.

## Logging/secrets

Runtime telemetry must not accept user query, structured request body, raw OAuth subject, access token, backend service token, payment secrets or raw private request IDs as event fields.

Production gateway/security logs may contain additional network metadata; final retention/access/deletion policy must be documented before launch.

## Public launch security gates

Do not approve broad hosted launch until:

- current CI/live evidence passes;
- EN/ZH Radar browse validation passes;
- real WorkOS fresh-user login/revocation/wrong-resource/refresh-token rejection tests pass;
- optional configured-scope rejection is tested if a future provider enables that gate;
- public HTTPS MCP remote discovery shows exact intended tools/annotations;
- all nine ordinary tools work remotely;
- Premium first-free/refund/paid-credit behavior works remotely;
- payment sandbox end-to-end succeeds;
- gateway/application limits are observed;
- secret rotation/incident paths are documented;
- final privacy/terms/retention/support pages are published;
- target platform review is complete.
