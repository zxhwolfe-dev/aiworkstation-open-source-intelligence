# Billing and entitlements

## Product rule

AI Open Source Intelligence does not charge for ordinary Radar browsing by secretly invoking a second server model.

```text
9 standard Radar tools
  -> no AI credit

1 hosted premium tool
  -> first successful task free
  -> then AI credits
```

The billing unit is a successful premium research task, not raw model tokens.

## Entitlement model

The private AI Workstation backend keeps a provider-neutral entitlement keyed by the opaque OAuth identity.

Public-safe fields include:

```text
plan: free | pro | enterprise
status: free | active | past_due | canceled | disabled
ai_credits: integer
trial_available: boolean
current_period_end: timestamp|null
upgrade_url: HTTPS URL
```

Payment-provider customer IDs and subscription IDs are private backend fields and are never returned in MCP tool results.

## Free trial

The one-time trial is server-side and atomic.

```text
new authenticated subject
  -> trial_available=true

first premium request
  -> reserve trial
  -> call publisher model
       | success -> trial remains consumed
       | failure -> reservation refunded
```

A model timeout or provider failure therefore does not consume the user's free attempt.

## Paid credits

After the trial:

```text
active Pro/Enterprise + enough credits
  -> reserve credit(s)
  -> call publisher model
       | success -> reservation remains consumed
       | failure -> exact reserved credits refunded
```

`past_due`, `canceled` and `disabled` subscriptions cannot spend existing credits until their status is restored according to product policy.

## Initial plan shape

The code intentionally keeps price outside source control. The initial hosted candidate uses a configurable monthly Pro allowance:

```text
GITHUB_AI_PRO_MONTHLY_CREDITS=50
```

Recommended launch structure to validate before fixing final pricing:

- Free: all standard Radar tools within rate limits + one successful Premium AI task;
- Pro: standard tools + monthly AI Research Credits;
- Enterprise: negotiated quotas/identity/support later.

Do not sell a second Pro subscription when an active Pro user simply exhausts monthly AI credits. If customer demand justifies it, add a separate one-time credit top-up product.

## Payment adapter boundary

Billing logic depends on the entitlement contract, not on Paddle classes. Paddle is the first adapter and can later coexist with another provider.

```text
Payment provider
  -> verified event adapter
  -> provider-neutral entitlement
  -> Hosted MCP
```

This allows a future domestic Alipay/WeChat or another international provider without rewriting MCP tools.

## Paddle checkout

The initial adapter creates a server-side recurring Pro transaction containing opaque custom data:

```text
mcp_subject=<opaque entitlement ID>
osi_product=ai_open_source_intelligence
plan=pro
```

No OAuth bearer token, raw OAuth subject or service secret is put into checkout custom data.

Checkout creation happens through the service-authenticated AI Workstation backend. The Hosted MCP returns only the public HTTPS checkout URL and product/credit metadata.

## Webhook verification

Webhook requests are public network endpoints but are not anonymously trusted.

The Paddle adapter:

1. reads the **raw** HTTP request body;
2. parses Paddle's timestamp/signature header;
3. checks timestamp tolerance;
4. calculates HMAC-SHA256 over the required timestamp/body payload;
5. uses constant-time comparison;
6. parses JSON only after signature verification;
7. maps only recognized product/price events to entitlements.

Invalid signature/body details are not echoed to the caller.

## What grants credits

Credits are provisioned/reset only from a recognized successful paid-period event. A subscription lifecycle notification by itself does not grant AI credits.

The adapter also checks that the completed transaction contains the configured Pro price.

This prevents unrelated Paddle transactions from granting plugin entitlements merely because they carry arbitrary custom data.

## Webhook replay protection

Payment events are idempotent at the database layer:

```text
(provider, event_id) = unique
```

The event claim and entitlement mutation occur in the same transaction. Replayed webhook delivery therefore cannot reset spent monthly credits or double-grant a period.

## Out-of-order events

Subscription lifecycle notifications can arrive after newer business state. The backend stores the latest provider `occurred_at` per subscription.

Rules:

- stale status events are processed as no-ops;
- an old `active` event cannot overwrite a newer `past_due` or `canceled` state;
- a later successful paid period may restore `active`;
- an older completed payment may still establish its paid-period allowance but cannot move subscription status backwards.

## Upgrade behavior

When Premium AI returns `UPGRADE_REQUIRED`:

### Free/unsubscribed user

The Hosted MCP may request a Pro checkout URL and surface it to the host/user.

### Active paid user with zero credits

Do **not** silently create another recurring subscription. Return the entitlement/period state and direct the user to the account/pricing surface. A future top-up offering must use a separate product/price and entitlement event type.

## Privacy

Billing records may contain payment-provider identifiers on the private server for reconciliation. Those identifiers are excluded from:

- public Radar APIs;
- MCP tool results;
- model prompts;
- OAuth entitlement IDs;
- public validation artifacts.

The publisher-model usage ledger uses a stable privacy-preserving identity fingerprint rather than the raw OAuth subject.

## Production gates

Before real-money launch:

- create and verify the merchant account;
- create the actual Pro product/recurring price;
- configure checkout domain and return behavior;
- configure webhook destination and secret;
- run sandbox purchase, renewal, payment failure and cancel tests;
- verify duplicate and out-of-order webhook handling with real provider events;
- publish final pricing, refund, tax, privacy and terms information;
- verify customer self-service/cancel path;
- decide final monthly credit allowance from observed model cost and usage.
