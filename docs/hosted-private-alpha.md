# Hosted Private Alpha Runbook

This runbook takes a reviewed source candidate from repository/External-Alpha quality gates to an **invited, OAuth-protected Hosted MCP** deployment. It deliberately stops before broad public launch, real-money billing acceptance, or platform submission.

Canonical Hosted MCP resource:

```text
https://mcp.aiworkstation.cn/mcp
```

Initial authorization provider:

```text
WorkOS AuthKit / Connect
```

## 0. Release invariant: one candidate, one evidence chain

Freeze a Hosted candidate commit before external deployment validation.

All of these must refer to that exact Git SHA:

- Python 3.10/3.12 CI evidence;
- EN/ZH live-validation evidence;
- Codex acceptance report + ledger;
- human review of that candidate's sanitized live artifact;
- Hosted remote OAuth/MCP evidence.

Do not reuse `d338faf0...` External Alpha artifacts to certify a later Hosted commit. They remain valid for the frozen External Alpha build only.

## 1. Candidate code gates

For the Hosted candidate:

1. merge only reviewed Hosted changes;
2. require repository CI green on Python 3.10 and 3.12;
3. require candidate-bound `ci-evidence.json`;
4. require candidate-bound bilingual `live-contract-validation` artifact;
5. run `osi-codex-acceptance` from a clean checkout of that exact SHA;
6. review the sanitized live artifact and record the human reviewer.

At this point `external_alpha_ready` should be true for the Hosted candidate itself before infrastructure evidence is added.

## 2. DNS

Create the DNS record for:

```text
mcp.aiworkstation.cn
```

Point it at the public IPv4/IPv6 address of the gateway host. Do not expose the MCP container port directly in DNS/firewall rules.

Verify from more than one resolver/network:

```bash
getent ahosts mcp.aiworkstation.cn
```

and, when available:

```bash
dig +short A mcp.aiworkstation.cn
dig +short AAAA mcp.aiworkstation.cn
```

Proceed only when the answers resolve to the intended gateway.

## 3. TLS and Nginx gateway

The repository provides:

```text
deploy/nginx/mcp.aiworkstation.cn.conf.example
```

Its intended topology is:

```text
Internet
  |
  | TCP 443 / HTTPS
  v
Nginx / TLS gateway
  |
  | loopback only
  v
127.0.0.1:8001
  |
  v
Hosted MCP container :8000
```

Required properties:

- TLS certificate valid for `mcp.aiworkstation.cn`;
- HTTP redirects to HTTPS except ACME challenge handling;
- MCP process is not Internet-addressable directly;
- `/mcp` is proxied with request/response buffering disabled;
- Authorization is forwarded;
- RFC 9728 protected-resource metadata routes are exposed;
- unrelated paths return 404;
- body-size and upstream timeouts remain bounded.

After certificate installation:

```bash
sudo nginx -t
sudo systemctl reload nginx
```

Verify certificate hostname and chain from an external machine before enabling invited testers.

## 4. WorkOS AuthKit / Connect

Use a dedicated WorkOS environment/application for the Hosted service rather than sharing unrelated production credentials where avoidable.

### Connect configuration

In WorkOS Dashboard → Connect → Configuration:

1. enable **Client ID Metadata Document (CIMD)**;
2. enable **Dynamic Client Registration (DCR)** during private alpha if compatibility with clients that have not migrated to CIMD is required;
3. add this exact Resource Indicator:

```text
https://mcp.aiworkstation.cn/mcp
```

Do not configure a slightly different origin, omit `/mcp`, or add a trailing alternate path. The MCP resource metadata, client `resource` request, WorkOS token `aud`, server verifier, deployment configuration, and final platform registration must all agree.

### Discover the WorkOS endpoints

Do not hand-type authorization/token/introspection paths if the actual AuthKit environment can report them. Inspect:

```bash
curl -fsS https://<authkit-domain>/.well-known/oauth-authorization-server | jq
```

Record the actual values for:

- `issuer`;
- `authorization_endpoint`;
- `token_endpoint`;
- `introspection_endpoint`;
- `registration_endpoint` when DCR is enabled;
- `scopes_supported`.

The current WorkOS MCP contract uses the exact Resource Indicator/audience as the primary authorization boundary. `OSI_OAUTH_REQUIRED_SCOPES` should remain empty for the initial WorkOS deployment unless the configured provider contract explicitly returns the chosen custom scope.

WorkOS introspection authenticates the application with `client_id` and `client_secret` in the form body. The server sends `token_type_hint=access_token` and rejects refresh/unknown token types.

## 5. Server-only environment

Create the production secret environment outside source control. Do not put these values in GitHub issues, PRs, logs, screenshots, or shell history.

Required shape:

```text
OSI_OAUTH_ISSUER_URL=https://<authkit-domain>
OSI_OAUTH_INTROSPECTION_URL=https://<authkit-domain>/oauth2/introspection
OSI_OAUTH_CLIENT_ID=<workos-connect-application-client-id>
OSI_OAUTH_CLIENT_SECRET=<server-only-secret>
OSI_OAUTH_RESOURCE_URL=https://mcp.aiworkstation.cn/mcp
OSI_OAUTH_REQUIRED_SCOPES=
OSI_OAUTH_INTROSPECTION_AUTH=body
OSI_BACKEND_SERVICE_TOKEN=<server-only-aiworkstation-service-token>
```

Prefer a root-readable environment file or platform secret store. Set restrictive filesystem permissions if a file is used.

Do not expose `OSI_BACKEND_SERVICE_TOKEN` or WorkOS client secret to browser/client-side code.

## 6. Preflight without opening the service

Use the repository's public-hosted Compose definition and real environment:

```bash
docker compose \
  -f compose.public-hosted.example.yml \
  --env-file /ABS/PRIVATE/PATH/osi-hosted.env \
  config >/tmp/osi-hosted-compose.rendered.yml
```

Then validate application configuration from the candidate image/environment:

```bash
set -a
. /ABS/PRIVATE/PATH/osi-hosted.env
set +a

osi-mcp-hosted --check-config
```

The output is intentionally non-secret. Confirm:

- mode = `hosted-oauth`;
- provider = `http`;
- OAuth resource = exact canonical MCP URL;
- backend origin = `https://aiworkstation.cn`;
- expected allowed hosts;
- expected rate limits;
- no secret/token is rendered.

## 7. Start the Hosted MCP

```bash
docker compose \
  -f compose.public-hosted.example.yml \
  --env-file /ABS/PRIVATE/PATH/osi-hosted.env \
  up -d --build
```

Confirm the container is healthy and that the host only listens on loopback for the upstream MCP port:

```bash
docker compose -f compose.public-hosted.example.yml ps
ss -ltnp | grep 8001
```

Expected host binding:

```text
127.0.0.1:8001
```

A public `0.0.0.0:8001`/`[::]:8001` host binding is a deployment failure.

## 8. Unauthenticated OAuth boundary

From a different machine/network, an MCP request without a token must **not** produce a successful tool list.

The Hosted validator checks that it receives:

- HTTP 401;
- Bearer `WWW-Authenticate`;
- `resource_metadata` on the same MCP origin;
- protected-resource metadata with exact `resource`;
- the expected WorkOS issuer in `authorization_servers`.

Manually useful metadata check:

```bash
curl -fsS https://mcp.aiworkstation.cn/.well-known/oauth-protected-resource | jq
```

The exact field values should include:

```json
{
  "resource": "https://mcp.aiworkstation.cn/mcp",
  "authorization_servers": ["https://<authkit-domain>"],
  "bearer_methods_supported": ["header"]
}
```

## 9. Authenticated Hosted smoke

Run from a clean checkout of the exact Hosted candidate SHA:

```bash
source .venv/bin/activate

osi-remote-smoke \
  --root . \
  --url https://mcp.aiworkstation.cn/mcp \
  --profile hosted \
  --auth-mode oauth \
  --expected-oauth-issuer https://<authkit-domain> \
  --locale en \
  --output tmp/hosted-remote.json
```

The command will print the authorization URL. Complete sign-in in a browser and paste the final callback URL when prompted. OAuth tokens remain in memory and are not written into the evidence report.

Required result:

- `ok=true`;
- report commit = exact Hosted candidate SHA;
- OAuth boundary = passed;
- authenticated MCP connection = passed;
- exactly 10 tools discovered: nine standard + `deep_research_ai_projects`;
- standard/Premium annotations correct;
- standard `search_ai_projects` call succeeds;
- no Premium invocation occurs.

### Controlled bearer diagnostic

Only if interactive OAuth troubleshooting requires it, put a temporary access token into an environment variable, never an argument:

```bash
read -rsp "Temporary WorkOS access token: " OSI_HOSTED_MCP_BEARER_TOKEN
export OSI_HOSTED_MCP_BEARER_TOKEN

osi-remote-smoke \
  --root . \
  --url https://mcp.aiworkstation.cn/mcp \
  --profile hosted \
  --auth-mode bearer-env \
  --expected-oauth-issuer https://<authkit-domain> \
  --output tmp/hosted-remote.json

unset OSI_HOSTED_MCP_BEARER_TOKEN
```

Treat a shell/session containing that token as sensitive until cleared.

## 10. Negative OAuth tests

Before Hosted Private Alpha is signed off, verify the deployed resource server fails closed for at least:

- no bearer token;
- malformed token;
- expired token;
- refresh token used as a bearer token;
- token for another Resource Indicator/audience;
- inactive/revoked token;
- wrong issuer;
- missing configured required scope if a non-empty scope policy is intentionally enabled.

Do not log the raw rejected tokens.

The ordinary Hosted remote evidence proves the public 401/metadata boundary and successful authenticated route. The negative matrix is an operator/security validation record and should be completed before expanding beyond a small invited cohort.

## 11. Final evidence-first Hosted readiness

Once **fresh Hosted-candidate** CI/live/Codex evidence exists, that candidate's live artifact has been reviewed, and `tmp/hosted-remote.json` is green:

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
  --expected-oauth-issuer https://<authkit-domain> \
  --output tmp/hosted-private-alpha-readiness.json
```

Success means:

```text
code_ready=true
external_alpha_ready=true
hosted_private_alpha_ready=true
```

`public_launch_ready=false` is still expected at this stage.

## 12. Rollback

Before inviting testers, record a rollback owner and make rollback mechanical:

1. retain the prior image/commit identifier;
2. keep Nginx config versioned and validate with `nginx -t` before reload;
3. keep server secrets outside image/source control;
4. if authentication or MCP behavior regresses, remove the invited connection, stop the Hosted container, or route the gateway to a known-good image;
5. do not relax OAuth validation as a recovery shortcut.

## 13. Explicit stop line

Hosted Private Alpha readiness does **not** authorize broad launch.

Do not yet claim Public Launch until the separate gates are complete, including:

- Paddle sandbox and final merchant/product configuration;
- Premium first-free / credit / refund behavior;
- service-specific hosted privacy/terms/retention policy;
- production revocation/rate-limit/abuse validation;
- final platform connection identity;
- fresh-install combined Plugin acceptance;
- platform/directory review and publish action.
