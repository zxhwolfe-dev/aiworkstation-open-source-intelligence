"""OAuth-protected hosted MCP for the one-install AI Open Source Intelligence product."""

from __future__ import annotations

import asyncio
from typing import Any, Literal, Mapping

from mcp.server import MCPServer
from mcp.server.auth.middleware.auth_context import get_access_token
from mcp.server.auth.provider import AccessToken, TokenVerifier
from mcp.server.auth.settings import AuthSettings
from mcp.types import ToolAnnotations

from .app import create_registry_from_env
from .contracts import utc_now_iso
from .full_tools import FullToolRegistry
from .hosted_auth import (
    IntrospectionTokenVerifier,
    entitlement_subject,
    hosted_auth_settings,
    load_hosted_oauth_config,
)
from .hosted_backend import HostedBackendClient, HostedBackendError, load_hosted_backend_config
from .hosted_rate_limit import HostedRateLimiter, load_hosted_rate_limit_config
from .hosted_rate_limited_provider import HostedRateLimitedProvider
from .mcp_server import SERVER_INSTRUCTIONS, build_mcp_server
from .tools import ToolRegistry

HOSTED_INSTRUCTIONS = SERVER_INSTRUCTIONS + (
    " The hosted server also provides deep_research_ai_projects. That premium tool uses the AI Workstation publisher model, "
    "consumes the user's one-time free premium trial or AI credits only after a usable result, and may return an upgrade checkout URL. "
    "Use the nine read-only Radar tools for ordinary browsing/research; call premium deep research only when the user explicitly asks for deeper analysis."
)


def _premium_annotations() -> ToolAnnotations:
    return ToolAnnotations(
        title="Deep AI research on open-source projects",
        read_only_hint=False,
        destructive_hint=False,
        idempotent_hint=False,
        open_world_hint=True,
    )


def current_entitlement_subject() -> str:
    token: AccessToken | None = get_access_token()
    if token is None:
        raise ValueError("AUTH_REQUIRED: authenticated OAuth access is required")
    return entitlement_subject(token)


def _result(
    *,
    data: Mapping[str, Any],
    recommendations: list[Mapping[str, Any]] | None = None,
    unknowns: list[str] | None = None,
    risks: list[Mapping[str, Any]] | None = None,
) -> dict[str, Any]:
    return {
        "tool": "deep_research_ai_projects",
        "data": dict(data),
        "verified_facts": (),
        "recommendations": tuple(dict(row) for row in (recommendations or [])),
        "unknowns": tuple(unknowns or []),
        "risks": tuple(dict(row) for row in (risks or [])),
        "generated_at": utc_now_iso(),
        "request_id": "",
        "schema_version": "osi.tool-result.v1",
    }


def _rate_limited_registry(
    registry: ToolRegistry,
    limiter: HostedRateLimiter,
) -> ToolRegistry:
    """Wrap the nine public Radar provider methods with per-OAuth-subject limits.

    Hosted production always uses the expanded ``FullToolRegistry``. Keeping the
    wrapper here makes it impossible for the public hosted entrypoint to start
    with an authenticated MCP surface while accidentally bypassing application
    rate limits on the ordinary data tools.
    """

    provider = getattr(registry, "_provider", None)
    if provider is None:
        raise ValueError("hosted MCP registry does not expose a provider")
    return FullToolRegistry(HostedRateLimitedProvider(provider, limiter))


def build_hosted_mcp_server(
    registry: ToolRegistry | None = None,
    *,
    token_verifier: TokenVerifier | None = None,
    auth: AuthSettings | None = None,
    backend: HostedBackendClient | None = None,
    rate_limiter: HostedRateLimiter | None = None,
) -> MCPServer:
    """Build the OAuth-protected nine-data-tool + one-premium-tool MCP server."""

    if token_verifier is None or auth is None:
        oauth_config = load_hosted_oauth_config()
        token_verifier = token_verifier or IntrospectionTokenVerifier(oauth_config)
        auth = auth or hosted_auth_settings(oauth_config)
    backend_client = backend or HostedBackendClient(load_hosted_backend_config())
    limiter = rate_limiter or HostedRateLimiter(load_hosted_rate_limit_config())
    active_registry = _rate_limited_registry(
        registry or create_registry_from_env(),
        limiter,
    )
    server = build_mcp_server(
        active_registry,
        token_verifier=token_verifier,
        auth=auth,
        instructions=HOSTED_INSTRUCTIONS,
    )

    @server.tool(annotations=_premium_annotations())
    async def deep_research_ai_projects(
        query: str,
        focus: Literal["research", "comparison", "stack", "market_scan"] = "research",
        filters: dict[str, Any] | None = None,
        locale: Literal["zh", "en"] = "en",
    ) -> dict[str, Any]:
        """Run publisher-model deep research; first successful use is free, then AI credits apply."""

        task = str(query or "").strip()
        if not task or len(task) > 4000:
            raise ValueError("INVALID_INPUT: query must contain between 1 and 4000 characters")
        subject = current_entitlement_subject()
        # Premium calls count against both the ordinary user envelope and the
        # tighter premium burst limit before any publisher-funded model work.
        limiter.check_subject(subject, premium=True)
        try:
            payload = await asyncio.to_thread(
                backend_client.premium_research,
                subject,
                query=task,
                focus=focus,
                locale=locale,
                filters=dict(filters or {}),
            )
        except HostedBackendError as exc:
            if exc.code == "UPGRADE_REQUIRED" or exc.status == 402:
                entitlement = exc.details.get("entitlement") if isinstance(exc.details.get("entitlement"), Mapping) else {}
                try:
                    checkout = await asyncio.to_thread(backend_client.create_checkout, subject)
                except HostedBackendError:
                    checkout = {}
                return _result(
                    data={
                        "status": "upgrade_required",
                        "entitlement": dict(entitlement),
                        "checkout": dict(checkout),
                    },
                    unknowns=["Premium deep research is unavailable until the user upgrades or receives additional AI credits."],
                    risks=[
                        {
                            "code": "PAYMENT_REQUIRED",
                            "message": "No free premium trial or paid AI credit is currently available.",
                            "severity": "medium",
                        }
                    ],
                )
            raise ValueError(f"{exc.code}: {exc.message}") from None

        premium = payload.get("premium") if isinstance(payload.get("premium"), Mapping) else {}
        selection = payload.get("selection") if isinstance(payload.get("selection"), Mapping) else {}
        analysis = str(premium.get("analysis") or "").strip()
        if not analysis:
            raise ValueError("BACKEND_CONTRACT_ERROR: premium analysis text is missing")
        entitlement = premium.get("entitlement") if isinstance(premium.get("entitlement"), Mapping) else {}
        return _result(
            data={
                "status": "completed",
                "focus": str(premium.get("focus") or focus),
                "selection": dict(selection),
                "snapshot_id": str(premium.get("snapshot_id") or selection.get("snapshot_id") or ""),
                "provider_model": str(premium.get("provider_model") or ""),
                "credit_source": str(premium.get("credit_source") or ""),
                "entitlement": dict(entitlement),
            },
            recommendations=[
                {
                    "summary": analysis,
                    "rationale": (),
                    "assumptions": (),
                }
            ],
            risks=[
                {
                    "code": "PUBLISHER_MODEL_ANALYSIS",
                    "message": "The deep research narrative is model analysis over the supplied public Radar context, not an additional verified fact source.",
                    "severity": "low",
                }
            ],
        )

    return server
