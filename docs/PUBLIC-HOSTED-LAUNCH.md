# Public Hosted Plugin launch runbook

This is the single operational runbook for turning AI Open Source Intelligence into the final one-install product:

```text
one Plugin
  ├─ 3 Skills
  └─ Hosted MCP at https://mcp.aiworkstation.cn/mcp
       ├─ 9 standard live Radar tools
       └─ 1 Premium publisher-model research tool
```

Users install once and authorize once. They do not configure a database URL, API key, Python environment, or local MCP server.

## Product contract

### Standard live tools — Free product layer

```text
search_ai_projects
get_project_facts
get_license_evidence
compare_ai_projects
find_alternatives
compose_ai_stack
get_radar_overview
browse_radar_projects
browse_radar_skills
```

These tools read AI Workstation Radar data/indexes and do not consume Premium AI credits. Hosted request/rate limits still apply to prevent abuse.

`get_radar_overview` discovers the current ranking, collection, category and scenario dimensions. `browse_radar_projects` can then browse/filter the full project directory using ranking/collection/category/scenario/use-case/license/deployment and other public filters. `browse_radar_skills` exposes the public Skills library.

### Premium tool

```text
deep_research_ai_projects
```

- one successful task is free for a new entitlement identity;
- a failed model call refunds the trial/credit reservation;
- Pro launch plan: US$12.99/month, 50 Premium AI credits per paid billing period;
- one successful Premium task normally costs 1 credit;
- an active Pro account with no remaining credits receives `quota_exhausted`; no duplicate recurring subscription is created.

Premium uses a dedicated direct OpenAI API project/key and defaults to `gpt-5.6-terra`, low reasoning, 2,400 output-token cap, `store=false`, no web search, and no memory.

## Architecture

```text
ChatGPT / Codex / MCP host
          |
        OAuth
          |
   WorkOS AuthKit/Connect
          |
 https://mcp.aiworkstation.cn/mcp
          |
  OAuth token verification
  per-subject rate limiting
          |
  +-------+-------------------------------+
  |                                       |
9 live Radar tools                  Premium tool
  |                                       |
public Radar API                    private service boundary
https://aiworkstation.cn                   |
                                    entitlement / Paddle
                                    bounded public context
                                           |
                                    direct OpenAI API
```

The public MCP does not connect directly to the private database. Ordinary tools use the public validated Radar contract; Premium/billing operations cross a separate service-token-authenticated internal API boundary.

## Secret ownership

Never commit any value below.

### Public Hosted MCP secret environment

Use `compose.public-hosted.example.yml` as the source of truth.

Required production values:

```text
OSI_OAUTH_ISSUER_URL=<WorkOS AuthKit domain>
OSI_OAUTH_INTROSPECTION_URL=<WorkOS discovery/introspection endpoint>
OSI_OAUTH_CLIENT_ID=<WorkOS Connect client ID>
OSI_OAUTH_CLIENT_SECRET=<WorkOS Connect client secret>
OSI_OAUTH_RESOURCE_URL=https://mcp.aiworkstation.cn/mcp
OSI_OAUTH_REQUIRED_SCOPES=
OSI_OAUTH_INTROSPECTION_AUTH=body

OSI_BACKEND_SERVICE_TOKEN=<random shared service secret>
```

For the documented WorkOS MCP flow, the exact Resource Indicator/audience is the authorization boundary; do not invent a mandatory `osi:use` scope. `OSI_OAUTH_REQUIRED_SCOPES` remains available only for another provider that actually issues and exposes configured resource-server scopes.

Rate limits have safe defaults in the compose template and remain configurable.

### Private AI Workstation backend secret environment

Use the private `akaiagents` template:

```text
docs/ops/github_ai_radar/hosted-plugin-backend.env.example
```

The same random backend service secret is installed as:

```text
GITHUB_AI_MCP_SERVICE_TOKEN=<same value>
```

Additional private values:

```text
PADDLE_API_KEY
PADDLE_PRO_PRICE_ID
PADDLE_WEBHOOK_SECRET
GITHUB_AI_PRO_MONTHLY_CREDITS=50
GITHUB_AI_PRO_DISPLAY_PRICE_USD=12.99

GITHUB_AI_PREMIUM_MODEL_BASE_URL=https://api.openai.com/v1
GITHUB_AI_PREMIUM_MODEL_API_KEY=<dedicated OpenAI API project key>
GITHUB_AI_PREMIUM_MODEL=gpt-5.6-terra
```

Do not use the site's Codex/relay key for paid Premium research.

## DNS and TLS

Create:

```text
mcp.aiworkstation.cn
```

pointing to the production reverse proxy/server.

The public endpoint is exactly:

```text
https://mcp.aiworkstation.cn/mcp
```

The container itself remains loopback-only on the host, for example:

```text
127.0.0.1:8001 -> container:8000
```

Nginx/Caddy terminates TLS and proxies only the required MCP surface. Do not expose container port 8000 directly to the Internet.

## WorkOS

Follow `docs/AUTH-PROVIDER-SETUP.md`.

Minimum production configuration:

```text
Connect application: AI Open Source Intelligence
CIMD: enabled
Resource Indicator: https://mcp.aiworkstation.cn/mcp
```

Use the WorkOS authorization-server discovery document for issuer and introspection URLs; do not guess them. WorkOS binds MCP access tokens to the requested Resource Indicator through the `aud` claim.

Before broad launch, test revoked, expired and wrong-resource access tokens, plus direct refresh-token-as-bearer rejection. Test wrong-scope rejection only if a future provider explicitly enables resource-server scope enforcement.

## Paddle

Follow `docs/PADDLE-SETUP.md`.

Start in sandbox. Production plan:

```text
AI Open Source Intelligence Pro
US$12.99/month
50 Premium AI credits / paid billing period
```

Webhook destination:

```text
https://aiworkstation.cn/api/v1/ai/githubai/mcp/paddle-webhook
```

The exact route must be confirmed in production before enabling notifications.

## Public customer pages

Before enabling production payment, these must return HTTP 200 in both primary locales:

```text
https://aiworkstation.cn/githubai/pricing/
https://aiworkstation.cn/githubai/privacy/
https://aiworkstation.cn/githubai/terms/

https://useaistation.com/githubai/pricing/
https://useaistation.com/githubai/privacy/
https://useaistation.com/githubai/terms/
```

## Pre-deployment machine gates

### OSI public repository

```bash
python -m compileall -q src tests
python -m unittest discover -s tests -v
osi-validate-plugin --root .
osi-readiness --root .
```

Run Hosted-specific tests and config checks as part of the full suite.

### Private AI Workstation

Run the targeted Hosted-Premium suite plus the normal GitHubAI deployment tests, including:

```text
tests/test_github_ai_mcp_routes.py
tests/test_github_ai_checkout_policy.py
tests/test_github_ai_premium_model_adapter.py
tests/test_github_ai_hosted_pricing.py
tests/test_github_ai_hosted_legal.py
```

Then run the full relevant production smoke before enabling billing.

## Staging / sandbox acceptance

Use a fresh WorkOS test user.

1. connect the Hosted MCP from a real MCP host;
2. verify OAuth launches automatically — no pasted bearer token;
3. list exactly 10 hosted tools;
4. call `get_radar_overview`;
5. browse one ranking, one collection, one category/use case and the Skills library;
6. run the original six research/decision tools;
7. verify standard tools do not change Premium credits;
8. run one successful `deep_research_ai_projects` and verify `credit_source=free_trial`;
9. run Premium again and verify `upgrade_required` + HTTPS Paddle sandbox checkout;
10. complete sandbox checkout;
11. verify signed Paddle webhook activates Pro and sets 50 credits;
12. run Premium and verify `credit_source=paid_credits`, decrement by exactly one;
13. simulate model failure and verify refund;
14. replay the Paddle webhook and verify idempotency;
15. exhaust credits and verify `quota_exhausted` with no duplicate checkout;
16. hit standard and Premium rate-limit thresholds and verify model/backend work is blocked before cost is incurred;
17. revoke the WorkOS session/token and verify access fails;
18. verify expired/wrong-resource access tokens fail and a refresh token cannot be used directly as bearer; if provider-specific scopes are configured, verify a missing configured scope also fails;
19. verify public Pricing/Privacy/Terms in zh/en;
20. verify no raw OAuth token, raw OAuth subject, email, payment-card data, complete Premium prompt, or private backend token enters MCP result/telemetry artifacts.

Do not enable production Paddle until all sandbox acceptance steps pass.

## Production cutover

After staging/sandbox passes:

1. switch WorkOS to the production environment/domain/client;
2. switch Paddle to production merchant API key/price/webhook secret;
3. use a dedicated production OpenAI API project/key for Premium;
4. deploy Hosted MCP behind production TLS;
5. repeat 10-tool OAuth smoke using a fresh real account;
6. make one low-risk real Pro purchase, Premium call, cancellation and refund test;
7. monitor errors, rate-limit events, model cost and Paddle webhook processing;
8. register the final Hosted MCP with OpenAI;
9. obtain the real OpenAI connection technical ID;
10. only then add the final Plugin connection mapping (`.app.json` / platform-required manifest mapping) and validate a fresh one-install flow;
11. submit the combined Skills + MCP Plugin for review;
12. publish only after platform approval.

## Human/platform-only inputs

All code/deployment work can be completed by the engineering agents except for external-account actions that require the publisher/merchant owner:

- WorkOS account/environment ownership or business verification;
- Paddle merchant verification and creation/approval of the production recurring product/price;
- creation of the dedicated OpenAI API project/key and billing authorization;
- OpenAI publisher/business verification and final Hosted MCP/Plugin registration;
- final platform Submit/Publish confirmations.

Once those values/approvals exist, deployment and validation should be automated rather than performed manually by the publisher.
