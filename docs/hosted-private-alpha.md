# Hosted Private Alpha Runbook

This runbook applies to the current **data-only** AI Open Source Intelligence product.

Canonical endpoint:

```text
https://mcp.aiworkstation.cn/mcp
```

Current Hosted access mode:

```text
OSI_HOSTED_ACCESS_MODE=public
```

The Hosted surface exposes exactly nine anonymous, read-only Radar data/evidence tools. It does not expose OAuth, WorkOS, Premium model execution, credits, checkout, or any AI Workstation server-side model path.

## 0. Release invariant

Freeze one candidate Git SHA and bind every release artifact and deployment check to that exact SHA.

Required candidate-bound evidence:

- Python 3.10/3.12 CI;
- EN/ZH live contract validation;
- Radar browse validation where required by the release process;
- Codex nine-tool acceptance;
- human artifact review;
- deployed MCP `serverInfo.version` identity;
- public Hosted remote smoke.

Production runtime identity:

```text
OSI_RELEASE_COMMIT=<exact-40-character-candidate-sha>
OSI_IMAGE_COMMIT=<same-exact-candidate-sha>
```

Hosted startup fails closed when runtime and baked image identity differ.

## 1. Product contract before deployment

The candidate must prove:

```text
tool_count=9
premium_enabled=false
server_model_enabled=false
oauth_enabled=false
```

Requirement-based public Radar selection must continue to send:

```text
use_model=false
```

`OSI_HOSTED_ACCESS_MODE=oauth` must fail closed.

The public Compose definition must not contain:

```text
OSI_OAUTH_*
OSI_BACKEND_SERVICE_TOKEN
OSI_PREMIUM_*
PADDLE_*
```

## 2. DNS and TLS

DNS:

```text
mcp.aiworkstation.cn
```

must resolve to the intended production gateway.

The public certificate must be valid for `mcp.aiworkstation.cn` and the MCP container port must never be published directly to the Internet.

Topology:

```text
Internet
  |
  | HTTPS 443
  v
Nginx TLS + anonymous abuse controls
  |
  | loopback only
  v
127.0.0.1:8001
  |
  v
Hosted MCP container :8000
```

## 3. Gateway policy

Use the candidate's versioned Nginx example:

```text
deploy/nginx/mcp.aiworkstation.cn.conf.example
```

Current required boundaries:

- `/mcp` is the only proxied MCP application path;
- everything else on the dedicated hostname returns `404` except ACME HTTP challenge handling;
- upstream is exactly `127.0.0.1:8001`;
- request/response buffering remains disabled for MCP streaming;
- MCP request body is limited to `256 KB`;
- gateway returns:

```text
X-OSI-Hosted-Gateway-Policy: tls-ip-rate-limited
```

- short-window per-IP limit: `60 requests/minute`, burst `30`;
- sustained per-IP limit: `10 requests/minute`, burst `300`;
- concurrent connections: `10` per IP;
- rate-limit rejection uses HTTP `429`.

The data-only release does not expose OAuth protected-resource metadata routes and does not forward an Authorization header to the MCP container.

## 4. Container deployment

Use the exact candidate source and:

```text
compose.public-hosted.example.yml
```

The host binding must remain:

```text
127.0.0.1:8001:8000
```

A binding such as `0.0.0.0:8001` or `[::]:8001` is a security failure.

Before opening external traffic, run:

```bash
osi-mcp-hosted --check-config
```

and require the data-only product fields above.

## 5. Remote smoke

Run from a clean checkout of the exact candidate:

```bash
osi-remote-smoke \
  --root . \
  --url https://mcp.aiworkstation.cn/mcp \
  --profile hosted-public \
  --auth-mode none \
  --invoke-search \
  --locale en \
  --output tmp/hosted-public-remote.json
```

Required evidence:

- `ok=true`;
- local candidate SHA equals remote `deployment_commit`;
- negotiated MCP protocol version is present;
- gateway policy check passes;
- exactly nine standard tools are discovered;
- all nine have the expected read-only annotations;
- `deep_research_ai_projects` is absent;
- a real `search_ai_projects` invocation succeeds.

The remote smoke must not invoke any AI Workstation server model.

## 6. Hosted readiness

Use the candidate-bound CI, full live validation bundle, Codex acceptance, human review and public Hosted remote smoke:

```bash
osi-hosted-evidence-readiness \
  --root . \
  --ci-evidence <candidate-ci-evidence.json> \
  --live-validation-evidence <candidate-validation-evidence.json> \
  --codex-acceptance-report <candidate-codex-report.json> \
  --hosted-remote-evidence <candidate-hosted-public-remote.json> \
  --artifact-reviewed \
  --reviewer "REVIEWER" \
  --expected-base-url https://aiworkstation.cn \
  --expected-hosted-mcp-url https://mcp.aiworkstation.cn/mcp \
  --expected-access-mode public \
  --output tmp/hosted-private-alpha-readiness.json
```

Success requires:

```text
code_ready=true
external_alpha_ready=true
hosted_private_alpha_ready=true
```

`public_launch_ready=false` may still be expected because platform publication, final service/legal review and real-world abuse monitoring are separate launch gates.

## 7. Rollback

If TLS, gateway, exact deployment identity, tool discovery, public port isolation, existing AI Workstation health or remote smoke fails:

1. stop the Hosted MCP container;
2. remove/restore the MCP Nginx vhost from the pre-deployment backup;
3. run `nginx -t`;
4. reload Nginx only after the test passes;
5. verify the existing AI Workstation site remains healthy;
6. keep DNS/certificates/source checkout for diagnosis unless they caused the failure.

Do not relax the data-only model boundary, loopback binding, candidate identity or gateway controls as a recovery shortcut.
