# Membership and Monetization Boundary

## Product decision

AI Workstation Open Source Intelligence does **not** own a second independent subscription system.

AI Workstation membership is the intended source of truth for future paid/member capabilities across the website and Skills/MCP entry points.

The initial Hosted MCP remains simple:

```text
Free Hosted MCP
  -> no login
  -> nine read-only Radar tools
  -> no Premium model execution
  -> no checkout
  -> no separate OSI credits
```

## Existing AI Workstation commercial flow can remain manual

Automated card billing is not required to launch the free Skills/MCP surface or to continue selling AI Workstation membership.

The existing business process can remain:

```text
user contacts AI Workstation
  -> payment is handled manually (for example WeChat/email/offline)
  -> AI Workstation activates/provides membership
  -> the AI Workstation membership system owns role, validity and quota
```

A future payment provider such as Paddle may automate payment and activation, but it must update the same membership source of truth rather than create a second OSI-specific subscriber database.

## Unified entitlement model

Future member-only Skills/MCP capabilities should ask a narrow private AI Workstation membership service questions such as:

```text
Who is this linked member?
Is the membership active?
What member tier/role applies?
What AI usage policy applies?
Can this Premium operation reserve/consume usage?
```

The Hosted open-source repository should not need direct access to the main website database.

The website and MCP become two entry points to the same member entitlement:

```text
                    AI Workstation membership
                              |
                  +-----------+-----------+
                  |                       |
             website usage           Skills / MCP
                  |                       |
                  +-----------+-----------+
                              |
                     unified AI usage policy
```

## Token/quota direction

Do not introduce an unrelated `50 Premium credits/month` ledger by default when AI Workstation already has a token-based AI usage policy.

The preferred future direction is to account member-only model work against the unified AI Workstation usage policy. Exact reservation/refund semantics must be implemented transactionally before Premium launch, but the product should present one membership/quota concept rather than two unrelated balances.

Standard Radar tools do not call the publisher-funded Premium model and therefore should not consume AI model token quota merely for deterministic public-data browsing.

## Identity is separate from membership

An MCP client still needs a secure way to prove which AI Workstation member it belongs to before member-only capabilities can be enabled.

That identity bridge is not itself the membership database.

Possible future implementations include:

- a standards-based OAuth authorization server linked to AI Workstation membership;
- a replaceable external OAuth provider mapped to AI Workstation membership;
- another reviewed secure first-party member-link flow that does not expose reusable membership secrets to the model.

WorkOS is one optional OAuth provider. It is not required for the anonymous nine-tool Hosted MCP and must not become the source of truth for paid membership.

## Invite/member secret safety

A reusable invite or activation code must **never** be used directly as:

- an MCP bearer token;
- an `Authorization` header value sent by a model;
- a normal MCP tool argument;
- a value stored in evidence reports, telemetry, logs, prompts, or public configuration.

When member linking is implemented, the user should complete the sensitive membership proof on a first-party AI Workstation web surface. The MCP client should receive only a revocable, purpose-specific identity/session credential or standards-based OAuth token after successful linking.

## Hosted access modes

### `public` — default

```text
OSI_HOSTED_ACCESS_MODE=public
```

- nine standard read-only Radar tools;
- anonymous;
- no WorkOS/OAuth dependency;
- no Premium tool;
- no payment dependency;
- Nginx IP/request/connection abuse controls required.

### `oauth` — compatibility/future mode

```text
OSI_HOSTED_ACCESS_MODE=oauth
```

- nine standard tools plus the current Premium tool contract;
- standards-based OAuth identity;
- private backend required;
- per-subject application limits;
- authorization provider is replaceable.

OAuth mode is retained to avoid throwing away completed standards work, but it is not the default commercial identity design until AI Workstation member linking is finalized.

## Rollout plan

### Phase 1 — free Hosted Skills/MCP

Ship the nine read-only Radar tools with `public` mode. Validate real clients, latency, abuse controls, data quality, discovery and adoption.

### Phase 2 — unified AI Workstation member bridge

Design and test a secure client-to-member binding flow. Reuse the existing AI Workstation membership/role/quota source of truth. Do not automate payment yet unless demand justifies it.

### Phase 3 — member-only Premium model capability

Enable Premium only after identity binding and unified quota accounting are complete. Failed model work must not consume final quota as if it succeeded; reservation/refund behavior must be explicit and tested.

### Phase 4 — optional billing automation

If manual payment becomes operationally expensive, add Paddle or another provider as an **automation adapter**:

```text
payment provider
  -> verified payment event
  -> update existing AI Workstation membership
```

The payment provider is not the membership source of truth.

## Non-goals

- charging for the open Skill text itself;
- hiding the open-source Skill files behind payment;
- maintaining separate website and MCP memberships;
- requiring WorkOS for free public tools;
- requiring Paddle before product-market demand exists;
- exposing invitation/member secrets to ChatGPT, Codex, other MCP hosts, logs or model context.
