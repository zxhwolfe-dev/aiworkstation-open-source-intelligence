# Paddle setup for Premium AI credits

Paddle is the initial payment adapter for the international Hosted Plugin. Entitlement logic remains provider-neutral so another payment provider can be added later without changing MCP tools.

## Launch plan

The initial customer-facing plan is:

```text
Free
- nine live Radar tools
- standard Radar calls do not consume Premium AI credits
- one successful lifetime Premium deep-research trial

Pro
- US$12.99/month base price
- 50 Premium AI credits per successfully paid billing period
- one successful Premium deep-research task normally consumes 1 credit
- failed Premium model runs refund the reservation
- unused launch-plan credits do not roll over
```

The **actual recurring price is configured in Paddle** through `PADDLE_PRO_PRICE_ID`; the MCP protocol does not hard-code money. `GITHUB_AI_PRO_DISPLAY_PRICE_USD=12.99` controls website copy and must match the production Paddle price.

An active Pro user with zero remaining credits is **quota exhausted**, not a new sales opportunity. The backend rejects creation of a second recurring Pro subscription. If future demand justifies top-ups, add a separate one-time Paddle product/price and entitlement event rather than reusing the recurring subscription price.

## 1. Merchant/account setup

Complete Paddle merchant verification before production checkout. Use Paddle sandbox until the complete OAuth → free trial → checkout → webhook → paid-credit flow is proven.

Create one recurring product:

```text
Product: AI Open Source Intelligence Pro
Price: US$12.99 / month
Billing: recurring monthly
```

Paddle may display local currency, applicable tax, or equivalent amounts to buyers. The Paddle checkout page controls the final charged amount.

## 2. Backend environment

AI Workstation backend requires:

```text
PADDLE_ENV=sandbox
PADDLE_API_KEY=<server-only API key>
PADDLE_PRO_PRICE_ID=<recurring Pro price ID>
PADDLE_WEBHOOK_SECRET=<notification destination secret>
PADDLE_CHECKOUT_URL=https://aiworkstation.cn/githubai/pricing/
GITHUB_AI_PRO_MONTHLY_CREDITS=50
GITHUB_AI_PRO_DISPLAY_PRICE_USD=12.99
PADDLE_WEBHOOK_TOLERANCE_SECONDS=5
```

The dedicated private deployment template lives at:

```text
docs/ops/github_ai_radar/hosted-plugin-backend.env.example
```

Never expose the Paddle API key or webhook secret to browser JavaScript.

## 3. Checkout creation

When a Free user has already consumed the one-time Premium trial, the Hosted MCP requests a server-side recurring transaction containing:

```text
items: configured Pro price x1
collection_mode: automatic
custom_data:
  mcp_subject: <opaque OAuth entitlement ID>
  osi_product: ai_open_source_intelligence
  plan: pro
```

Only the opaque entitlement ID is placed in payment metadata. Do not put bearer tokens, raw WorkOS subjects, email addresses, or backend service tokens into Paddle custom data.

The Hosted MCP returns the HTTPS Paddle checkout URL to the model/client. The user explicitly opens the checkout in a browser. Premium tools never charge silently.

## 4. Webhook destination

Configure Paddle to deliver billing events to:

```text
https://aiworkstation.cn/api/v1/ai/githubai/mcp/paddle-webhook
```

If the production API prefix differs, verify the actual registered route before enabling production notifications.

The webhook route does not trust the Hosted-MCP service token as proof of payment. It validates the original Paddle-signed request body.

## 5. Signature verification

The adapter verifies:

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

Only a recognized `transaction.completed` event with the configured Pro price can provision/reset the monthly allowance.

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

It also records event timing so retries/stale lifecycle events cannot repeatedly add credits or overwrite a newer subscription state.

## 7. Customer cancellation, tax, and refunds

Customer-facing pages link to Paddle's current buyer policies.

Launch behavior:

- Pro renews automatically until canceled;
- buyers can manage/cancel through Paddle's Buyer Portal linked from Paddle payment/receipt email;
- cancellation generally takes effect at the end of the current paid billing period;
- Paddle handles localized checkout/tax treatment for the transaction;
- refunds are handled under applicable law and Paddle's Refund Policy;
- the product Terms do not reduce mandatory consumer rights.

Published URLs:

```text
https://aiworkstation.cn/githubai/pricing/
https://aiworkstation.cn/githubai/terms/
https://aiworkstation.cn/githubai/privacy/

https://useaistation.com/githubai/pricing/
https://useaistation.com/githubai/terms/
https://useaistation.com/githubai/privacy/
```

## 8. Sandbox acceptance

Use a fresh WorkOS test user and run the complete sequence:

1. authorize the Hosted MCP;
2. call standard Radar tools and verify Premium credits remain unchanged;
3. run the one-time free Premium task successfully;
4. second Premium call returns `upgrade_required` plus an HTTPS Paddle checkout URL;
5. complete sandbox payment;
6. receive a verified `transaction.completed` webhook;
7. entitlement becomes active Pro with 50 credits;
8. paid Premium call succeeds with `credit_source=paid_credits` and decrements exactly 1;
9. simulate a Premium model failure and verify the credit is refunded;
10. replay the same Paddle webhook and verify credits do not reset again;
11. simulate renewal and verify a new paid billing period resets allowance once;
12. spend all credits and verify `quota_exhausted` with no duplicate checkout;
13. simulate past due and verify paid credits cannot be spent;
14. simulate cancellation and stale out-of-order events;
15. send an invalid-signature webhook and verify no entitlement mutation.

## 9. Production switch

Only after sandbox acceptance:

1. complete Paddle production merchant verification;
2. create the matching production recurring product/price;
3. replace sandbox API key/price/webhook secret with production values;
4. set `PADDLE_ENV=production`;
5. verify website display price matches the production Paddle price;
6. make one low-risk real purchase/refund/cancellation test before broad launch.
