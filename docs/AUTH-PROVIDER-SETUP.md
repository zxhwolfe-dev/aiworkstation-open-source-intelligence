# Hosted OAuth provider setup

## Recommendation

For the first public release, use a managed OAuth/OpenID authorization provider that supports modern MCP resource-server discovery/authorization behavior. Do not build a custom login/token service merely to ship this plugin.

The OSI code is intentionally provider-neutral: the hosted MCP validates access tokens through a standards-based introspection endpoint and relies on the authorization server for login, consent, user lifecycle and revocation.

A managed provider such as WorkOS AuthKit is a strong first candidate when its MCP/OAuth features and commercial terms fit the publishing account. Auth0 or another standards-compliant provider can be substituted without changing tool logic.

## Required capabilities

Before selecting the production provider, verify the actual account/plan supports:

- OAuth 2.1 / Authorization Code + PKCE behavior required by the target MCP host;
- authorization-server metadata/discovery;
- protected-resource/MCP discovery required by the target platform;
- stable user `sub` claim;
- resource/audience binding for the MCP endpoint;
- scope delivery (`osi:use` initial scope);
- token introspection or an equivalently strong standards-based verifier;
- refresh/revocation/disabled-user behavior;
- production custom domain if desired;
- email/GitHub/social login methods suitable for target users.

## Production values to create

Use the final public MCP URL, for example:

```text
https://mcp.aiworkstation.cn/mcp
```

Create/configure:

```text
issuer URL
introspection URL
resource-server client ID
resource-server client secret
resource/audience = exact MCP URL
scope = osi:use
```

Then inject them only into Hosted MCP deployment secrets:

```text
OSI_OAUTH_ISSUER_URL
OSI_OAUTH_INTROSPECTION_URL
OSI_OAUTH_CLIENT_ID
OSI_OAUTH_CLIENT_SECRET
OSI_OAUTH_RESOURCE_URL
OSI_OAUTH_REQUIRED_SCOPES=osi:use
```

## User identity

The authorization server's raw `sub` is not the internal entitlement key.

After verification:

```text
(issuer, subject)
   -> SHA-256
   -> oidc_<opaque-id>
```

This lets one user keep the same free-trial/subscription state across refreshed access tokens without exposing the raw identity to AI Workstation billing/model services.

## Fresh-account acceptance

From the real target host, with no existing session:

1. install/connect AI Open Source Intelligence;
2. authorization UI opens automatically;
3. complete login/consent;
4. call `get_radar_overview`;
5. call one ranking/collection/category browse;
6. disconnect/reconnect and verify identity continuity;
7. revoke/disable the user/token;
8. verify the MCP no longer accepts it;
9. verify a token for the wrong resource or missing `osi:use` scope is rejected.

## Do not ship if

- users must manually paste bearer tokens;
- access is silently anonymous when OAuth fails;
- the server trusts a client-supplied username/header as identity;
- one user's OAuth identity can select another user's entitlement;
- OAuth subject/token appears in tool results/logs/payment metadata;
- revoked/expired/wrong-audience tokens are accepted.
