# Billing and entitlements

## Current product: no billing boundary is involved

AI Open Source Intelligence `0.2.x` exposes one unified Skill plus nine anonymous, read-only Radar data/evidence tools.

```text
9 standard Radar tools
  -> public data/retrieval
  -> use_model=false for requirement selection
  -> no AI Workstation server-model token cost
  -> no login required
  -> no payment required
  -> no Premium credit balance
```

There is no runnable `deep_research_ai_projects` tool, OAuth Hosted mode, checkout path or OSI-specific credit ledger in the current Hosted product.

## Existing AI Workstation membership remains separate

The main AI Workstation website already has its own member identity and AI-token quota policy. That system continues to govern website model features.

The nine data-only MCP tools must **not** consume or deduct the website's 100k/1m daily model-token quotas, because those tools do not invoke the website model.

Do not create a fake token charge merely to make MCP usage look like website model usage.

## Future paid/server-model direction

If AI Workstation later adds a member-only server-model capability for Skills/MCP, AI Workstation membership should be the single entitlement source of truth.

Conceptually:

```text
MCP client identity
  -> securely linked AI Workstation member
  -> existing member status / role
  -> existing AI usage and quota policy
  -> allow/reject explicit server-model operation
```

Do not create a second unrelated OSI `free/pro/50 credits` membership system.

## Existing manual payment remains valid

The existing commercial workflow can continue for AI Workstation membership:

```text
manual payment / WeChat / email / offline contact
  -> operator provides or activates AI Workstation membership
  -> existing member validity and quota apply
```

Automated checkout is not required to operate the current data-only Skill/MCP product.

## Identity is not billing

A future identity provider would only prove which user is calling the service. It must not become a second subscription database.

A reusable AI Workstation invite/activation code must never be used directly as:

- an MCP bearer credential;
- an Authorization header value;
- a normal MCP tool argument;
- a model-visible membership secret;
- a telemetry/evidence identifier.

Future membership linking should happen through a reviewed first-party or standards-based flow and produce a purpose-specific, revocable credential.

## Optional payment automation later

If Paddle, WeChat Pay, Alipay or another automated provider is added later, its role should be:

```text
payment provider
  -> verified payment event
  -> AI Workstation membership activation/renewal/update
  -> same website + future member-linked MCP entitlement
```

The payment provider is an automation adapter, not the membership source of truth.

## Required gates before any future server-model feature

A future version that executes AI Workstation server inference must have a fresh product/release review and must:

- explicitly expose that server-model execution is occurring;
- link callers safely to existing AI Workstation membership;
- prove disabled/expired-member revocation;
- account real model usage through the existing AI usage/quota system;
- implement reservation/commit/refund semantics where necessary;
- publish the relevant privacy/retention/support behavior;
- measure real model cost and latency;
- receive a fresh candidate-bound evidence chain before deployment.

None of these future gates should be smuggled back into `0.2.x` through an environment-variable switch.
