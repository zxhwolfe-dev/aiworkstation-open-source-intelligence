# Paddle setup for Premium AI credits

Paddle is the first payment adapter for the international hosted product. Entitlement logic remains provider-neutral so another provider can be added later without changing MCP tools.

## 1. Merchant/account setup

Complete Paddle merchant verification before relying on production checkout. Use sandbox until the complete product flow is proven.

Create one recurring **AI Open Source Intelligence Pro** product/price for the initial subscription plan.

The product price itself is configured in Paddle, not hard-coded in the repository. The application maps the configured Paddle price ID to the Pro entitlement.

## 2. Backend environment

AI Workstation backend requires:

```text
PADDLE_ENV=sandbox
PADDLE_API_KEY=<server-only API key>
PADDLE_PRO_PRICE_ID=<recurring Pro price ID>
PADDLE_WEBHOOK_SECRET=<notification destination secret>
PADDLE_CHECKOUT_URL=<approved HTTPS checkout/default-payment-link page>
GITHUB_AI_PRO_MONTHLY_CREDITS=50
PADDLE_WEBHOOK_TOLERANCE_SECONDS=5
```

If the selected checkout landing page uses Paddle.js, configure its public client-side token separately. Never expose the API key or webhook secret to browser JavaScript.

## 3. Checkout creation

The backend creates a server-side recurring transaction containing:

```text
items: configured Pro price x1
collection_mode: automatic
custom_data:
  mcp_subject: <opaque OAuth entitlement ID>
  osi_product: ai_open_source_intelligence
  plan: pro
```

Only the opaque entitlement ID is placed in payment metadata. Do not put bearer tokens/raw OAuth subjects/backend service tokens into custom data.

## 4. Webhook destination

Configure Paddle to deliver required billing events to the public AI Workstation billing webhook path created for the hosted MCP integration.

The route does not accept the MCP service token as proof of payment. It validates Paddle's signed webhook body.

## 5. Signature verification

The adapter verifies the original raw request body before JSON parsing:

```text
Paddle-Signature timestamp + signature
    |
HMAC-SHA256 over timestamp:rawBody
    |
constant-time comparison
    |
timestamp tolerance
```

Changing whitespace/body bytes before signature verification invalidates the signature.

## 6. Entitlement events

### Grant/reset monthly credits

Only a recognized completed transaction with the configured Pro price can provision/reset the monthly Pro AI-credit allowance.

### Subscription lifecycle

Subscription events synchronize states such as:

```text
active
past_due
canceled
disabled
```

They do not independently manufacture monthly AI credits.

### Replay and ordering

The database enforces unique payment events:

```text
(provider, event_id)
```

It also records the latest provider event time per subscription so stale lifecycle events cannot overwrite newer state.

## 7. Sandbox acceptance

Use a fresh OAuth test user and run the full sequence:

1. consume the one-time free Premium AI task;
2. second Premium call returns upgrade state;
3. create checkout;
4. complete sandbox payment;
5. receive verified completed-transaction webhook;
6. entitlement becomes Pro with configured monthly credits;
7. Premium call succeeds with `paid_credits`;
8. replay the same webhook and confirm credits do not reset again;
9. send/observe renewal and confirm a new billing period resets allowance once;
10. simulate past due and verify credits cannot be spent;
11. simulate recovery payment and verify active status returns;
12. simulate cancellation;
13. deliver an older active event after cancellation and verify it is ignored;
14. send invalid-signature payload and verify no entitlement mutation occurs.

## 8. Customer-facing policy

Before production payment is enabled, publish:

- actual subscription price/currency behavior;
- monthly AI-credit allowance;
- what one credit buys;
- renewal behavior;
- cancellation method;
- refund policy;
- tax/billing statement information;
- support contact.

## 9. Exhausted active subscription

An active Pro user who consumes all monthly AI credits must not automatically be sent through another recurring Pro subscription checkout.

Initial behavior should be:

```text
active Pro + 0 credits
  -> monthly quota exhausted
  -> show current period/end and account/pricing help
```

If demand exists, introduce a separate one-time credit top-up product with its own price ID and entitlement event. Do not reuse the recurring Pro price as a top-up.
