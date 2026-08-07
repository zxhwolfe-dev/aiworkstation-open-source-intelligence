# Guarded Streamable HTTP Deployment

The repository can run the six read-only tools over Streamable HTTP for local,
private-network and reverse-proxy alpha testing. This is a deployment surface,
not a claim that the endpoint is safe to expose directly to the public Internet.

The current MCP Python SDK v2 uses Streamable HTTP as its production-oriented
HTTP transport and supports stateless JSON responses. This project also enables
the SDK's transport-security host/origin checks explicitly for non-loopback
binds.

## Security model

### Local mode

Defaults:

```text
OSI_MCP_HTTP_HOST=127.0.0.1
OSI_MCP_HTTP_PORT=8000
OSI_MCP_HTTP_MAX_REQUEST_BODY_BYTES=262144
OSI_PROVIDER=mock
```

This opens a loopback-only MCP endpoint and performs no live Radar reads unless
`OSI_PROVIDER=http` is selected explicitly. Local mode leaves the SDK's secure
localhost transport-security defaults intact.

### Non-loopback mode

Binding to `0.0.0.0`, a LAN address or a non-loopback hostname is rejected unless
all of these are configured:

```text
OSI_PROVIDER=http
OSI_MCP_HTTP_PUBLIC_BIND_ACK=reverse-proxy-or-private-network
AIWORKSTATION_RADAR_BASE_URL=https://aiworkstation.cn
OSI_MCP_HTTP_ALLOWED_HOSTS=mcp.example.com,mcp.example.com:*
```

The live Radar origin must be allow-listed HTTPS with no embedded credentials,
query, fragment, path or non-standard public port.

`OSI_MCP_HTTP_ALLOWED_HOSTS` is passed to the MCP SDK as explicit
DNS-rebinding/Host-header protection. Entries are exact `host[:port]` values or
`host:*` patterns. Include only Host values the trusted proxy/client is expected
to send.

For browser-based MCP clients, also define exact HTTPS origins:

```text
OSI_MCP_HTTP_ALLOWED_ORIGINS=https://app.example.com
```

An empty origin list is appropriate for non-browser clients. If browsers are
supported, the gateway/application CORS policy must match the same narrow origin
set.

The public-bind acknowledgement is deliberately named to make the boundary
explicit: it is **not authentication**. A non-loopback endpoint must still be
protected by a trusted private network or authenticated TLS reverse proxy.
`OSI_MCP_HTTP_ASSUME_PUBLIC_AUTH=true` is rejected.

## Request-body cap

The MCP SDK has its own HTTP body limit, and this project sets a smaller alpha
default because the six tools accept compact structured requests:

```text
OSI_MCP_HTTP_MAX_REQUEST_BODY_BYTES=262144
```

The configured value must remain between 16 KiB and 1 MiB. This is defense in
depth; the gateway should impose its own request/header limits too.

## Validate configuration without opening a socket

```bash
osi-mcp-http --check-config
```

Local output includes the bind, provider, body cap and whether explicit hosted
allowlists are present. A non-loopback configuration fails before the server is
built if the acknowledgement, live provider, Radar origin or Host allowlist is
missing/invalid.

## Run locally

```bash
python -m pip install -e ".[mcp]"
OSI_PROVIDER=mock osi-mcp-http
```

Connect to:

```text
http://127.0.0.1:8000/mcp
```

Run the real MCP compatibility smoke test:

```bash
osi-remote-smoke --url http://127.0.0.1:8000/mcp
```

Add one read-only tool call:

```bash
osi-remote-smoke \
  --url http://127.0.0.1:8000/mcp \
  --invoke-search \
  --locale en
```

The smoke client requires HTTPS for non-local endpoints and rejects credentials,
query strings and fragments embedded in endpoint URLs.

## Container build

```bash
docker build -t aiworkstation-osi-mcp:0.1.0 .
docker compose -f compose.hosted.example.yml config
docker compose -f compose.hosted.example.yml up --build
```

The image:

- runs as a non-root user;
- contains the runtime Python package and MCP dependency only;
- has a cheap TCP health check;
- does not bake credentials or public-bind acknowledgement into the image.

The Compose example:

- binds the process to container `0.0.0.0:8000` but maps only host
  `127.0.0.1:8000`;
- explicitly allows only `127.0.0.1:8000` and `localhost:8000` Host headers;
- leaves browser origins empty;
- uses a read-only filesystem, bounded tmpfs, `no-new-privileges`, dropped
  capabilities and resource limits.

For a same-host reverse proxy that preserves a public Host header, replace or
extend `OSI_MCP_HTTP_ALLOWED_HOSTS` with the exact public MCP hostname before
starting the service. Do not expose the container port on all host interfaces
merely for convenience.

## Reverse-proxy requirements before Internet exposure

The proxy/gateway must provide at minimum:

1. TLS termination with a valid public certificate.
2. Authentication before MCP requests reach the application.
3. Per-principal and per-IP rate limiting.
4. Request-body/header size limits.
5. Connection and upstream timeouts suitable for MCP.
6. A strict Host policy that agrees with `OSI_MCP_HTTP_ALLOWED_HOSTS`.
7. Logging that excludes authorization credentials and complete prompts.
8. An abuse-blocking path that can disable a principal without redeployment.
9. A defined maximum concurrency and upstream request budget.
10. A cheap health/readiness strategy that does not invoke an expensive Radar
    search.

If browser clients are introduced, configure CORS narrowly and mirror the
allowed browser origins in `OSI_MCP_HTTP_ALLOWED_ORIGINS`.

## Native MCP authorization

The MCP SDK provides resource-server authorization primitives, but this
repository intentionally does not yet ship an authorization server, token
verifier or protected-resource metadata. Those features depend on the intended
account, identity and commercial model.

For a broad public ChatGPT/plugin or hosted MCP service, prefer per-user OAuth-
style authorization over a shared static token so identity, revocation, scopes
and future quotas can be enforced correctly.

## Remote validation sequence

After deployment behind the protected gateway/private network:

```bash
osi-remote-smoke --url https://YOUR-MCP-HOST/mcp
osi-remote-smoke \
  --url https://YOUR-MCP-HOST/mcp \
  --invoke-search \
  --locale en
osi-remote-smoke \
  --url https://YOUR-MCP-HOST/mcp \
  --invoke-search \
  --locale zh
```

Record the deployed commit, endpoint and gateway configuration in the release
evidence, then use `osi-readiness --require-hosted-alpha` with the real
attestations.

## What remains before broad public hosting

The repository now provides the read-only transport, DNS-rebinding protection,
request caps, container scaffold and compatibility tests. A public service still
requires operator/product work:

- final MCP hostname, DNS and TLS;
- per-user OAuth/identity and revocation;
- quotas, rate limits, concurrency and abuse controls;
- production logging/metrics and retention;
- secret management and key rotation;
- deployment rollback/incident policy;
- final privacy, terms, support and software-license decisions;
- live platform registration/review and compatibility testing.

Until those exist, the hosted server remains a private-alpha capability.
