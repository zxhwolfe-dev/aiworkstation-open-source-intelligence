# Public Launch Decisions

This document separates product decisions already made in code from real external/account/production decisions that still block a broad hosted launch.

## Resolved product decisions

### Public repository license

The public distribution repository uses Apache-2.0. Private AI Workstation databases, unpublished Radar data, private backend systems, credentials, payment accounts and trademarks are not made public merely because this client/distribution repository is open source.

### Final product shape

The intended public product is **one Plugin installation** containing:

- three Skills;
- one OAuth-protected hosted MCP connection;
- nine standard live Radar tools;
- one explicit Premium AI tool.

Skills-only remains a developer/degraded mode, not the desired final user experience.

### Data/model cost boundary

Nine standard tools use public Radar data/retrieval and do not consume publisher AI credits.

`deep_research_ai_projects` is the explicit publisher-model premium capability:

- first successful task free;
- later tasks consume AI credits;
- model failure refunds the reservation;
- premium narrative stays recommendation/analysis.

### Identity architecture

Hosted MCP uses standard OAuth resource-server verification. Verified issuer+subject is transformed into an opaque entitlement ID before private backend/payment/model use.

A separate service credential authenticates Hosted MCP to private AI Workstation Premium/billing endpoints.

WorkOS AuthKit/Connect is the initial authorization provider. The exact Hosted MCP Resource Indicator/audience is the primary access boundary. Custom required scopes remain optional/provider-dependent rather than inventing a WorkOS-only `osi:use` scope that AuthKit does not currently advertise in its MCP authorization metadata.

### Rate-limit architecture

Initial public deployment is intentionally single-process with per-OAuth-identity application limits. Gateway connection/IP limits are defense-in-depth.

Horizontal scaling requires a shared limiter before claiming globally consistent user quotas.

### Payment architecture

Entitlements are provider-neutral. Paddle is the initial international billing adapter, with server-created checkout, signed webhook verification, replay protection and event ordering.

The initial code allowance is configurable (currently 50 monthly Pro AI credits by default). The actual price is not hard-coded in source control.

## Real decisions/configuration still required

### 1. Public MCP hostname

The intended canonical resource URL is:

```text
https://mcp.aiworkstation.cn/mcp
```

Before treating it as live, configure and verify:

- public DNS;
- valid TLS;
- Nginx/gateway routing;
- production allowed Hosts/origins;
- rollback/incident owner.

Once registered with a platform, treat the final resource URL as stable because OAuth Resource Indicators and platform connection identities bind to it.

### 2. WorkOS OAuth provider/account

Configure the production WorkOS AuthKit/Connect environment rather than building a custom authorization server for the first release.

Production/private-alpha validation must prove:

- Client ID Metadata Document (CIMD) is enabled for modern MCP clients;
- Dynamic Client Registration (DCR) is enabled where validator/legacy-client compatibility is required;
- the exact `https://mcp.aiworkstation.cn/mcp` Resource Indicator is configured;
- fresh-user login/consent succeeds;
- issued access-token `aud` matches the exact resource;
- unauthenticated MCP access receives a Bearer 401 + RFC 9728 resource-metadata challenge;
- refresh/reconnect behavior works for clients that request offline access;
- revocation/disabled-user behavior fails closed;
- wrong-resource tokens are rejected;
- any explicitly configured provider scope is enforced;
- the actual target MCP host is compatible.

For WorkOS, `OSI_OAUTH_REQUIRED_SCOPES` should remain empty unless the chosen WorkOS configuration explicitly provides a custom scope in introspection. Resource/audience binding is mandatory either way.

### 3. Paddle merchant/product

Complete merchant verification and create the actual recurring Pro product/price.

Configure real/sandbox values:

```text
PADDLE_API_KEY
PADDLE_PRO_PRICE_ID
PADDLE_WEBHOOK_SECRET
PADDLE_CHECKOUT_URL
```

Run the full sandbox purchase/renewal/failure/cancel/replay/stale-event suite before production.

### 4. Final price and credit economics

Decide after measuring real Premium model cost/latency and early usage:

- monthly Pro price;
- monthly AI-credit allowance;
- credit cost for future larger reports;
- whether to offer one-time top-up credits;
- enterprise pricing/support.

Do not sell a duplicate recurring subscription merely because an active Pro user exhausts monthly credits.

### 5. Hosted-service privacy/retention/legal

Publish final service-specific:

- Privacy Policy;
- Terms of Service;
- pricing/credit semantics;
- cancellation/refund policy;
- support/security contact;
- OAuth/account retention;
- entitlement/payment-event retention;
- model usage/log retention;
- deletion/export/correction process;
- processors/hosting regions;
- training/evaluation-data policy.

Repository pre-release policies are not a substitute for final real-money hosted-service terms.

### 6. Platform connection registration

Only after endpoint/OAuth are stable:

1. register the real hosted MCP connection;
2. obtain the actual technical/connection ID;
3. add the real Plugin mapping;
4. test a fresh installation;
5. submit the combined Skills + MCP Plugin.

Never commit placeholder technical IDs.

## Hosted Private Alpha evidence sequence

The private-alpha gate is intentionally evidence-first rather than based on operator booleans:

1. keep the already-reviewed External Alpha CI/live/Codex/human evidence for the Hosted candidate;
2. deploy the candidate behind the canonical HTTPS gateway;
3. configure WorkOS AuthKit/Connect and the exact MCP Resource Indicator;
4. run `osi-remote-smoke --profile hosted --auth-mode oauth` from the same candidate checkout;
5. require a Bearer 401 challenge + protected-resource metadata before authenticated access;
6. discover exactly nine standard tools plus the Premium tool;
7. invoke one standard read-only search over authenticated MCP;
8. feed that sanitized report into `osi-hosted-evidence-readiness`;
9. require `hosted_private_alpha_ready=true` before inviting hosted testers.

This does not invoke the Premium model and therefore does not consume a trial/credit during ordinary Hosted Private Alpha connectivity validation.

## Required public launch sequence

1. current unit/CI suite green;
2. evidence-critical EN/ZH live validation green;
3. full Radar EN/ZH browse validation green;
4. deploy HTTPS Hosted MCP behind protected gateway;
5. configure real WorkOS OAuth provider;
6. remote OAuth discovery + authenticated 9-standard + 1-Premium tool discovery + standard-tool smoke;
7. obtain evidence-first Hosted Private Alpha readiness;
8. Paddle sandbox end-to-end;
9. Premium first-free / upgrade / paid / refund smoke;
10. revocation/rate-limit/secret/privacy review;
11. publish final pricing/legal/retention pages;
12. register final hosted MCP connection;
13. update Plugin with real connection identity;
14. fresh-install combined Plugin acceptance;
15. platform submission/review;
16. staged public rollout.

## Things that should not block early hosted sandbox testing

These can wait until sandbox/alpha proves demand:

- multi-region deployment;
- enterprise team workspace;
- saved project collections;
- write-capable MCP tools;
- multi-replica shared limiter;
- one-time credit top-ups;
- elaborate billing dashboard.
