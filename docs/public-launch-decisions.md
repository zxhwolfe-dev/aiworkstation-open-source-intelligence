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

### Rate-limit architecture

Initial public deployment is intentionally single-process with per-OAuth-identity application limits. Gateway connection/IP limits are defense-in-depth.

Horizontal scaling requires a shared limiter before claiming globally consistent user quotas.

### Payment architecture

Entitlements are provider-neutral. Paddle is the initial international billing adapter, with server-created checkout, signed webhook verification, replay protection and event ordering.

The initial code allowance is configurable (currently 50 monthly Pro AI credits by default). The actual price is not hard-coded in source control.

## Real decisions/configuration still required

### 1. Public MCP hostname

Choose/finalize the public resource URL, recommended shape:

```text
https://mcp.aiworkstation.cn/mcp
```

Then configure:

- DNS;
- TLS;
- Nginx/gateway;
- production allowed Hosts/origins;
- rollback/incident owner.

Once registered with a platform, treat the final resource URL as stable.

### 2. OAuth provider/account

Choose and configure the actual authorization provider/account.

A managed provider is preferred for the first release rather than building a custom authorization server.

Production must prove:

- fresh-user login/consent;
- correct resource/audience and `osi:use` scope;
- refresh/reconnect behavior;
- revocation/disabled-user behavior;
- wrong-scope/wrong-resource rejection;
- target platform compatibility.

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

## Required public launch sequence

1. current unit/CI suite green;
2. evidence-critical EN/ZH live validation green;
3. full Radar EN/ZH browse validation green;
4. deploy HTTPS Hosted MCP behind protected gateway;
5. configure real OAuth provider;
6. remote OAuth discovery + nine standard-tool smoke;
7. Paddle sandbox end-to-end;
8. Premium first-free / upgrade / paid / refund smoke;
9. revocation/rate-limit/secret/privacy review;
10. publish final pricing/legal/retention pages;
11. register final hosted MCP connection;
12. update Plugin with real connection identity;
13. fresh-install combined Plugin acceptance;
14. platform submission/review;
15. staged public rollout.

## Things that should not block early hosted sandbox testing

These can wait until sandbox/alpha proves demand:

- multi-region deployment;
- enterprise team workspace;
- saved project collections;
- write-capable MCP tools;
- multi-replica shared limiter;
- one-time credit top-ups;
- elaborate billing dashboard.
