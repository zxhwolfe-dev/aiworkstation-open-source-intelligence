# Hosted OAuth provider setup

## Recommendation

For the first public release, use **WorkOS AuthKit/Connect** as the managed OAuth authorization provider, assuming the publishing account and commercial terms remain suitable. Do not build a custom login/token service merely to ship this plugin.

The OSI code remains provider-neutral at the resource-server boundary: the hosted MCP validates access tokens through a standards-based introspection endpoint and relies on the authorization server for login, consent, user lifecycle and revocation.

Auth0 or another standards-compatible provider can be substituted later without changing tool logic, but provider-specific token claims/scopes must be configured from the provider's real contract rather than assumed.

## Required capabilities

Before production, verify the actual WorkOS account/environment supports:

- OAuth authorization behavior required by the target MCP host;
- authorization-server metadata/discovery;
- Client ID Metadata Document (CIMD) and any backwards-compatible registration mode needed by target clients;
- protected-resource/MCP discovery required by the target platform;
- stable user `sub` claim;
- Resource Indicator / audience binding for the exact MCP endpoint;
- access-token verification/introspection;
- refresh/revocation/disabled-user behavior;
- production custom domain if desired;
- email/GitHub/social login methods suitable for target users.

## Production values to create

Use the final public MCP URL, for example:

```text
https://mcp.aiworkstation.cn/mcp
```

Add that exact URL in WorkOS Connect as a valid **Resource Indicator**. Configure a default Resource Indicator as well when needed for MCP clients that omit the `resource` parameter, and keep it identical to the canonical production MCP resource URL.

Create/configure:

```text
issuer URL = https://<authkit-domain>
introspection URL = https://<authkit-domain>/oauth2/introspection
WorkOS Application client ID
WorkOS Application client secret
resource/audience = exact MCP URL
```

For the documented WorkOS MCP contract, leave custom required scopes empty. WorkOS's current introspection response exposes the access token's issuer, audience/resource, subject, expiry and token type, but does not document custom resource scopes. The MCP therefore uses exact issuer + Resource Indicator/audience binding as its default authorization boundary.

A different provider may configure `OSI_OAUTH_REQUIRED_SCOPES` only when it actually issues and verifies those scopes.

Inject deployment values only into Hosted MCP secrets/environment:

```text
OSI_OAUTH_ISSUER_URL
OSI_OAUTH_INTROSPECTION_URL
OSI_OAUTH_CLIENT_ID
OSI_OAUTH_CLIENT_SECRET
OSI_OAUTH_RESOURCE_URL
OSI_OAUTH_REQUIRED_SCOPES=
OSI_OAUTH_INTROSPECTION_AUTH=body
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
4. verify the issued access token is bound to the exact MCP Resource Indicator/audience;
5. call `get_radar_overview`;
6. call one ranking/collection/category browse;
7. disconnect/reconnect and verify identity continuity;
8. revoke/disable the user/token;
9. verify the MCP no longer accepts it;
10. verify a token for the wrong MCP resource is rejected;
11. verify a refresh token cannot be used directly as a bearer access token;
12. if optional custom scopes are enabled with another provider, verify missing/wrong scope is rejected.

## Do not ship if

- users must manually paste bearer tokens;
- access is silently anonymous when OAuth fails;
- the server trusts a client-supplied username/header as identity;
- one user's OAuth identity can select another user's entitlement;
- OAuth subject/token appears in tool results/logs/payment metadata;
- revoked/expired/wrong-audience tokens are accepted;
- refresh tokens are accepted directly as bearer access tokens;
- deployment requires a custom scope that the selected provider does not actually issue or expose to the resource server.
