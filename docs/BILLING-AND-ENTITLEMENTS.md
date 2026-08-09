# Billing and entitlements

## Current product rule

AI Open Source Intelligence does not own a second independent subscriber system.

The default Hosted MCP is free and anonymous:

```text
9 standard Radar tools
  -> public read-only data/retrieval
  -> no publisher-model token cost
  -> no WorkOS requirement
  -> no payment requirement
  -> no OSI credit balance
```

AI Workstation membership is the intended future source of truth for paid/member-only capabilities across both the website and Skills/MCP entry points.

See [`MEMBERSHIP-AND-MONETIZATION.md`](MEMBERSHIP-AND-MONETIZATION.md).

## Existing payment flow is valid

Automated billing is not required for Hosted Private Alpha or for selling AI Workstation membership.

The existing operational model can continue:

```text
manual payment / WeChat / email / offline contact
  -> operator activates or provides AI Workstation membership
  -> existing member role / validity / quota becomes the entitlement
```

This is a legitimate first-stage commercial workflow. Automation should be introduced only when payment volume or international demand justifies the extra complexity.

## Unified entitlement direction

Future Premium/member checks should read a narrow private AI Workstation membership contract rather than maintain an OSI-specific `free/pro/credits` truth source.

Conceptually:

```text
MCP client identity
  -> securely linked AI Workstation member
  -> member active/expired/disabled state
  -> member role/tier
  -> existing AI usage/quota policy
  -> allow or reject member-only operation
```

The public repository should not receive direct database credentials for the main AI Workstation member database.

## Unified quota direction

Do not present users with two unrelated balances such as:

```text
AI Workstation: 820,000 tokens remaining
OSI: 37 Premium credits remaining
```

when one membership already owns the AI usage policy.

The preferred future UX is one AI Workstation membership and one understandable AI usage policy. Member-only publisher-model work should be accounted through that policy once reservation/refund semantics are implemented safely.

Standard Radar browsing remains outside publisher-model token quota because it does not invoke the publisher-funded model.

## Identity is not billing

A client identity provider is only a way to establish which user/member is calling the service.

WorkOS, another OAuth provider, or a future first-party authorization service must not become a second membership source of truth.

A reusable AI Workstation invite/activation code must never be used directly as:

- an MCP bearer credential;
- an Authorization header value;
- a normal tool argument;
- a model-visible membership secret;
- a telemetry/evidence value.

Member proof/linking should happen on a reviewed first-party web surface or equivalent secure standards-based flow. The resulting MCP credential must be purpose-specific and revocable.

## Optional Paddle automation

Paddle is no longer a prerequisite or the assumed first-launch payment architecture.

If automated billing is added later, its role should be:

```text
Paddle / other payment provider
  -> cryptographically verified payment event
  -> AI Workstation membership activation/renewal/update
  -> same website + Skills/MCP entitlement
```

The payment provider is an adapter/automation layer, not the membership database.

A future adapter still requires the normal payment-safety properties:

- server-created checkout;
- signed webhook verification over the raw body;
- replay/idempotency protection;
- out-of-order event handling;
- exact product/price validation;
- reconciliation metadata kept private;
- cancellation/refund/customer-service behavior documented.

These are future Public Launch/commercial gates, not anonymous Hosted Private Alpha gates.

## Existing OAuth/Premium compatibility code

The repository currently retains an explicit OAuth Hosted compatibility mode and `deep_research_ai_projects` contract. Its legacy trial/AI-credit behavior is retained so completed engineering work is not destroyed, but it is **not the final commercial policy** and is not enabled by default.

```text
OSI_HOSTED_ACCESS_MODE=oauth
```

Before that mode is used for real paid service, replace/bridge its entitlement semantics with the unified AI Workstation membership/quota contract and complete dedicated migration tests.

Do not sell or advertise the retained `50 monthly credits` behavior as final product policy merely because old compatibility code can represent it.

## Production commercial gates

Before enabling any real member-only publisher-model capability:

- design a secure MCP-client-to-AI-Workstation-member linking flow;
- prove disabled/expired member revocation;
- define how website and MCP model usage share the existing quota;
- implement transactional reserve/commit/refund semantics for model usage;
- prevent repeated invite/member-secret reuse as authentication;
- publish member/Premium privacy, support and retention behavior;
- test real cost/latency and choose sustainable limits;
- only then decide whether automated billing is necessary.

If automated billing is later enabled, additionally complete sandbox purchase/renewal/failure/cancel/refund/replay/out-of-order tests before accepting real money through the automated path.
