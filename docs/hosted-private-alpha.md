# Hosted Private Alpha Runbook

This runbook takes a reviewed source candidate from repository/External-Alpha quality gates to a real public Hosted MCP deployment while deliberately keeping the first Hosted surface **free, anonymous, and read-only**.

Canonical endpoint:

```text
https://mcp.aiworkstation.cn/mcp
```

Default access mode:

```text
OSI_HOSTED_ACCESS_MODE=public
```

Public mode exposes exactly the nine standard Radar tools. It does not load OAuth/WorkOS configuration, does not load a Premium/member backend, and does not expose `deep_research_ai_projects`.

OAuth remains an optional compatibility/future-member mode, not a prerequisite for the free Hosted MCP.

## 0. Release invariant: one candidate, one evidence chain

Freeze a Hosted candidate commit before external deployment validation.

All of these must refer to that exact Git SHA:

- Python 3.10/3.12 CI evidence;
- EN/ZH live-validation evidence;
- Codex acceptance report + ledger;
- human review of that candidate's sanitized live artifact;
- deployed Hosted MCP `serverInfo.version` identity;
- Hosted remote MCP evidence.

The deployment must receive the exact 40-character candidate SHA through:

```text
OSI_RELEASE_COMMIT=<exact-hosted-candidate-sha>
```

The same SHA is baked into the Docker image as `OSI_IMAGE_COMMIT`. Hosted startup fails when image/runtime identities differ. The MCP exposes the non-secret identity in `serverInfo.version` as `0.1.0+git.<sha>` and remote evidence requires `deployment_commit` to match the candidate.

## 1. Candidate code gates

For the Hosted candidate:

1. merge only reviewed Hosted changes;
2. require repository CI green on Python 3.10 and 3.12;
3. require candidate-bound `ci-evidence.json`;
4. require candidate-bound bilingual `live-contract-validation` artifact;
5. run `osi-codex-acceptance` from a clean checkout of that exact SHA;
6. review the sanitized live artifact and record the human reviewer.

`external_alpha_ready` must be true for the Hosted candidate before infrastructure evidence is added.

## 2. DNS

Create the DNS record for:

```text
mcp.aiworkstation.cn
```

Point it at the intended HTTPS gateway. Do not expose the MCP container port directly in DNS or firewall rules.

Verify:

```bash
getent ahosts mcp.aiworkstation.cn
```

and, when available:

```bash
dig +short A mcp.aiworkstation.cn
dig +short AAAA mcp.aiworkstation.cn
```

## 3. TLS and Nginx gateway

The repository provides:

```text
deploy/nginx/mcp.aiworkstation.cn.conf.example
```

Topology:

```text
Internet
  |
  | HTTPS 443
  v
Nginx TLS + IP abuse controls
  |
  | loopback only
  v
127.0.0.1:8001
  |
  v
Hosted MCP container :8000
```

Public-mode requirements:

- valid TLS certificate for `mcp.aiworkstation.cn`;
- HTTP redirects to HTTPS except ACME challenge handling;
- container port `8001` is loopback-only;
- `/mcp` is the only functional MCP application path;
- request/response buffering stays disabled for MCP streaming;
- per-IP request limiting and connection limiting are active;
- request body is bounded;
- successful and error responses from `/mcp` include:

```text
X-OSI-Hosted-Gateway-Policy: tls-ip-rate-limited
```

- unrelated paths return 404.

The OAuth protected-resource metadata locations remain narrowly proxied for the optional OAuth mode. In public mode they are not required to return successful OAuth metadata.

Before reload:

```bash
sudo nginx -t
```

## 4. Public mode has no WorkOS requirement

For Hosted Private Alpha, do **not** create a WorkOS dependency just to serve the nine free tools.

The following are not required in public mode:

```text
OSI_OAUTH_ISSUER_URL
OSI_OAUTH_INTROSPECTION_URL
OSI_OAUTH_CLIENT_ID
OSI_OAUTH_CLIENT_SECRET
OSI_BACKEND_SERVICE_TOKEN
```

They may be absent or empty.

The product boundary is intentional:

```text
public Hosted MCP
  -> nine read-only Radar tools
  -> no login
  -> no Premium model execution
  -> no subscription/credit/checkout state
```

## 5. Server environment

Minimum production environment:

```text
OSI_RELEASE_COMMIT=<exact-40-character-hosted-candidate-sha>
OSI_HOSTED_ACCESS_MODE=public
```

The Compose definition already supplies the live Radar provider/origin and bounded HTTP settings.

Generate the candidate value from the checkout rather than typing it from memory:

```bash
printf 'OSI_RELEASE_COMMIT=%s\n' "$(git rev-parse HEAD)"
```

## 6. Preflight without opening the service

Render the Compose configuration and run the application self-check.

Expected `osi-mcp-hosted --check-config` fields include:

```text
mode=hosted-public
access_mode=public
tool_count=9
premium_enabled=false
gateway_abuse_control=required-ip-rate-limit
release_commit=<exact candidate>
```

The output must not require or print OAuth secrets, backend tokens, or payment credentials.

## 7. Start the Hosted MCP

Use the candidate-bound public Hosted Compose definition.

Confirm the host listens only on:

```text
127.0.0.1:8001
```

A public `0.0.0.0:8001` or `[::]:8001` binding is a deployment failure.

## 8. Public gateway boundary

From an external network verify HTTPS reachability and the gateway policy header.

A simple GET to `/mcp` may return a non-success MCP method/status; that is acceptable. The formal boundary is that the request reaches the intended HTTPS gateway and the response carries:

```text
X-OSI-Hosted-Gateway-Policy: tls-ip-rate-limited
```

Do not try to trigger rate-limit exhaustion in production as part of normal evidence generation. The Nginx configuration and header contract establish the configured edge policy; normal operational monitoring can validate 429 behavior separately.

## 9. Formal public Hosted smoke

Run from a clean checkout of the exact Hosted candidate SHA:

```bash
source .venv/bin/activate

osi-remote-smoke \
  --root . \
  --url https://mcp.aiworkstation.cn/mcp \
  --profile hosted-public \
  --auth-mode none \
  --locale en \
  --output tmp/hosted-remote.json
```

Required result:

- `ok=true`;
- report `commit` = exact local Hosted candidate SHA;
- report `deployment_commit` = same SHA from remote `serverInfo.version`;
- `deployment-identity` = passed;
- gateway boundary = passed;
- auth mode = `none`;
- exactly nine standard Radar tools discovered;
- all nine advertise read-only/non-destructive/idempotent annotations;
- `deep_research_ai_projects` is absent;
- real public `search_ai_projects` succeeds;
- negotiated MCP protocol version is recorded.

A mismatch between local and deployed commit is a hard failure.

## 10. Final evidence-first Hosted readiness

Once fresh candidate CI/live/Codex/human evidence exists and `tmp/hosted-remote.json` is green:

```bash
osi-hosted-evidence-readiness \
  --root . \
  --ci-evidence /ABS/PATH/HOSTED/ci-evidence.json \
  --live-validation-evidence /ABS/PATH/HOSTED/validation-evidence.json \
  --codex-acceptance-report /ABS/PATH/HOSTED/codex-acceptance.json \
  --hosted-remote-evidence /ABS/PATH/HOSTED/hosted-remote.json \
  --artifact-reviewed \
  --reviewer "REVIEWER NAME" \
  --expected-base-url https://aiworkstation.cn \
  --expected-hosted-mcp-url https://mcp.aiworkstation.cn/mcp \
  --expected-access-mode public \
  --output tmp/hosted-private-alpha-readiness.json
```

Success means:

```text
code_ready=true
external_alpha_ready=true
hosted_private_alpha_ready=true
public_launch_ready=false
```

## 11. AI Workstation membership is the future entitlement source

Do not create a second unrelated OSI subscription/credit identity just because Skills/MCP is a new entry point.

Future paid/member capabilities should map to the existing AI Workstation membership source of truth. The Hosted project should consume a narrow private membership contract rather than owning payment state itself.

Target product model:

```text
AI Workstation member
  -> existing member/invite identity and role
  -> existing AI usage/quota policy
  -> website entry point
  -> Skills/MCP entry point
```

The free nine-tool Hosted surface remains usable without identity.

A future member-auth bridge may use standards-based OAuth or another secure client identity mechanism, but WorkOS is only one optional provider. Do not expose invite codes as bearer tokens or tool arguments.

## 12. Optional OAuth compatibility mode

The existing OAuth implementation is retained for compatibility and future experiments:

```text
OSI_HOSTED_ACCESS_MODE=oauth
```

OAuth mode still requires:

- a standards-compliant authorization server;
- exact MCP Resource Indicator/audience;
- introspection client credentials;
- Premium/member backend configuration;
- per-subject application limits.

WorkOS AuthKit/Connect remains one compatible authorization provider, but it is not part of public-mode Private Alpha.

Formal OAuth evidence uses:

```bash
osi-remote-smoke \
  --root . \
  --url https://mcp.aiworkstation.cn/mcp \
  --profile hosted-oauth \
  --auth-mode oauth \
  --expected-oauth-issuer https://<authorization-server> \
  --output tmp/hosted-oauth-remote.json
```

OAuth mode is not required to certify the anonymous nine-tool Hosted Private Alpha.

## 13. Rollback

Rollback is isolated from the existing AI Workstation/Radar services:

1. disable only the `mcp.aiworkstation.cn` Nginx vhost;
2. validate `nginx -t` before reload;
3. stop only the OSI Hosted container;
4. keep ports 8000/8010 and the existing AI Workstation services untouched;
5. never change `OSI_RELEASE_COMMIT` to claim a SHA that is not actually in the running image.

## 14. Explicit stop line

Hosted Private Alpha does not authorize broad paid launch.

Before any member-only/Premium launch, separately complete:

- secure AI Workstation member identity binding for MCP clients;
- unified membership/quota semantics with the existing AI Workstation system;
- Premium model cost/usage accounting against that unified policy;
- hosted privacy/terms/retention updates;
- production revocation and abuse validation;
- final platform connection review/publish.

Automated Paddle billing is optional and can remain deferred while AI Workstation continues manual WeChat/email payment and invite/member activation.
