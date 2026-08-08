"""Machine-verifiable OAuth/remote-MCP evidence for Hosted Private Alpha."""

from __future__ import annotations

import json
import re
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any, Mapping

from .contracts import TOOL_NAMES
from .endpoint_policy import validate_mcp_endpoint

HOSTED_REMOTE_SCHEMA = "osi.remote-smoke.v2"
HOSTED_PREMIUM_TOOL = "deep_research_ai_projects"
MAX_METADATA_BYTES = 256 * 1024


class _NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):  # type: ignore[no-untyped-def]
        return None


def expected_hosted_tools() -> tuple[str, ...]:
    return tuple(TOOL_NAMES) + (HOSTED_PREMIUM_TOOL,)


def _origin_parts(url: str) -> tuple[str, str, int] | None:
    parsed = urllib.parse.urlsplit(url)
    if parsed.scheme not in {"http", "https"} or not parsed.hostname:
        return None
    try:
        port = parsed.port
    except ValueError:
        return None
    if port is None:
        port = 443 if parsed.scheme == "https" else 80
    return parsed.scheme, parsed.hostname.lower(), port


def _safe_metadata_url(endpoint: str, value: str) -> str:
    metadata = str(value or "").strip()
    parsed = urllib.parse.urlsplit(metadata)
    if (
        parsed.scheme != "https"
        or not parsed.hostname
        or parsed.username
        or parsed.password
        or parsed.query
        or parsed.fragment
    ):
        raise ValueError("resource metadata URL must be credential-free HTTPS without query/fragment")
    if _origin_parts(metadata) != _origin_parts(endpoint):
        raise ValueError("resource metadata URL must stay on the hosted MCP origin")
    if parsed.path not in {
        "/.well-known/oauth-protected-resource",
        "/.well-known/oauth-protected-resource/mcp",
    }:
        raise ValueError("resource metadata URL uses an unexpected path")
    return metadata


def _extract_resource_metadata(header: str) -> str:
    text = str(header or "")
    quoted = re.search(r'resource_metadata\s*=\s*"([^"]+)"', text, flags=re.IGNORECASE)
    if quoted:
        return quoted.group(1).strip()
    token = re.search(r"resource_metadata\s*=\s*([^,\s]+)", text, flags=re.IGNORECASE)
    return token.group(1).strip() if token else ""


def _read_json_response(response: Any) -> Mapping[str, Any]:
    raw = response.read(MAX_METADATA_BYTES + 1)
    if len(raw) > MAX_METADATA_BYTES:
        raise ValueError("OAuth metadata response is too large")
    payload = json.loads(raw.decode("utf-8"))
    if not isinstance(payload, Mapping):
        raise ValueError("OAuth metadata response must be a JSON object")
    return payload


def inspect_oauth_boundary(
    endpoint: str,
    *,
    expected_issuer: str,
    timeout_seconds: float = 10.0,
    opener: Any | None = None,
) -> dict[str, Any]:
    """Verify 401 discovery and RFC 9728 metadata without ever handling a token."""

    normalized_endpoint = validate_mcp_endpoint(endpoint, allow_http_localhost=False)
    issuer = str(expected_issuer or "").strip().rstrip("/")
    parsed_issuer = urllib.parse.urlsplit(issuer)
    errors: list[str] = []
    if parsed_issuer.scheme != "https" or not parsed_issuer.hostname:
        errors.append("expected OAuth issuer must be HTTPS")

    active_opener = opener or urllib.request.build_opener(_NoRedirect())
    challenge_status = 0
    www_authenticate = ""
    request = urllib.request.Request(
        normalized_endpoint,
        data=b'{"jsonrpc":"2.0","id":"auth-probe","method":"tools/list","params":{}}',
        method="POST",
        headers={
            "accept": "application/json, text/event-stream",
            "content-type": "application/json",
            "user-agent": "AI-Workstation-OSI-Hosted-Probe/1.0",
        },
    )
    try:
        response = active_opener.open(request, timeout=timeout_seconds)
        challenge_status = int(getattr(response, "status", 0) or 0)
        www_authenticate = str(response.headers.get("WWW-Authenticate") or "")
        response.read(4096)
    except urllib.error.HTTPError as exc:
        challenge_status = int(exc.code)
        www_authenticate = str(exc.headers.get("WWW-Authenticate") or "")
        try:
            exc.read(4096)
        except OSError:
            pass
    except (urllib.error.URLError, TimeoutError, OSError) as exc:
        errors.append(f"unauthenticated MCP probe failed: {type(exc).__name__}")

    if challenge_status != 401:
        errors.append(f"unauthenticated MCP request returned HTTP {challenge_status or 'unknown'}, expected 401")
    if not www_authenticate.lower().startswith("bearer"):
        errors.append("401 response is missing a Bearer WWW-Authenticate challenge")

    metadata_url = _extract_resource_metadata(www_authenticate)
    if not metadata_url:
        errors.append("WWW-Authenticate challenge is missing resource_metadata")
    else:
        try:
            metadata_url = _safe_metadata_url(normalized_endpoint, metadata_url)
        except ValueError as exc:
            errors.append(str(exc))
            metadata_url = ""

    metadata_payload: Mapping[str, Any] = {}
    metadata_status = 0
    if metadata_url:
        metadata_request = urllib.request.Request(
            metadata_url,
            method="GET",
            headers={
                "accept": "application/json",
                "user-agent": "AI-Workstation-OSI-Hosted-Probe/1.0",
            },
        )
        try:
            with active_opener.open(metadata_request, timeout=timeout_seconds) as response:
                metadata_status = int(getattr(response, "status", 0) or 0)
                metadata_payload = _read_json_response(response)
        except urllib.error.HTTPError as exc:
            metadata_status = int(exc.code)
            errors.append(f"protected-resource metadata returned HTTP {exc.code}")
        except (urllib.error.URLError, TimeoutError, OSError, ValueError, UnicodeDecodeError, json.JSONDecodeError) as exc:
            errors.append(f"protected-resource metadata fetch failed: {type(exc).__name__}")

    resource = str(metadata_payload.get("resource") or "").strip().rstrip("/")
    authorization_servers_raw = metadata_payload.get("authorization_servers")
    authorization_servers = (
        [str(value).strip().rstrip("/") for value in authorization_servers_raw if str(value).strip()]
        if isinstance(authorization_servers_raw, (list, tuple))
        else []
    )
    bearer_methods_raw = metadata_payload.get("bearer_methods_supported")
    bearer_methods = (
        [str(value).strip().lower() for value in bearer_methods_raw if str(value).strip()]
        if isinstance(bearer_methods_raw, (list, tuple))
        else []
    )

    if metadata_url and metadata_status != 200:
        errors.append("protected-resource metadata did not return HTTP 200")
    if resource != normalized_endpoint.rstrip("/"):
        errors.append("protected-resource metadata resource does not match the exact MCP endpoint")
    if issuer and issuer not in authorization_servers:
        errors.append("protected-resource metadata does not advertise the expected OAuth issuer")
    if bearer_methods and "header" not in bearer_methods:
        errors.append("protected-resource metadata does not support bearer tokens in the Authorization header")

    return {
        "ok": not errors,
        "endpoint": normalized_endpoint,
        "expected_issuer": issuer,
        "challenge_status": challenge_status,
        "bearer_challenge": bool(www_authenticate.lower().startswith("bearer")),
        "resource_metadata_url": metadata_url,
        "metadata_status": metadata_status,
        "resource": resource,
        "authorization_servers": authorization_servers,
        "bearer_methods_supported": bearer_methods,
        "errors": errors,
    }


def _load_json(path: Path) -> Mapping[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, Mapping):
        raise ValueError(f"{path} must contain a JSON object")
    return payload


def validate_hosted_remote_evidence(
    path: Path | None,
    *,
    candidate_commit: str,
    expected_endpoint: str,
    expected_issuer: str,
) -> dict[str, Any]:
    """Fail closed unless a hosted OAuth smoke report proves the deployed boundary."""

    if path is None:
        return {
            "ok": False,
            "supplied": False,
            "path": "",
            "errors": ["Hosted remote evidence was not supplied"],
        }

    evidence_path = path.expanduser().resolve()
    try:
        payload = _load_json(evidence_path)
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        return {
            "ok": False,
            "supplied": True,
            "path": str(evidence_path),
            "errors": [f"Hosted remote evidence is unreadable: {exc}"],
        }

    errors: list[str] = []
    try:
        normalized_endpoint = validate_mcp_endpoint(expected_endpoint, allow_http_localhost=False)
    except ValueError as exc:
        normalized_endpoint = str(expected_endpoint or "").strip()
        errors.append(f"expected hosted MCP endpoint is invalid: {exc}")
    issuer = str(expected_issuer or "").strip().rstrip("/")
    report_endpoint = str(payload.get("endpoint") or "").strip().rstrip("/")
    report_commit = str(payload.get("commit") or "").strip()
    profile = str(payload.get("profile") or "").strip()
    auth = payload.get("auth") if isinstance(payload.get("auth"), Mapping) else {}
    boundary = payload.get("oauth_boundary") if isinstance(payload.get("oauth_boundary"), Mapping) else {}
    checks = {
        str(item.get("id") or ""): bool(item.get("ok"))
        for item in payload.get("checks") or []
        if isinstance(item, Mapping)
    }
    discovered = [str(value) for value in payload.get("tools") or []]
    expected_tools = list(expected_hosted_tools())
    search = payload.get("search") if isinstance(payload.get("search"), Mapping) else {}

    if payload.get("schema_version") != HOSTED_REMOTE_SCHEMA:
        errors.append("Hosted remote evidence schema is not supported")
    if payload.get("ok") is not True:
        errors.append("Hosted remote smoke report did not pass")
    if not candidate_commit or report_commit != candidate_commit:
        errors.append("Hosted remote evidence belongs to a different candidate commit")
    if report_endpoint != normalized_endpoint.rstrip("/"):
        errors.append("Hosted remote evidence used a different MCP endpoint")
    if profile != "hosted":
        errors.append("Hosted remote evidence was not produced with the hosted profile")
    if str(auth.get("mode") or "") not in {"oauth", "bearer-env"}:
        errors.append("Hosted remote evidence did not use authenticated MCP access")
    if boundary.get("ok") is not True or int(boundary.get("challenge_status") or 0) != 401:
        errors.append("Hosted remote evidence did not prove the unauthenticated 401 OAuth boundary")
    if str(boundary.get("resource") or "").strip().rstrip("/") != normalized_endpoint.rstrip("/"):
        errors.append("Hosted OAuth resource metadata is bound to a different resource")
    advertised = [str(value).strip().rstrip("/") for value in boundary.get("authorization_servers") or []]
    if not issuer or issuer not in advertised:
        errors.append("Hosted OAuth resource metadata does not advertise the expected issuer")
    if set(discovered) != set(expected_tools) or len(discovered) != len(expected_tools):
        errors.append("Hosted remote evidence did not discover exactly nine standard tools plus Premium")
    for check_id in ("tool-set", "tool-annotations", "search-invocation"):
        if checks.get(check_id) is not True:
            errors.append(f"Hosted remote smoke check did not pass: {check_id}")
    if search.get("is_error") is not False or search.get("tool") != "search_ai_projects":
        errors.append("Hosted remote evidence did not prove a successful standard search invocation")
    if not str(payload.get("protocol_version") or "").strip():
        errors.append("Hosted remote evidence is missing the negotiated MCP protocol version")

    return {
        "ok": not errors,
        "supplied": True,
        "path": str(evidence_path),
        "candidate_commit": candidate_commit,
        "report_commit": report_commit,
        "endpoint": report_endpoint,
        "expected_issuer": issuer,
        "auth_mode": str(auth.get("mode") or ""),
        "protocol_version": str(payload.get("protocol_version") or ""),
        "tools": discovered,
        "oauth_boundary_verified": boundary.get("ok") is True,
        "search_verified": checks.get("search-invocation") is True,
        "errors": errors,
    }
