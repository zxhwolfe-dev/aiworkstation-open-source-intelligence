# Public Launch Decisions

This document separates the free Hosted MCP milestone from future member/Premium commercialization.

## Resolved product decisions

### Public repository license

The public distribution repository uses Apache-2.0. Private AI Workstation databases, unpublished Radar data, private backend systems, credentials, payment accounts and trademarks are not made public merely because this client/distribution repository is open source.

### Default Hosted product shape

The first public Hosted surface is:

- three Skills;
- one public HTTPS Hosted MCP connection;
- nine standard live read-only Radar tools;
- no required login;
- no WorkOS dependency;
- no automated payment dependency;
- no Premium tool in default public mode.

```text
OSI_HOSTED_ACCESS_MODE=public
```

### Data/model cost boundary

Nine standard tools use public Radar data/retrieval and do not consume publisher-model AI quota.

A Premium publisher-model capability remains optional/future and must not be enabled as a real paid product until its entitlement and usage semantics are unified with AI Workstation membership.

### Membership architecture

AI Workstation membership is the intended source of truth across website and Skills/MCP entry points.

Do not create a second final OSI membership/credit system.

Current manual payment through existing WeChat/email/offline processes can continue. Automated payment is an optional future adapter.

### Identity architecture

The anonymous nine-tool Hosted service needs no user identity.

Before member-only/Premium capabilities are enabled, design a secure client-to-AI-Workstation-member linking flow. Standards-based OAuth is one possible transport. WorkOS is one optional OAuth provider, not a product dependency.

Reusable invite/activation codes must never be used directly as MCP bearer credentials or normal tool arguments.

### Rate-limit architecture

Default public deployment uses TLS plus gateway per-IP request and connection limits. The MCP upstream remains loopback-only.

The retained OAuth compatibility mode additionally has per-authenticated-subject application limits.

Horizontal scaling must revisit shared quota/rate-limit consistency before making global user-level guarantees.

### Payment architecture

Paddle or another provider may be introduced later as an automation adapter:

```text
verified payment event
  -> existing AI Workstation membership activation/renewal/update
```

The payment provider is not the membership source of truth.

The retained legacy OAuth/Premium compatibility code can represent trial/credit behavior, but that is not final commercial policy.

## Real configuration still required for free Hosted Private Alpha

### 1. Public MCP hostname

Canonical URL:

```text
https://mcp.aiworkstation.cn/mcp
```

Configure and verify:

- public DNS;
- valid TLS;
- Nginx routing;
- loopback-only port 8001 upstream;
- exact Host policy;
- gateway request/connection limits;
- rollback owner/procedure.

### 2. Candidate-bound deployment

The exact Hosted candidate SHA must be identical across:

- local candidate checkout;
- Docker build `OSI_IMAGE_COMMIT`;
- runtime `OSI_RELEASE_COMMIT`;
- remote MCP `serverInfo.version`.

Do not deploy a floating branch as formal evidence.

### 3. Public gateway abuse controls

The Nginx public Hosted contract must expose:

```text
X-OSI-Hosted-Gateway-Policy: tls-ip-rate-limited
```

on `/mcp` responses and configure bounded IP request/connection controls.

Port 8001 must not be Internet-addressable.

### 4. Hosted-service privacy/retention/legal

Before broad public promotion, review final service-specific:

- Privacy Policy;
- Terms of Service;
- support/security contact;
- abuse controls;
- operational logging/retention;
- deletion/correction process if user-linked data is later introduced;
- processors/hosting regions where relevant.

The anonymous nine-tool phase has materially less identity/billing data than the earlier OAuth/Paddle proposal, but final hosted-service statements still need review.

### 5. Platform connection registration

After the endpoint is stable:

1. register the actual hosted MCP connection;
2. obtain the real technical/connection identity;
3. test a fresh installation;
4. submit/publish through the relevant platform process when ready.

Never commit placeholder technical IDs.

## Hosted Private Alpha evidence sequence

Because this redesign creates a new candidate SHA, earlier `0249303e...` evidence remains valid historical evidence for that OAuth-oriented tree but cannot certify the new Hosted candidate.

For the **exact new candidate**:

1. obtain fresh Python 3.10/3.12 CI evidence;
2. obtain fresh EN/ZH live-validation evidence;
3. run fresh nine-standard-tool Codex acceptance and verify its ledger;
4. have a named human review the sanitized live artifact;
5. deploy the same candidate behind the canonical HTTPS/IP-rate-limited gateway;
6. run:

```bash
osi-remote-smoke \
  --profile hosted-public \
  --auth-mode none \
  --url https://mcp.aiworkstation.cn/mcp
```

7. require exact deployment identity;
8. discover exactly nine standard read-only tools and no Premium tool;
9. invoke one real standard read-only search;
10. feed candidate-bound artifacts into `osi-hosted-evidence-readiness --expected-access-mode public`;
11. require `hosted_private_alpha_ready=true`.

No WorkOS login or payment event is required for this milestone.

## Future member/Premium gates

Before enabling real member-only publisher-model capability:

1. design secure MCP-client-to-AI-Workstation-member linking;
2. prove active/expired/disabled membership behavior;
3. define one unified website + MCP AI usage/quota policy;
4. implement transactional usage reserve/commit/refund behavior;
5. update privacy/terms/support for linked member data;
6. run cost/latency/abuse tests;
7. decide whether automated payment is justified.

If OAuth is selected for the member bridge, then additionally verify the normal OAuth requirements, including exact Resource Indicator/audience. The existing compatibility configuration still keeps `OSI_OAUTH_REQUIRED_SCOPES` optional/provider-dependent; do not invent a mandatory provider-specific scope.

If WorkOS is selected, its Resource Indicator must be the exact MCP URL. If another provider is selected, apply the equivalent standard resource/audience boundary.

If Paddle or another payment provider is selected, complete merchant/product, webhook, replay, out-of-order, renewal, cancellation and refund testing before automated real-money launch.

## Things that should not block early free Hosted validation

- WorkOS account setup;
- Paddle merchant setup;
- automated checkout;
- Premium monthly credit economics;
- enterprise team workspace;
- multi-region deployment;
- saved project collections;
- write-capable MCP tools;
- multi-replica shared limiter;
- elaborate billing dashboards.
