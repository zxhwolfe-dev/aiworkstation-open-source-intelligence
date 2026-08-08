# Hosted MCP OAuth

## Goal

The public hosted product uses standard OAuth resource-server semantics. Users sign in through the MCP/plugin host once; they do not copy AI Workstation API keys into ChatGPT or Codex.

## Architecture

```text
MCP host
  |
  | OAuth authorization with Resource Indicator
  v
Authorization server
  |
  | access token bound to the public MCP resource audience
  v
https://<public-mcp-host>/mcp
  |
  | access-token introspection
  v
Authorization server
```

The MCP server validates:

- token is active;
- token is an access token when the provider reports a token type;
- issuer equals the configured issuer;
- token has a subject and client ID;
- expiration has not passed when an expiration is present;
- audience/resource includes the exact public MCP resource URL;
- configured required scopes are present when scope enforcement is explicitly enabled for a provider that exposes them.

For the initial WorkOS AuthKit/Connect deployment, the primary authorization boundary is the exact MCP **Resource Indicator/audience**. WorkOS's current token-introspection response documents `active`, `client_id`, `iss`, `aud`, `sub`, expiry and `token_type`, but does not expose custom resource scopes. Do not invent a mandatory `osi:use` scope for that provider contract.

## Environment

The hosted WorkOS candidate expects:

```text
OSI_PROVIDER=http
AIWORKSTATION_RADAR_BASE_URL=https://aiworkstation.cn

OSI_OAUTH_ISSUER_URL=https://<authkit-domain>
OSI_OAUTH_INTROSPECTION_URL=https://<authkit-domain>/oauth2/introspection
OSI_OAUTH_CLIENT_ID=<workos-application-client-id>
OSI_OAUTH_CLIENT_SECRET=<server-only-secret>
OSI_OAUTH_RESOURCE_URL=https://<public-mcp-host>/mcp
OSI_OAUTH_REQUIRED_SCOPES=
OSI_OAUTH_INTROSPECTION_AUTH=body
OSI_OAUTH_TIMEOUT_SECONDS=10

OSI_BACKEND_BASE_URL=https://aiworkstation.cn
OSI_BACKEND_SERVICE_TOKEN=<server-only-backend-service-secret>
```

`OSI_OAUTH_REQUIRED_SCOPES` is optional. Leave it empty for the documented WorkOS MCP flow. A different standards-compatible provider may set one or more space-separated scopes only when those scopes are actually issued and returned by its token verifier/introspection contract.

Existing public-bind protections are also mandatory for a non-loopback hosted deployment:

- live HTTP provider;
- reverse-proxy/private-network acknowledgement;
- explicit allowed Host values;
- explicit browser origins when CORS is enabled;
- TLS termination at the public gateway.

Validate without opening a socket:

```bash
osi-mcp-hosted --check-config
```

## WorkOS Resource Indicator

Configure the exact public MCP endpoint in WorkOS Connect as a valid Resource Indicator, for example:

```text
https://mcp.aiworkstation.cn/mcp
```

The value must match `OSI_OAUTH_RESOURCE_URL` exactly after the server's normalization rules. Access tokens presented to this MCP must carry the same value in `aud`/resource. A token issued for another resource is rejected even when it belongs to the same WorkOS environment and user.

Where WorkOS offers a default Resource Indicator for MCP clients that omit `resource`, configure it deliberately and keep it aligned with the canonical production endpoint.

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

The following must not be returned in public tool results:

- raw bearer token;
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

The implementation is intentionally bounded and in-process for the initial single-process hosted deployment. A multi-replica deployment must move shared quotas to a shared store such as Redis or another transactional rate-limit backend before claiming global per-user limits.

## Authorization-provider selection

The code uses a generic RFC 7662 introspection verifier rather than importing a vendor SDK into tool logic. WorkOS AuthKit/Connect is the initial production target; another provider can be substituted if it exposes the required MCP/OAuth metadata and verification contract.

Before public launch verify, with the actual target platform:

- authorization-server discovery;
- protected resource metadata;
- client registration/CIMD requirements;
- authorization flow from a fresh user;
- exact token audience/resource value;
- scope delivery only when optional scope enforcement is configured;
- refresh/reconnect behavior;
- revocation and disabled-user behavior.

## Fail-closed rules

Public Hosted MCP must not start as an unauthenticated fallback when OAuth configuration is missing. Inactive tokens, refresh tokens presented as bearer access tokens, invalid/missing issuer, wrong audience/resource, expired tokens, configured-scope failures, or introspection failures return authentication failure rather than downgrading to anonymous access.
