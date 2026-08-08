# Public Hosted MCP rollout

This runbook describes the intended first public deployment of the one-install AI Open Source Intelligence product. It is a deployment plan, not a claim that the endpoint is already live.

## Target

Recommended public endpoint:

```text
https://mcp.aiworkstation.cn/mcp
```

The exact DNS name can change before registration. Once a hosted connection is registered with a platform, treat the final resource URL as a stable product identifier.

## Topology

```text
Internet / MCP hosts
      |
      | HTTPS
      v
Nginx / TLS gateway
      |
      | host loopback
      v
127.0.0.1:8001
      |
Docker: osi-mcp-hosted
      |
      +--> public AI Open Source Radar APIs
      |
      +--> OAuth token introspection
      |
      +--> service-authenticated AI Workstation premium backend
```

The container is not bound directly to the public host interface.

## Phase 1 — DNS and TLS

1. Create DNS for the final MCP hostname.
2. Issue a valid public TLS certificate.
3. Configure Nginx to proxy only the intended MCP path to `127.0.0.1:8001`.
4. Preserve the canonical public Host header.
5. Apply reasonable connection/body/time limits at the gateway.
6. Do not expose the AI Workstation backend service token through Nginx.

Example proxy shape:

```nginx
server {
    listen 443 ssl http2;
    server_name mcp.aiworkstation.cn;

    client_max_body_size 256k;

    location = /mcp {
        proxy_pass http://127.0.0.1:8001/mcp;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Forwarded-Proto https;
        proxy_read_timeout 180s;
        proxy_send_timeout 180s;
    }
}
```

Production Nginx should also use the site's standard TLS, logging, bot/abuse and incident controls.

## Phase 2 — OAuth provider

Configure a real OAuth provider that supports the MCP host's authorization flow and a standards-compliant resource-server/introspection path.

Hosted environment requires:

```text
OSI_OAUTH_ISSUER_URL
OSI_OAUTH_INTROSPECTION_URL
OSI_OAUTH_CLIENT_ID
OSI_OAUTH_CLIENT_SECRET
OSI_OAUTH_RESOURCE_URL=https://mcp.aiworkstation.cn/mcp
OSI_OAUTH_REQUIRED_SCOPES=osi:use
```

Do not launch until a fresh user can:

1. connect the MCP from the target host;
2. complete authorization without manually copying tokens;
3. receive a token whose issuer/resource/scope/subject pass validation;
4. call all nine standard tools;
5. revoke/disable the account/token and observe access being denied.

## Phase 3 — backend service boundary

Generate a random high-entropy server credential and configure the same secret in two places only:

```text
Hosted MCP:
  OSI_BACKEND_SERVICE_TOKEN

AI Workstation backend:
  GITHUB_AI_MCP_SERVICE_TOKEN
```

Never put it in:

- Skill files;
- Plugin listing;
- browser JavaScript;
- Paddle custom data;
- OAuth claims;
- GitHub Actions artifact output.

## Phase 4 — Paddle sandbox

Private AI Workstation backend requires the first billing adapter configuration:

```text
PADDLE_ENV=sandbox
PADDLE_API_KEY
PADDLE_PRO_PRICE_ID
PADDLE_WEBHOOK_SECRET
PADDLE_CHECKOUT_URL
PADDLE_CLIENT_SIDE_TOKEN      # only if the chosen checkout landing page needs Paddle.js
GITHUB_AI_PRO_MONTHLY_CREDITS=50
```

Run at least:

- first purchase;
- duplicate webhook replay;
- renewal;
- payment failure/past due;
- cancel;
- out-of-order old event after cancel;
- invalid signature;
- unrelated/wrong-price transaction.

Only a recognized completed paid transaction may provision/reset monthly AI credits.

## Phase 5 — application limits

Initial single-process defaults:

```text
standard tools: 60/minute, 300/hour per OAuth identity
premium tool:   5/minute per OAuth identity
```

The gateway can add IP/connection abuse limits, but application entitlements remain keyed by OAuth identity.

Before horizontal scaling, replace the in-process application limiter with a shared store. Do not run multiple replicas while claiming one globally consistent per-user quota.

## Phase 6 — preflight

Validate code/config before opening a socket:

```bash
OSI_PROVIDER=http \
...required env... \
osi-mcp-hosted --check-config
```

Validate compose:

```bash
docker compose -f compose.public-hosted.example.yml config
```

Then deploy behind the gateway and verify:

- process healthy;
- `/mcp` reachable only through HTTPS public origin;
- missing bearer token denied;
- invalid bearer denied;
- wrong scope/audience denied;
- valid OAuth connection succeeds;
- exact hosted tool set is 10;
- standard 9 tools are read-only/idempotent annotations;
- premium tool is non-destructive but non-read-only/non-idempotent;
- no auth/payment secret appears in logs/results.

## Phase 7 — real product acceptance

### Standard tools

Verify from ChatGPT/Codex or another intended MCP host:

- project search;
- project facts;
- license evidence;
- comparison;
- alternatives;
- stack composition;
- overview;
- rankings/collections/categories/scenarios browsing;
- Skills list/search/detail.

Run at least one Chinese and one English journey.

### Premium flow

With a fresh OAuth user:

1. call `deep_research_ai_projects`;
2. verify a usable result and `credit_source=free_trial`;
3. call again;
4. verify `upgrade_required` and a checkout link for an unsubscribed user;
5. complete sandbox purchase;
6. verify webhook provisioned the same opaque entitlement;
7. call Premium again without reconnecting/reinstalling;
8. verify `credit_source=paid_credits`;
9. force model failure and verify the reserved credit is refunded.

## Phase 8 — public service/legal

Before real-money/public directory launch publish final service-specific:

- privacy policy;
- terms/service conditions;
- pricing and credit semantics;
- refund/cancellation policy;
- data/log retention policy;
- support/security contact;
- incident communication path.

Repository alpha documents are engineering policies, not a substitute for final hosted-service terms.

## Phase 9 — platform registration

Only after the endpoint and OAuth identity are stable:

1. register the hosted MCP connection with the publishing platform;
2. capture the real connection/technical ID;
3. add the final Plugin MCP/app mapping to the package;
4. install from a fresh account;
5. repeat standard and premium acceptance;
6. submit the combined **Skills + MCP** product for review.

Do not commit placeholder connection IDs.
