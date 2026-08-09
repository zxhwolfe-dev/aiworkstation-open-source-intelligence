# Hosted MCP OAuth Compatibility Mode

## Scope

OAuth is **optional** for AI Workstation Open Source Intelligence Hosted MCP.

The default Hosted Private Alpha uses:

```text
OSI_HOSTED_ACCESS_MODE=public
```

and exposes exactly nine anonymous read-only Radar tools. It does not need WorkOS, another identity provider, a billing backend, or Premium credentials.

This document describes the retained compatibility/future-member mode:

```text
OSI_HOSTED_ACCESS_MODE=oauth
```

The verifier remains provider-neutral at the RFC 7662 boundary. WorkOS AuthKit/Connect is one compatible provider, not a product dependency.

## OAuth architecture

```text
MCP host
  |
  | OAuth authorization
  v
standards-compatible authorization server
  |
  | access token whose aud/resource is the exact MCP Resource Indicator
  v
https://mcp.aiworkstation.cn/mcp
  |
  | RFC 7662 token introspection
  v
authorization server
```

OAuth mode validates:

- introspection reports `active=true`;
- `token_type` is an access-token form, never a refresh token;
- issuer equals the configured authorization-server issuer;
- token has a subject and client ID;
- expiration has not passed;
- `aud`/resource includes the exact public MCP resource URL;
- optional required scopes are present only when the provider contract explicitly supplies them.

## WorkOS compatibility contract

If WorkOS is selected as the authorization provider, configure this exact Resource Indicator:

```text
https://mcp.aiworkstation.cn/mcp
```

For the existing WorkOS adapter:

```text
OSI_OAUTH_REQUIRED_SCOPES=
OSI_OAUTH_INTROSPECTION_AUTH=body
```

Do not invent a mandatory `osi:use` scope. WorkOS introspection authenticates the resource-server application with `client_id` and `client_secret` in the form body and the implementation sends `token_type_hint=access_token`.

WorkOS CIMD/DCR configuration is relevant only when OAuth mode is intentionally enabled.

## OAuth-mode environment

```text
OSI_PROVIDER=http
AIWORKSTATION_RADAR_BASE_URL=https://aiworkstation.cn
OSI_RELEASE_COMMIT=<exact-40-character-hosted-candidate-sha>
OSI_HOSTED_ACCESS_MODE=oauth

OSI_OAUTH_ISSUER_URL=https://<authorization-server>
OSI_OAUTH_INTROSPECTION_URL=https://<authorization-server>/oauth2/introspection
OSI_OAUTH_CLIENT_ID=<resource-server-client-id>
OSI_OAUTH_CLIENT_SECRET=<server-only-secret>
OSI_OAUTH_RESOURCE_URL=https://mcp.aiworkstation.cn/mcp
OSI_OAUTH_REQUIRED_SCOPES=
OSI_OAUTH_INTROSPECTION_AUTH=body
OSI_OAUTH_TIMEOUT_SECONDS=10

OSI_BACKEND_BASE_URL=https://aiworkstation.cn
OSI_BACKEND_SERVICE_TOKEN=<server-only-backend-service-secret>
```

`OSI_RELEASE_COMMIT` remains mandatory for both public and OAuth Hosted modes and must be the exact deployed Git SHA. Docker builds bind the same candidate through `OSI_IMAGE_COMMIT`.

Validate without opening a socket:

```bash
osi-mcp-hosted --check-config
```

OAuth mode reports `mode=hosted-oauth`; public mode reports `mode=hosted-public` and does not load the OAuth/backend secrets above.

## Protected Resource Metadata

OAuth mode must return a Bearer `401` challenge for an unauthenticated MCP request and advertise RFC 9728 Protected Resource Metadata. The Nginx template narrowly permits both discovery forms:

```text
https://mcp.aiworkstation.cn/.well-known/oauth-protected-resource
https://mcp.aiworkstation.cn/.well-known/oauth-protected-resource/mcp
```

Metadata must bind the exact MCP resource and advertise the configured authorization server.

Public mode does not require OAuth metadata to be successful.

## Formal OAuth smoke

Use the explicit OAuth profile:

```bash
osi-remote-smoke \
  --root . \
  --url https://mcp.aiworkstation.cn/mcp \
  --profile hosted-oauth \
  --auth-mode oauth \
  --expected-oauth-issuer https://<authorization-server> \
  --locale en \
  --output tmp/hosted-oauth-remote.json
```

The backward-compatible `--profile hosted` alias still represents OAuth Hosted mode.

OAuth evidence proves:

1. the 401/Bearer/RFC 9728 authorization boundary;
2. a real OAuth client flow with in-memory token storage;
3. exact remote `serverInfo.version` deployment identity;
4. exactly nine standard tools plus `deep_research_ai_projects`;
5. expected annotations;
6. one successful standard read-only search;
7. no token is written to evidence.

A bearer token supplied through `OSI_HOSTED_MCP_BEARER_TOKEN` remains diagnostic-only and cannot replace the real OAuth flow for OAuth-mode readiness.

## Identity privacy

The verified OAuth subject is converted to an opaque key:

```text
sha256(issuer + "\n" + subject) -> oidc_<opaque-id>
```

Raw tokens, raw subjects, OAuth client secrets, private backend tokens, and payment-provider identifiers must not be returned in public tool results or evidence.

## AI Workstation membership direction

OAuth provider identity must not become a second subscription database.

Future paid/member access should map the authenticated client identity to the existing AI Workstation membership source of truth and existing quota policy. WorkOS, if used at all, should act only as an identity bridge.

Do not use invite codes directly as MCP bearer tokens or tool arguments.

Automated Paddle billing is not a prerequisite for Hosted Private Alpha and remains optional while AI Workstation uses manual WeChat/email payment and member/invite activation.

## Rate limiting

OAuth mode retains per-subject application limits. Public mode instead relies on the explicit Nginx IP/request/connection boundary in `deploy/nginx/mcp.aiworkstation.cn.conf.example`.

A multi-replica OAuth deployment must move shared user quotas to a shared transactional rate-limit store before claiming globally consistent quotas.
