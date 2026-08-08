"""OAuth 2.1 resource-server authentication for the hosted MCP.

The MCP server delegates login and token issuance to a standards-compliant
authorization server. This module verifies opaque access tokens through RFC 7662
introspection, validates issuer/resource/scope boundaries, and converts the
issuer+subject pair into an opaque entitlement identifier before any identity is
sent to the AI Workstation backend.
"""

from __future__ import annotations

import asyncio
import base64
import hashlib
import json
import os
import time
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass
from typing import Any, Mapping, Sequence

from mcp.server.auth.provider import AccessToken, TokenVerifier
from mcp.server.auth.settings import AuthSettings
from pydantic import AnyHttpUrl


class _NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):  # type: ignore[no-untyped-def]
        return None


@dataclass(frozen=True, slots=True)
class HostedOAuthConfig:
    issuer_url: str
    introspection_url: str
    client_id: str
    client_secret: str
    resource_url: str
    required_scopes: tuple[str, ...] = ("osi:use",)
    introspection_auth: str = "basic"
    timeout_seconds: float = 10.0


def _https_url(value: str, field: str) -> str:
    text = str(value or "").strip().rstrip("/")
    parsed = urllib.parse.urlsplit(text)
    if (
        parsed.scheme != "https"
        or not parsed.hostname
        or parsed.username
        or parsed.password
        or parsed.query
        or parsed.fragment
    ):
        raise ValueError(f"{field} must be a credential-free HTTPS URL without query or fragment")
    return text


def _scopes(value: Any) -> tuple[str, ...]:
    if isinstance(value, str):
        return tuple(part for part in value.split() if part)
    if isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)):
        return tuple(str(part).strip() for part in value if str(part).strip())
    return ()


def load_hosted_oauth_config() -> HostedOAuthConfig:
    issuer = _https_url(os.getenv("OSI_OAUTH_ISSUER_URL", ""), "OSI_OAUTH_ISSUER_URL")
    introspection = _https_url(
        os.getenv("OSI_OAUTH_INTROSPECTION_URL", ""), "OSI_OAUTH_INTROSPECTION_URL"
    )
    resource = _https_url(os.getenv("OSI_OAUTH_RESOURCE_URL", ""), "OSI_OAUTH_RESOURCE_URL")
    client_id = str(os.getenv("OSI_OAUTH_CLIENT_ID") or "").strip()
    client_secret = str(os.getenv("OSI_OAUTH_CLIENT_SECRET") or "").strip()
    if not client_id or len(client_id) > 512:
        raise ValueError("OSI_OAUTH_CLIENT_ID is required")
    if not client_secret or len(client_secret) > 4096:
        raise ValueError("OSI_OAUTH_CLIENT_SECRET is required")
    required = tuple(
        part for part in str(os.getenv("OSI_OAUTH_REQUIRED_SCOPES") or "osi:use").split() if part
    )
    auth_style = str(os.getenv("OSI_OAUTH_INTROSPECTION_AUTH") or "basic").strip().lower()
    if auth_style not in {"basic", "body"}:
        raise ValueError("OSI_OAUTH_INTROSPECTION_AUTH must be basic or body")
    try:
        timeout = float(os.getenv("OSI_OAUTH_TIMEOUT_SECONDS", "10"))
    except ValueError as exc:
        raise ValueError("OSI_OAUTH_TIMEOUT_SECONDS must be numeric") from exc
    if timeout <= 0 or timeout > 30:
        raise ValueError("OSI_OAUTH_TIMEOUT_SECONDS must be greater than 0 and no more than 30")
    return HostedOAuthConfig(
        issuer_url=issuer,
        introspection_url=introspection,
        client_id=client_id,
        client_secret=client_secret,
        resource_url=resource,
        required_scopes=required,
        introspection_auth=auth_style,
        timeout_seconds=timeout,
    )


def entitlement_subject(access_token: AccessToken) -> str:
    """Return a stable opaque billing key without exposing the raw OAuth subject."""

    subject = str(access_token.subject or "").strip()
    issuer = str((access_token.claims or {}).get("iss") or "").strip().rstrip("/")
    if not issuer or not subject:
        raise ValueError("OAuth token must include issuer and subject")
    digest = hashlib.sha256(f"{issuer}\n{subject}".encode("utf-8")).hexdigest()
    return f"oidc_{digest[:40]}"


class IntrospectionTokenVerifier(TokenVerifier):
    """Validate hosted-MCP bearer tokens through an RFC 7662 endpoint."""

    def __init__(self, config: HostedOAuthConfig) -> None:
        self.config = config
        self._opener = urllib.request.build_opener(_NoRedirect())

    def _introspect(self, token: str) -> Mapping[str, Any] | None:
        raw_token = str(token or "").strip()
        if not raw_token or len(raw_token) > 16_384:
            return None
        fields: dict[str, str] = {"token": raw_token}
        headers = {
            "accept": "application/json",
            "content-type": "application/x-www-form-urlencoded",
            "user-agent": "AI-Workstation-OSI-MCP/1.0",
        }
        if self.config.introspection_auth == "basic":
            credentials = f"{self.config.client_id}:{self.config.client_secret}".encode("utf-8")
            headers["authorization"] = "Basic " + base64.b64encode(credentials).decode("ascii")
        else:
            fields["client_id"] = self.config.client_id
            fields["client_secret"] = self.config.client_secret
        request = urllib.request.Request(
            self.config.introspection_url,
            data=urllib.parse.urlencode(fields).encode("utf-8"),
            method="POST",
            headers=headers,
        )
        try:
            with self._opener.open(request, timeout=self.config.timeout_seconds) as response:
                if int(response.status) != 200:
                    return None
                raw = response.read(256 * 1024 + 1)
        except (urllib.error.HTTPError, urllib.error.URLError, TimeoutError, OSError):
            return None
        if len(raw) > 256 * 1024:
            return None
        try:
            payload = json.loads(raw.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError):
            return None
        return payload if isinstance(payload, Mapping) else None

    def _validate(self, token: str, payload: Mapping[str, Any]) -> AccessToken | None:
        if payload.get("active") is not True:
            return None
        subject = str(payload.get("sub") or "").strip()
        client_id = str(payload.get("client_id") or "").strip()
        if not subject or not client_id:
            return None
        issuer = str(payload.get("iss") or self.config.issuer_url).strip().rstrip("/")
        if issuer != self.config.issuer_url:
            return None
        expires_at: int | None = None
        if payload.get("exp") is not None:
            try:
                expires_at = int(payload["exp"])
            except (TypeError, ValueError):
                return None
            if expires_at <= int(time.time()):
                return None
        granted_scopes = _scopes(payload.get("scope") or payload.get("scopes"))
        if any(scope not in granted_scopes for scope in self.config.required_scopes):
            return None
        audience = payload.get("aud") or payload.get("resource")
        if isinstance(audience, str):
            audiences = {audience.rstrip("/")}
        elif isinstance(audience, Sequence) and not isinstance(audience, (str, bytes, bytearray)):
            audiences = {str(value).strip().rstrip("/") for value in audience if str(value).strip()}
        else:
            audiences = set()
        if self.config.resource_url not in audiences:
            return None
        claims = {
            "iss": issuer,
            "aud": payload.get("aud") or payload.get("resource"),
        }
        if payload.get("org_id") is not None:
            claims["org_id"] = str(payload.get("org_id"))
        return AccessToken(
            token=token,
            client_id=client_id,
            scopes=list(granted_scopes),
            expires_at=expires_at,
            resource=self.config.resource_url,
            subject=subject,
            claims=claims,
        )

    async def verify_token(self, token: str) -> AccessToken | None:
        payload = await asyncio.to_thread(self._introspect, token)
        return self._validate(token, payload) if payload is not None else None


def hosted_auth_settings(config: HostedOAuthConfig) -> AuthSettings:
    return AuthSettings(
        issuer_url=AnyHttpUrl(config.issuer_url),
        resource_server_url=AnyHttpUrl(config.resource_url),
        required_scopes=list(config.required_scopes),
    )
