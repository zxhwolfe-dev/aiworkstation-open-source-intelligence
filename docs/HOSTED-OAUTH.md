# Hosted MCP OAuth

## Goal

The hosted product uses standard MCP OAuth resource-server semantics. Users authenticate through an MCP host and WorkOS AuthKit/Connect; they never copy AI Workstation backend credentials into ChatGPT, Codex, or another host.

The initial production authorization provider is **WorkOS AuthKit/Connect**. The implementation remains provider-neutral at the verifier boundary so a standards-compatible RFC 7662 provider can be substituted later.

## Architecture

```text
MCP host
  |
  | OAuth 2.1 authorization
  v
WorkOS AuthKit / Connect
  |
  | access token whose aud is the exact MCP Resource Indicator
  v
https://mcp.aiworkstation.cn/mcp
  |
  | RFC 7662 token introspection
  v
WorkOS AuthKit / Connect
```

The MCP server validates:

- token introspection reports `active=true`;
- `token_type` is an access-token form, never a refresh token;
- issuer equals the configured AuthKit issuer;
- token has a subject and client ID;
- expiration has not passed;
- `aud`/resource includes the exact public MCP resource URL;
- optional required scopes are present only when a provider contract explicitly supplies them.

## WorkOS contract

WorkOS MCP authorization uses **Resource Indicators** as the primary access boundary. Configure the exact MCP endpoint in WorkOS Connect:

```text
https://mcp.aiworkstation.cn/mcp
```

MCP clients send that value as the OAuth `resource` parameter and WorkOS issues an access token whose `aud` matches the requested resource. Do not launch with no Resource Indicator configured: WorkOS otherwise uses its environment-default audience and can ignore the requested `resource`, which is not the boundary this service expects.

WorkOS AuthKit authorization-server metadata currently advertises the standard scopes `email`, `offline_access`, `openid`, and `profile`. The hosted service therefore **does not invent or require a WorkOS-specific `osi:use` scope**. `OSI_OAUTH_REQUIRED_SCOPES` defaults to empty. A future/generic RFC 7662 provider may configure explicit scopes if its introspection contract returns them reliably.

WorkOS token introspection authenticates the resource-server application by putting `client_id` and `client_secret` in the form body. The implementation also sends:

```text
token_type_hint=access_token
```

The introspection response must identify an active access token. Refresh-token and unknown token types fail closed.

Official references:

- https://workos.com/docs/authkit/mcp
- https://workos.com/docs/reference/workos-connect/introspection
- https://workos.com/changelog/resource-indicators-for-mcp-auth

## MCP client registration compatibility

In WorkOS Dashboard → **Connect → Configuration**:

1. enable **Client ID Metadata Document (CIMD)** for modern MCP clients;
2. enable **Dynamic Client Registration (DCR)** when compatibility with clients/validators that still dynamically register is required;
3. add the exact MCP endpoint as a Resource Indicator.

CIMD is the current MCP direction; DCR remains useful during Hosted Private Alpha and for older clients. Do not assume every target host supports the same registration mode—verify the real host before public launch.

## Environment

The WorkOS hosted candidate expects:

```text
OSI_PROVIDER=http
AIWORKSTATION_RADAR_BASE_URL=https://aiworkstation.cn

OSI_OAUTH_ISSUER_URL=https://<authkit-domain>
OSI_OAUTH_INTROSPECTION_URL=https://<authkit-domain>/oauth2/introspection
OSI_OAUTH_CLIENT_ID=<workos-connect-resource-server-client-id>
OSI_OAUTH_CLIENT_SECRET=<server-only-secret>
OSI_OAUTH_RESOURCE_URL=https://mcp.aiworkstation.cn/mcp
OSI_OAUTH_REQUIRED_SCOPES=
OSI_OAUTH_INTROSPECTION_AUTH=body
OSI_OAUTH_TIMEOUT_SECONDS=10

OSI_BACKEND_BASE_URL=https://aiworkstation.cn
OSI_BACKEND_SERVICE_TOKEN=<server-only-backend-service-secret>
```

`OSI_OAUTH_REQUIRED_SCOPES` may be set for a different authorization provider whose contract guarantees those scopes. It should remain empty for the initial WorkOS configuration unless WorkOS explicitly adds and returns the chosen custom scope.

Existing public-bind protections remain mandatory:

- live HTTP Radar provider;
- reverse-proxy/private-network acknowledgement;
- exact allowed Host values;
- explicit browser origins only when browser CORS is actually enabled;
- TLS termination at the public gateway;
- Hosted MCP process/container bound to loopback behind the gateway rather than directly to the Internet.

Validate configuration without opening a socket:

```bash
osi-mcp-hosted --check-config
```

The command intentionally prints only non-secret configuration.

## Protected Resource Metadata

The MCP server must return `401 Unauthorized` for an unauthenticated MCP request and advertise RFC 9728 Protected Resource Metadata through `WWW-Authenticate`.

The deployment proxy permits both discovery forms used by current MCP clients/spec revisions:

```text
https://mcp.aiworkstation.cn/.well-known/oauth-protected-resource
https://mcp.aiworkstation.cn/.well-known/oauth-protected-resource/mcp
```

The metadata must identify:

```json
{
  "resource": "https://mcp.aiworkstation.cn/mcp",
  "authorization_servers": ["https://<authkit-domain>"],
  "bearer_methods_supported": ["header"]
}
```

`osi-remote-smoke --profile hosted` checks this boundary before it performs an authenticated MCP tool discovery.

## Hosted Private Alpha OAuth smoke

The preferred validator exercises the real OAuth flow without persisting tokens:

```bash
osi-remote-smoke \
  --root . \
  --url https://mcp.aiworkstation.cn/mcp \
  --profile hosted \
  --auth-mode oauth \
  --expected-oauth-issuer https://<authkit-domain> \
  --locale en \
  --output tmp/hosted-remote.json
```

The validator:

1. proves an unauthenticated request receives a Bearer `401` challenge;
2. fetches and validates protected-resource metadata;
3. runs a real OAuth MCP client flow using ephemeral in-memory token storage;
4. discovers exactly nine standard Radar tools plus `deep_research_ai_projects`;
5. checks the standard/Premium side-effect annotations;
6. invokes one standard read-only `search_ai_projects` call;
7. writes a sanitized candidate-bound report containing no token.

For controlled diagnostics where an access token was obtained separately, use an environment-only token rather than a command-line argument:

```bash
read -rsp "Temporary WorkOS access token: " OSI_HOSTED_MCP_BEARER_TOKEN
export OSI_HOSTED_MCP_BEARER_TOKEN

after_test() { unset OSI_HOSTED_MCP_BEARER_TOKEN; }

osi-remote-smoke \
  --root . \
  --url https://mcp.aiworkstation.cn/mcp \
  --profile hosted \
  --auth-mode bearer-env \
  --expected-oauth-issuer https://<authkit-domain> \
  --output tmp/hosted-remote.json

after_test
```

Never put a bearer token in GitHub Actions logs, shell arguments, evidence JSON, screenshots, issues, or pull-request comments.

## Identity privacy

The raw OAuth subject is not used as the AI Workstation billing key.

The verified token produces:

```text
sha256(issuer + "\n" + subject) -> oidc_<opaque-id>
```

That stable opaque ID is used for:

- one-time premium trial;
- plan/AI-credit entitlement;
- application rate limits;
- private backend service calls.

The following must never be returned in public tool results or release evidence:

- raw bearer/access/refresh tokens;
- raw OAuth subject;
- authorization-server client secret;
- AI Workstation backend service token;
- Paddle customer/subscription IDs.

## Service-to-service backend authentication

The hosted MCP does not trust an entitlement subject by itself. Premium backend calls include both:

- a server-only service credential;
- the opaque authenticated user subject.

This prevents callers from directly choosing another user's entitlement identity.

## Rate limiting

The hosted candidate applies user-identity limits after OAuth verification. Current defaults:

```text
standard tools: 60/minute, 300/hour
premium tool:    5/minute
```

Configuration:

```text
OSI_RATE_LIMIT_PER_MINUTE
OSI_RATE_LIMIT_PER_HOUR
OSI_PREMIUM_RATE_LIMIT_PER_MINUTE
OSI_RATE_LIMIT_MAX_SUBJECTS
```

The implementation is intentionally bounded and in-process for the initial single-process Hosted Private Alpha deployment. A multi-replica deployment must move shared quotas to a shared store such as Redis or another transactional rate-limit backend before claiming globally consistent user quotas.

## Before public launch

Verify with the actual target MCP host, not only the project validator:

- authorization-server discovery;
- protected-resource metadata discovery;
- CIMD/DCR compatibility;
- fresh-user login and consent;
- exact token resource/audience;
- refresh/reconnect behavior where the host requests offline access;
- revocation and disabled-user behavior;
- wrong-resource rejection;
- any provider-specific required-scope rejection;
- target-platform connection and reinstall behavior.

## Fail-closed rules

Hosted MCP must not start as an unauthenticated fallback when OAuth configuration is missing. Invalid issuer, token type, audience/resource, expiration, configured required scope, or introspection response returns authentication failure rather than downgrading to anonymous access.
