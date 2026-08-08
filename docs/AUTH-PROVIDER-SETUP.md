# Hosted OAuth provider setup

## Initial production provider: WorkOS AuthKit / Connect

The first public Hosted MCP release uses **WorkOS AuthKit / Connect** as the OAuth authorization server.

This is deliberately a managed authorization layer. AI Open Source Intelligence remains the MCP resource server and continues to own tool permissions, entitlement mapping, rate limits, billing policy and data access. WorkOS handles browser login/consent, OAuth client interoperability, token issuance, refresh/revocation and authorization-server discovery.

The implementation remains standards-based and provider-neutral enough to migrate later, but production setup and examples now target WorkOS so operators have one tested path rather than an abstract menu of identity providers.

## Why this fits the MCP product

WorkOS Connect exposes the OAuth endpoints required by current MCP clients, including:

- OAuth authorization-server metadata;
- Authorization Code + PKCE;
- refresh tokens;
- Client ID Metadata Document (CIMD);
- optional Dynamic Client Registration (DCR) for older MCP clients;
- Resource Indicators for MCP audience binding;
- token introspection;
- stable user `sub` claims.

The official MCP Python SDK used by this repository automatically exposes RFC 9728 Protected Resource Metadata when `TokenVerifier` and `AuthSettings.resource_server_url` are configured. Clients can therefore discover WorkOS from the MCP server after the initial 401 instead of asking a user to paste a bearer token.

## WorkOS dashboard setup

Use one WorkOS production environment for the public Plugin and a separate sandbox/staging environment while validating.

### 1. Configure AuthKit / Connect

Create/configure the customer-facing Connect OAuth application for **AI Open Source Intelligence**.

WorkOS's current authorization-server metadata advertises the standard scopes:

```text
email offline_access openid profile
```

Do **not** invent or require an `osi:use` scope for the WorkOS MCP resource server unless WorkOS later adds a documented custom-scope mechanism that is actually present in issued/introspected access tokens.

The current MCP authorization boundary is the exact Resource Indicator/audience. Request standard identity scopes only when the client/product actually needs them. `offline_access` may be used by a client that needs refresh tokens; it is not a resource-server permission for AI Open Source Intelligence.

### 2. Enable MCP client registration compatibility

In **Connect → Configuration**:

- enable **Client ID Metadata Document (CIMD)**;
- enable **Dynamic Client Registration (DCR)** only if compatibility testing shows an older target MCP client still needs it.

CIMD is the preferred launch path for current MCP clients.

### 3. Add the MCP Resource Indicator

Add this exact production MCP endpoint as a WorkOS Resource Indicator:

```text
https://mcp.aiworkstation.cn/mcp
```

MCP clients send this value as the OAuth `resource` parameter. WorkOS issues the access token with an `aud` claim matching that requested Resource Indicator, and the MCP resource server rejects tokens issued for another audience.

Use a separate staging URL while testing, for example:

```text
https://mcp-staging.aiworkstation.cn/mcp
```

and never accept a staging token on production.

### 4. Read metadata from the WorkOS domain

The WorkOS AuthKit domain exposes:

```text
https://<your-authkit-domain>/.well-known/oauth-authorization-server
```

Read the actual values from that document. For current WorkOS Connect these include an issuer and an introspection endpoint such as:

```text
https://<your-authkit-domain>/oauth2/introspection
```

Do not guess endpoint paths when configuring production; use the environment's discovery document.

### 5. Create a Connect client secret

Create the WorkOS client secret used by the MCP resource server for token introspection. Store the secret only in server-side deployment secrets.

WorkOS token introspection authenticates the resource-server client by sending `client_id` and `client_secret` in the form body, so the production default is:

```text
OSI_OAUTH_INTROSPECTION_AUTH=body
```

The implementation still supports `basic` for a future standards-compatible provider.

The resource server sends:

```text
token_type_hint=access_token
```

and rejects an introspection result that explicitly identifies the presented bearer credential as a `refresh_token`.

## Hosted MCP environment

Inject only through server secrets:

```text
OSI_OAUTH_ISSUER_URL=https://<your-authkit-domain>
OSI_OAUTH_INTROSPECTION_URL=https://<your-authkit-domain>/oauth2/introspection
OSI_OAUTH_CLIENT_ID=<workos-connect-client-id>
OSI_OAUTH_CLIENT_SECRET=<server-secret>
OSI_OAUTH_RESOURCE_URL=https://mcp.aiworkstation.cn/mcp
OSI_OAUTH_REQUIRED_SCOPES=
OSI_OAUTH_INTROSPECTION_AUTH=body
```

`OSI_OAUTH_REQUIRED_SCOPES` is intentionally empty for the documented WorkOS MCP flow. It remains available for another standards-compatible provider only when that provider actually issues and exposes the configured scopes to the resource server.

Never commit the client secret or a real access/refresh token.

## User identity and billing identity

The authorization server's raw `sub` is not used directly as the AI Workstation entitlement key.

After token verification:

```text
(issuer, subject)
   -> SHA-256
   -> oidc_<opaque-id>
```

The same user therefore keeps the same free-trial/Pro state across refreshed OAuth tokens while the private AI Workstation backend never needs the raw WorkOS user subject, email or access token.

## First-use user experience

The intended public flow is:

```text
Install AI Open Source Intelligence once
          ↓
First live tool call
          ↓
MCP returns OAuth challenge + resource metadata
          ↓
Client discovers WorkOS
          ↓
Browser login / consent
          ↓
Return to ChatGPT / Codex
          ↓
Nine live Radar tools available
          ↓
First successful Premium deep research = free trial
```

Users must not manually paste bearer tokens or configure a database/API URL.

## Fresh-account acceptance

From each real target host with no existing session:

1. install/connect AI Open Source Intelligence;
2. authorization UI opens automatically;
3. complete login/consent;
4. verify the issued access token is bound to the exact production Resource Indicator/audience;
5. call `get_radar_overview`;
6. browse at least one ranking, collection and category;
7. call `browse_radar_skills`;
8. run one successful Premium deep research and verify `credit_source=free_trial`;
9. disconnect/reconnect and verify identity continuity;
10. revoke/disable the WorkOS session/token;
11. verify MCP access fails;
12. verify a token for the wrong Resource Indicator is rejected;
13. verify a refresh token cannot be used directly as a bearer access token;
14. if a future provider enables optional resource-server scopes, verify a missing configured scope is rejected.

## Do not ship if

- users must manually paste bearer tokens;
- access silently becomes anonymous when OAuth fails;
- the server trusts a client-supplied username/header as identity;
- one OAuth identity can select another user's entitlement;
- OAuth subject/token/email appears in tool results, logs or payment metadata;
- revoked, expired or wrong-audience tokens are accepted;
- refresh tokens are accepted directly as bearer access tokens;
- deployment requires a custom scope that the selected provider does not actually issue/expose;
- `/.well-known/oauth-protected-resource` cannot be discovered by the target MCP host.
