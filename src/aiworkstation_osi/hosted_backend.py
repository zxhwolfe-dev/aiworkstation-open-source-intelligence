"""Private AI Workstation backend client for hosted MCP premium operations."""

from __future__ import annotations

import json
import os
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass
from typing import Any, Mapping

from .hosted_auth import _https_url

SERVICE_TOKEN_HEADER = "x-aiworkstation-mcp-service-token"
SUBJECT_HEADER = "x-aiworkstation-mcp-subject"
MAX_RESPONSE_BYTES = 2 * 1024 * 1024


class _NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):  # type: ignore[no-untyped-def]
        return None


class HostedBackendError(RuntimeError):
    def __init__(self, code: str, message: str, *, status: int = 500, details: Mapping[str, Any] | None = None) -> None:
        super().__init__(message)
        self.code = str(code)
        self.message = str(message)
        self.status = int(status)
        self.details = dict(details or {})


@dataclass(frozen=True, slots=True)
class HostedBackendConfig:
    base_url: str
    service_token: str
    timeout_seconds: float = 30.0


def load_hosted_backend_config() -> HostedBackendConfig:
    base_url = _https_url(
        os.getenv("OSI_BACKEND_BASE_URL", "https://aiworkstation.cn"),
        "OSI_BACKEND_BASE_URL",
    )
    service_token = str(os.getenv("OSI_BACKEND_SERVICE_TOKEN") or "").strip()
    if not service_token or len(service_token) > 4096:
        raise ValueError("OSI_BACKEND_SERVICE_TOKEN is required")
    try:
        timeout = float(os.getenv("OSI_BACKEND_TIMEOUT_SECONDS", "30"))
    except ValueError as exc:
        raise ValueError("OSI_BACKEND_TIMEOUT_SECONDS must be numeric") from exc
    if timeout <= 0 or timeout > 120:
        raise ValueError("OSI_BACKEND_TIMEOUT_SECONDS must be greater than 0 and no more than 120")
    return HostedBackendConfig(base_url=base_url, service_token=service_token, timeout_seconds=timeout)


class HostedBackendClient:
    def __init__(self, config: HostedBackendConfig) -> None:
        self.config = config
        self._opener = urllib.request.build_opener(_NoRedirect())

    def _request(
        self,
        method: str,
        path: str,
        *,
        subject: str,
        body: Mapping[str, Any] | None = None,
    ) -> Mapping[str, Any]:
        subject_value = str(subject or "").strip()
        if not subject_value or len(subject_value) > 191:
            raise HostedBackendError("AUTH_REQUIRED", "Hosted MCP identity is unavailable", status=401)
        if not path.startswith("/api/v1/ai/githubai/mcp/") or "?" in path or "#" in path:
            raise ValueError("unsupported hosted backend path")
        url = self.config.base_url + path
        headers = {
            "accept": "application/json",
            "user-agent": "AI-Workstation-OSI-Hosted-MCP/1.0",
            SERVICE_TOKEN_HEADER: self.config.service_token,
            SUBJECT_HEADER: subject_value,
        }
        data = None
        if body is not None:
            headers["content-type"] = "application/json"
            data = json.dumps(dict(body), ensure_ascii=False, separators=(",", ":")).encode("utf-8")
        request = urllib.request.Request(url, method=method, headers=headers, data=data)
        try:
            with self._opener.open(request, timeout=self.config.timeout_seconds) as response:
                raw = response.read(MAX_RESPONSE_BYTES + 1)
                status = int(response.status)
        except urllib.error.HTTPError as exc:
            raw = exc.read(MAX_RESPONSE_BYTES + 1)
            status = int(exc.code)
            payload = self._decode(raw)
            detail = payload.get("detail") if isinstance(payload.get("detail"), Mapping) else {}
            code = str(detail.get("code") or "BACKEND_ERROR")
            message = str(detail.get("message") or "AI Workstation backend request failed")
            safe_details: dict[str, Any] = {}
            entitlement = detail.get("entitlement")
            if isinstance(entitlement, Mapping):
                safe_details["entitlement"] = dict(entitlement)
            raise HostedBackendError(code, message, status=status, details=safe_details) from None
        except (urllib.error.URLError, TimeoutError, OSError) as exc:
            raise HostedBackendError(
                "BACKEND_UNAVAILABLE",
                "AI Workstation premium backend is temporarily unavailable",
                status=503,
            ) from exc
        if status != 200:
            raise HostedBackendError("BACKEND_ERROR", "AI Workstation backend request failed", status=status)
        if len(raw) > MAX_RESPONSE_BYTES:
            raise HostedBackendError("BACKEND_RESPONSE_TOO_LARGE", "AI Workstation backend response is too large", status=502)
        payload = self._decode(raw)
        if payload.get("ok") is not True:
            raise HostedBackendError("BACKEND_CONTRACT_ERROR", "AI Workstation backend returned an invalid contract", status=502)
        return payload

    @staticmethod
    def _decode(raw: bytes) -> Mapping[str, Any]:
        if len(raw) > MAX_RESPONSE_BYTES:
            return {}
        try:
            payload = json.loads(raw.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError):
            return {}
        return payload if isinstance(payload, Mapping) else {}

    def entitlement(self, subject: str) -> Mapping[str, Any]:
        payload = self._request("GET", "/api/v1/ai/githubai/mcp/entitlement", subject=subject)
        value = payload.get("entitlement")
        if not isinstance(value, Mapping):
            raise HostedBackendError("BACKEND_CONTRACT_ERROR", "Entitlement response is invalid", status=502)
        return dict(value)

    def premium_research(
        self,
        subject: str,
        *,
        query: str,
        focus: str,
        locale: str,
        filters: Mapping[str, Any] | None = None,
    ) -> Mapping[str, Any]:
        payload = self._request(
            "POST",
            "/api/v1/ai/githubai/mcp/premium-research",
            subject=subject,
            body={
                "query": query,
                "focus": focus,
                "locale": locale,
                "filters": dict(filters or {}),
            },
        )
        premium = payload.get("premium")
        selection = payload.get("selection")
        if not isinstance(premium, Mapping) or not isinstance(selection, Mapping):
            raise HostedBackendError("BACKEND_CONTRACT_ERROR", "Premium research response is invalid", status=502)
        return {"premium": dict(premium), "selection": dict(selection)}

    def create_checkout(self, subject: str) -> Mapping[str, Any]:
        payload = self._request("POST", "/api/v1/ai/githubai/mcp/checkout", subject=subject, body={})
        checkout = payload.get("checkout")
        if not isinstance(checkout, Mapping):
            raise HostedBackendError("BACKEND_CONTRACT_ERROR", "Checkout response is invalid", status=502)
        url = str(checkout.get("checkout_url") or "").strip()
        parsed = urllib.parse.urlsplit(url)
        if parsed.scheme != "https" or not parsed.hostname:
            raise HostedBackendError("BACKEND_CONTRACT_ERROR", "Checkout URL is invalid", status=502)
        return dict(checkout)
