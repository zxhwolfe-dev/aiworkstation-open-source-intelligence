# Streamable HTTP and Hosted MCP Deployment

This document covers local/self-hosted Streamable HTTP and the production
anonymous data-only Hosted MCP.

## Production service

Canonical endpoint:

```text
https://mcp.aiworkstation.cn/mcp
```

Current contract:

```text
anonymous
read-only / non-destructive / idempotent
9 public Radar data/evidence tools
no OAuth or bearer token
no Premium, checkout, credits or server-model tool
```

The host model performs reasoning. AI Workstation serves public Radar
data/evidence, and requirement selection keeps `use_model=false`.

The `v0.3.0` production deployment was verified on 2026-08-11 with:

```text
source/runtime commit:
7b92e463a1da567afd5d1310601afdf1c6674646

GHCR digest:
sha256:ca97a9192fa0b6bdd9b62628acc48c74f7cb6b127ef88fcbacaaa6e6f5aed849
```

The deployed container reported healthy with zero restarts at validation time.
English and Chinese remote smoke tests, nine-tool discovery, a real search,
runtime/OCI identity, gateway policy, Host rejection and loopback isolation all
passed. This is a deployment record, not a perpetual uptime guarantee.

## Production topology

```text
MCP client
    |
    | HTTPS
    v
Nginx: TLS + Host/path policy + abuse controls
    |
    | host loopback only
    v
127.0.0.1:8001 -> Hosted MCP container:8000
    |
    v
public AI Open Source Radar APIs
```

The dedicated hostname proxies only `/mcp`; unrelated paths return `404`.
HTTP redirects to HTTPS, invalid Host values are rejected, and the container
port is not published on a public interface.

Current anonymous gateway controls:

```text
short window: 60 requests/minute/IP, burst 30
sustained:    10 requests/minute/IP, burst 300
connections:  10/IP
body size:    256 KB
```

The gateway policy response identifies itself as:

```text
X-OSI-Hosted-Gateway-Policy: tls-ip-rate-limited
```

The production vhost writes privacy-minimized service metrics to
`/var/log/nginx/osi-mcp.access.log`. Records contain only timestamp, HTTP
status, total request duration and upstream response duration; they omit client
IP, query string, referrer, User-Agent and request body. The host's Nginx
logrotate policy rotates logs daily and retains 14 rotations. Operators should
review status counts, p50/p95 latency, `429`, `5xx`, upstream failures and
container restart count at least daily during External Alpha.

The public Compose configuration bounds privacy-minimized application telemetry
to five 10 MiB Docker `json-file` logs. Apply this as a configuration-only
container recreation after the change reaches `main`, while retaining the exact
verified image digest and rollback record. These limits prevent an idle or
degraded service from consuming unbounded host storage; they do not replace the
Nginx service metrics or an incident owner.

These controls fit the current public, read-only, no-account product. If a
future release adds private data, member features or server inference, it must
introduce a separately reviewed identity, authorization, quota and privacy
design rather than silently changing this endpoint's semantics.

## Local Streamable HTTP defaults

```text
OSI_MCP_HTTP_HOST=127.0.0.1
OSI_MCP_HTTP_PORT=8000
OSI_MCP_HTTP_MAX_REQUEST_BODY_BYTES=262144
OSI_PROVIDER=mock
```

This opens a loopback-only endpoint and performs no live Radar reads unless
`OSI_PROVIDER=http` is selected explicitly.

Run locally:

```bash
python -m pip install -e ".[mcp]"
OSI_PROVIDER=mock osi-mcp-http
```

Connect to:

```text
http://127.0.0.1:8000/mcp
```

## Non-loopback self-hosted mode

Binding to `0.0.0.0`, a LAN address or a non-loopback hostname is rejected
unless all of these are configured:

```text
OSI_PROVIDER=http
OSI_MCP_HTTP_PUBLIC_BIND_ACK=reverse-proxy-or-private-network
AIWORKSTATION_RADAR_BASE_URL=https://aiworkstation.cn
OSI_MCP_HTTP_ALLOWED_HOSTS=mcp.example.com,mcp.example.com:*
```

The live Radar origin must be allow-listed HTTPS with no embedded credentials,
query, fragment, path or non-standard public port.

`OSI_MCP_HTTP_ALLOWED_HOSTS` is explicit DNS-rebinding/Host-header protection.
For browser clients, also set exact HTTPS origins with
`OSI_MCP_HTTP_ALLOWED_ORIGINS`. Keep the origin list empty for non-browser-only
deployments.

The public-bind acknowledgement is an operator assertion, not authentication.
Self-hosted operators remain responsible for TLS, network access, rate limits,
logging, incident response and local policy.

## Validate configuration without opening a socket

```bash
osi-mcp-http --check-config
```

A non-loopback configuration fails before server construction if the
acknowledgement, provider, Radar origin or Host allowlist is missing or invalid.

The request-body value must remain between 16 KiB and 1 MiB. A reverse proxy
should impose its own request/header limits as defense in depth.

## Container build and production candidate identity

Build an exact candidate image:

```bash
docker build \
  --build-arg OSI_IMAGE_COMMIT="$(git rev-parse HEAD)" \
  -t aiworkstation-osi-mcp:0.3.0 .
```

Validate the public-hosted example:

```bash
docker compose -f compose.public-hosted.example.yml config
```

Production must set the same exact 40-character commit for
`OSI_IMAGE_COMMIT` and `OSI_RELEASE_COMMIT`. The image runs as non-root with a
read-only filesystem, bounded tmpfs, dropped capabilities and
`no-new-privileges`.

Do not expose the container directly to the Internet or bake credentials into
the image.

## Remote validation

The read-only smoke client requires HTTPS for non-local endpoints and rejects
URLs containing usernames, passwords, query strings or fragments.

```bash
osi-remote-smoke \
  --url https://mcp.aiworkstation.cn/mcp

osi-remote-smoke \
  --url https://mcp.aiworkstation.cn/mcp \
  --invoke-search \
  --locale en

osi-remote-smoke \
  --url https://mcp.aiworkstation.cn/mcp \
  --invoke-search \
  --locale zh
```

A production acceptance must also verify:

- exact `serverInfo.version` commit;
- OCI revision, `OSI_IMAGE_COMMIT` and `OSI_RELEASE_COMMIT` equality;
- exactly nine tools and correct annotations;
- no Premium/OAuth/server-model tool;
- gateway header, HTTPS redirect and non-MCP `404` behavior;
- public port isolation and invalid Host rejection;
- container health/restart count and rollback readiness.

`osi-readiness --require-hosted-alpha` retains its historical field name. Its
output is candidate-bound evidence; it does not replace platform review,
real-user Alpha results, operational monitoring or incident ownership.

## Current remaining release work

Runtime deployment is complete. Remaining work is product/distribution work:

- align service-specific Privacy/Terms/support copy with actual Hosted data
  handling;
- establish an error/latency/429 monitoring baseline and review anonymous abuse
  thresholds with real traffic;
- complete fresh-install Skill + Hosted MCP acceptance with external testers;
- verify publisher identity and submit the combined public plugin;
- retain an explicit rollback owner and procedure for every future runtime
  deployment.

For the initial production monitoring baseline, record the observation window
and use the dedicated metrics log rather than raw prompts or client identity.
An empty or very small sample is valid evidence of low traffic, not evidence
that the threshold is correctly tuned. Keep the current abuse thresholds until
real traffic demonstrates a concrete false-positive or capacity problem.
