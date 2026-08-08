# Hosted MCP OAuth

## Goal

The public hosted product uses standard OAuth resource-server semantics. Users sign in through the MCP/plugin host once; they do not copy AI Workstation API keys into ChatGPT or Codex.

## Architecture

```text
MCP host
  |
  | OAuth authorization
  v
Authorization server
  |
  | access token scoped to public MCP resource
  v
https://<public-mcp-host>/mcp
  |
  | token introspection
  v
Authorization server
```

The MCP server validates:

- token is active;
- issuer equals the configured issuer;
- token has a subject and client ID;
- expiration has not passed;
- required scopes are present;
- audience/resource includes the exact public MCP resource URL.

## Environment

The hosted candidate expects:

```text
OSI_PROVIDER=http
AIWORKSTATION_RADAR_BASE_URL=https://aiworkstation.cn

OSI_OAUTH_ISSUER_URL=https://<authorization-server>
OSI_OAUTH_INTROSPECTION_URL=https://<authorization-server>/<introspection-path>
OSI_OAUTH_CLIENT_ID=<resource-server-client-id>
OSI_OAUTH_CLIENT_SECRET=<server-only-secret>
OSI_OAUTH_RESOURCE_URL=https://<public-mcp-host>/mcp
OSI_OAUTH_REQUIRED_SCOPES=osi:use
OSI_OAUTH_INTROSPECTION_AUTH=basic
OSI_OAUTH_TIMEOUT_SECONDS=10

OSI_BACKEND_BASE_URL=https://aiworkstation.cn
OSI_BACKEND_SERVICE_TOKEN=<server-only-backend-service-secret>
```

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

The code uses a generic RFC 7662 introspection verifier rather than importing a vendor SDK into tool logic. A production provider must support the MCP/OAuth client flow expected by the target host and expose standards-compliant authorization-server/resource metadata.

Before public launch verify, with the actual target platform:

- authorization-server discovery;
- protected resource metadata;
- client registration requirements;
- authorization flow from a fresh user;
- token audience/resource value;
- scope delivery;
- refresh/revocation behavior;
- logout/revocation and disabled-user behavior.

## Fail-closed rules

Public Hosted MCP must not start as an unauthenticated fallback when OAuth configuration is missing. Invalid issuer, scope, audience, expiration or introspection failures return authentication failure rather than downgrading to anonymous access.
