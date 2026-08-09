"""Machine-verifiable evidence for anonymous public Hosted Private Alpha."""

from __future__ import annotations

import json
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any, Mapping

from .contracts import TOOL_NAMES
from .endpoint_policy import validate_mcp_endpoint
from .release_identity import release_commit_from_server_version

PUBLIC_HOSTED_REMOTE_SCHEMA = "osi.remote-smoke.public.v1"
PUBLIC_GATEWAY_HEADER = "X-OSI-Hosted-Gateway-Policy"
PUBLIC_GATEWAY_POLICY = "tls-ip-rate-limited"


class _NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):  # type: ignore[no-untyped-def]
        return None


def inspect_public_gateway(
    endpoint: str,
    *,
    timeout_seconds: float = 10.0,
    opener: Any | None = None,
) -> dict[str, Any]:
    """Verify HTTPS reachability and the explicit anonymous gateway policy header."""

    normalized = validate_mcp_endpoint(endpoint, allow_http_localhost=False)
    active_opener = opener or urllib.request.build_opener(_NoRedirect())
    status = 0
    policy = ""
    errors: list[str] = []
    request = urllib.request.Request(
        normalized,
        method="GET",
        headers={"user-agent": "AI-Workstation-OSI-Public-Hosted-Probe/1.0"},
    )
    try:
        with active_opener.open(request, timeout=timeout_seconds) as response:
            status = int(getattr(response, "status", 0) or 0)
            policy = str(response.headers.get(PUBLIC_GATEWAY_HEADER) or "").strip()
            response.read(4096)
    except urllib.error.HTTPError as exc:
        status = int(exc.code)
        policy = str(exc.headers.get(PUBLIC_GATEWAY_HEADER) or "").strip()
        try:
            exc.read(4096)
        except OSError:
            pass
    except (urllib.error.URLError, TimeoutError, OSError) as exc:
        errors.append(f"public Hosted gateway probe failed: {type(exc).__name__}")

    if status <= 0:
        errors.append("public Hosted gateway did not return an HTTP response")
    if policy != PUBLIC_GATEWAY_POLICY:
        errors.append(
            f"public Hosted gateway is missing {PUBLIC_GATEWAY_HEADER}: {PUBLIC_GATEWAY_POLICY}"
        )
    return {
        "ok": not errors,
        "endpoint": normalized,
        "status": status,
        "policy_header": PUBLIC_GATEWAY_HEADER,
        "policy": policy,
        "errors": errors,
    }


def _load_json(path: Path) -> Mapping[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, Mapping):
        raise ValueError(f"{path} must contain a JSON object")
    return payload


def validate_public_hosted_remote_evidence(
    path: Path | None,
    *,
    candidate_commit: str,
    expected_endpoint: str,
) -> dict[str, Any]:
    """Fail closed unless a real anonymous Hosted smoke proves the deployed boundary."""

    if path is None:
        return {
            "ok": False,
            "supplied": False,
            "path": "",
            "errors": ["Public Hosted remote evidence was not supplied"],
        }

    evidence_path = path.expanduser().resolve()
    try:
        payload = _load_json(evidence_path)
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        return {
            "ok": False,
            "supplied": True,
            "path": str(evidence_path),
            "errors": [f"Public Hosted remote evidence is unreadable: {exc}"],
        }

    errors: list[str] = []
    try:
        normalized_endpoint = validate_mcp_endpoint(expected_endpoint, allow_http_localhost=False)
    except ValueError as exc:
        normalized_endpoint = str(expected_endpoint or "").strip()
        errors.append(f"expected Hosted MCP endpoint is invalid: {exc}")

    normalized_candidate = str(candidate_commit or "").strip().lower()
    report_endpoint = str(payload.get("endpoint") or "").strip().rstrip("/")
    report_commit = str(payload.get("commit") or "").strip().lower()
    server_version = str(payload.get("server_version") or "").strip()
    deployment_commit = str(payload.get("deployment_commit") or "").strip().lower()
    auth = payload.get("auth") if isinstance(payload.get("auth"), Mapping) else {}
    gateway = payload.get("gateway_boundary") if isinstance(payload.get("gateway_boundary"), Mapping) else {}
    checks = {
        str(item.get("id") or ""): bool(item.get("ok"))
        for item in payload.get("checks") or []
        if isinstance(item, Mapping)
    }
    discovered = [str(value) for value in payload.get("tools") or []]
    search = payload.get("search") if isinstance(payload.get("search"), Mapping) else {}

    if payload.get("schema_version") != PUBLIC_HOSTED_REMOTE_SCHEMA:
        errors.append("Public Hosted remote evidence schema is not supported")
    if payload.get("ok") is not True:
        errors.append("Public Hosted remote smoke report did not pass")
    if payload.get("profile") != "hosted-public":
        errors.append("Public Hosted remote evidence was not produced with hosted-public profile")
    if str(auth.get("mode") or "") != "none":
        errors.append("Public Hosted remote evidence must use auth mode none")
    if not normalized_candidate or report_commit != normalized_candidate:
        errors.append("Public Hosted remote evidence belongs to a different candidate commit")
    if deployment_commit != normalized_candidate:
        errors.append("Public Hosted remote evidence was produced by a different deployed server commit")
    if release_commit_from_server_version(server_version) != deployment_commit:
        errors.append("Public Hosted server version does not encode the reported deployment commit")
    if checks.get("deployment-identity") is not True:
        errors.append("Public Hosted smoke did not pass the deployment identity check")
    if report_endpoint != normalized_endpoint.rstrip("/"):
        errors.append("Public Hosted remote evidence used a different MCP endpoint")

    if gateway.get("ok") is not True:
        errors.append("Public Hosted remote evidence did not prove the gateway abuse-control boundary")
    if str(gateway.get("policy") or "") != PUBLIC_GATEWAY_POLICY:
        errors.append("Public Hosted gateway policy header does not match the expected policy")

    expected_tools = list(TOOL_NAMES)
    if set(discovered) != set(expected_tools) or len(discovered) != len(expected_tools):
        errors.append("Public Hosted remote evidence did not discover exactly nine standard tools")
    for check_id in ("tool-set", "tool-annotations", "search-invocation"):
        if checks.get(check_id) is not True:
            errors.append(f"Public Hosted remote smoke check did not pass: {check_id}")
    if search.get("is_error") is not False or search.get("tool") != "search_ai_projects":
        errors.append("Public Hosted remote evidence did not prove a successful standard search invocation")
    if not str(payload.get("protocol_version") or "").strip():
        errors.append("Public Hosted remote evidence is missing the negotiated MCP protocol version")

    return {
        "ok": not errors,
        "supplied": True,
        "path": str(evidence_path),
        "candidate_commit": normalized_candidate,
        "report_commit": report_commit,
        "deployment_commit": deployment_commit,
        "server_version": server_version,
        "endpoint": report_endpoint,
        "auth_mode": str(auth.get("mode") or ""),
        "protocol_version": str(payload.get("protocol_version") or ""),
        "tools": discovered,
        "gateway_policy_verified": gateway.get("ok") is True,
        "deployment_identity_verified": checks.get("deployment-identity") is True and deployment_commit == normalized_candidate,
        "search_verified": checks.get("search-invocation") is True,
        "errors": errors,
    }
