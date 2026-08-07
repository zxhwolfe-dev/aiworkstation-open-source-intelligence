# Guarded Streamable HTTP Deployment

The repository can now run the six read-only tools over Streamable HTTP for
private-network and reverse-proxy alpha testing. This is a deployment surface,
not a claim that the endpoint is safe to expose directly to the public Internet.

The official MCP Python SDK v2 recommends Streamable HTTP for production and
supports stateless JSON responses. `osi-mcp-http` uses those settings so the
service is easier to scale and test across modern MCP hosts.

## Security model

`osi-mcp-http` has two modes.

### Local mode

Defaults:

```text
OSI_MCP_HTTP_HOST=127.0.0.1
OSI_MCP_HTTP_PORT=8000
OSI_PROVIDER=mock
```

This opens a loopback-only MCP endpoint and performs no live network reads unless
`OSI_PROVIDER=http` is selected explicitly.

### Non-loopback mode

Binding to `0.0.0.0`, a LAN address or a non-loopback hostname is rejected unless
all of these are true:

```text
OSI_PROVIDER=http
OSI_MCP_HTTP_PUBLIC_BIND_ACK=reverse-proxy-or-private-network
AIWORKSTATION_RADAR_BASE_URL=https://aiworkstation.cn
```

The live Radar origin must be HTTPS, use an allow-listed AI Workstation host,
have no embedded credentials, query or fragment, and use the standard HTTPS
port.

The acknowledgement is deliberately named to make the boundary explicit: it is
**not authentication**. A non-loopback endpoint must still be protected by a
trusted private network or by a TLS reverse proxy that implements authentication,
rate limiting and abuse controls.

There is no environment flag that pretends authentication already exists.
`OSI_MCP_HTTP_ASSUME_PUBLIC_AUTH=true` is rejected.

## Validate configuration without opening a socket

```bash
osi-mcp-http --check-config
```

Example local output:

```json
{
  "ok": true,
  "endpoint": "http://127.0.0.1:8000/mcp",
  "settings": {
    "host": "127.0.0.1",
    "port": 8000,
    "provider": "mock",
    "public_bind": false,
    "stateless_http": true,
    "json_response": true,
    "auth_mode": "reverse-proxy-required"
  }
}
```

## Run locally

```bash
python -m pip install -e ".[mcp]"
OSI_PROVIDER=mock osi-mcp-http
```

Connect an MCP client to:

```text
http://127.0.0.1:8000/mcp
```

Run the read-only compatibility smoke test:

```bash
osi-remote-smoke --url http://127.0.0.1:8000/mcp
```

Add one real tool invocation:

```bash
osi-remote-smoke \
  --url http://127.0.0.1:8000/mcp \
  --invoke-search \
  --locale en
```

The smoke client requires HTTPS for non-local endpoints and rejects credentials,
query strings and fragments embedded in endpoint URLs.

## Container build

Build:

```bash
docker build -t aiworkstation-osi-mcp:0.1.0 .
```

The image:

- runs as a non-root user;
- contains only the runtime Python package and its MCP dependency;
- has a TCP health check;
- does not bake credentials into the image;
- does not automatically opt into a public bind.

A localhost-only compose example is provided:

```bash
docker compose -f compose.hosted.example.yml up --build
```

It maps the container only to host loopback:

```text
127.0.0.1:8000 -> container:8000
```

This is suitable for a same-host reverse proxy or private validation. Do not
change it to `0.0.0.0:8000:8000` merely for convenience.

## Reverse-proxy requirements before Internet exposure

The proxy or gateway must provide, at minimum:

1. TLS 1.2+ termination with a valid public certificate.
2. Authentication before MCP requests reach the application.
3. Per-principal and per-IP rate limiting.
4. Request-body and header size limits.
5. Connection and upstream timeouts suitable for MCP.
6. Host allow-listing and DNS-rebinding protection.
7. Logging that excludes authorization credentials and complete user prompts.
8. An abuse-blocking path that can disable a principal without redeployment.
9. A defined maximum concurrency and upstream request budget.
10. A health/readiness strategy that does not invoke an expensive Radar search.

If browser-based clients are introduced, configure CORS narrowly. Do not use a
wildcard production origin policy simply to make a client connect.

## Native MCP authorization

The MCP SDK supports OAuth-style resource-server authorization, but this
repository does not yet ship an authorization server, token verifier or protected
resource metadata. Those features must be designed around the intended account
and billing model rather than added as a placeholder.

For a public ChatGPT plugin or broadly shared hosted MCP service, native OAuth is
preferred over a shared static bearer token because it enables per-user identity,
revocation, scopes and future quota enforcement.

## Remote validation sequence

After deployment behind the protected gateway:

```bash
osi-remote-smoke --url https://YOUR-MCP-HOST/mcp
```

Then, only after authentication and live Radar access are confirmed:

```bash
osi-remote-smoke \
  --url https://YOUR-MCP-HOST/mcp \
  --invoke-search \
  --locale en
```

Repeat for Chinese and record the deployment commit and endpoint in the release
readiness evidence.

## What remains before public hosting

Code in this repository can prepare the transport and validation surface, but a
public service still requires operator-owned infrastructure:

- final MCP hostname and DNS;
- TLS certificate and reverse proxy/load balancer;
- OAuth/identity decision and token validation;
- quotas, rate limits and abuse controls;
- production logging/metrics destination;
- secret management;
- deployment rollback policy;
- public legal and support URLs;
- live ChatGPT/Codex registration and compatibility testing.

Until those exist, the hosted server is an internal/private-alpha capability.
