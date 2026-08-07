"""Capture sanitized AI Workstation public Radar response fixtures.

The command performs anonymous read-only requests. It stores response shapes for
adapter validation while removing user queries, internal publication fields,
credentials and oversized content.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import urllib.parse
from pathlib import Path
from typing import Any, Mapping, Sequence

from .contracts import utc_now_iso
from .errors import ProviderUnavailableError, UpstreamContractError
from .http_provider import PUBLIC_API_PREFIX, JsonResponse, JsonTransport, _project_id
from .strict_http_provider import SafeUrllibJsonTransport

FIXTURE_SCHEMA_VERSION = "osi.public-contract-fixture.v1"
CAPTURE_SCHEMA_VERSION = "osi.public-contract-capture.v1"
MAX_STRING_LENGTH = 500
MAX_LIST_ITEMS = 20
MAX_DEPTH = 10
REDACTED_QUERY_TEXT = "<redacted-query>"

REMOVED_KEYS = {
    "authorization", "api_key", "apikey", "access_token", "refresh_token",
    "bearer_token", "cookie", "cookies", "secret", "password", "email",
    "client_id", "request_id", "query", "prompt", "raw", "raw_content",
    "evidence_ids", "claim_refs", "publication_version", "source_hash",
    "validated_version", "assignment_version", "prompt_version",
    "requirement_token",
}
SELECTOR_REMOVED_KEYS = frozenset(
    REMOVED_KEYS | {"understanding", "query_analysis", "requirement_spec"}
)

SAFE_HEADERS = {
    "cache-control", "content-type", "date", "etag", "last-modified", "x-request-id",
}

DEFAULT_FORMAL_QUERY = {
    "en": "Find a self-hosted RAG project with Docker and a web UI.",
    "zh": "找支持 Docker、Web 界面和私有部署的 RAG 知识库项目。",
}
DEFAULT_NO_MATCH_QUERY = {
    "en": "Find an open-source AI project.",
    "zh": "找一个开源 AI 项目。",
}
DEFAULT_NO_MATCH_FILTERS = {"category": "__osi_contract_no_match_v1__"}


def _hash_text(value: str) -> str:
    return "sha256:" + hashlib.sha256(value.encode("utf-8")).hexdigest()


def _validate_timeout(timeout: float) -> None:
    if timeout <= 0 or timeout > 240:
        raise ValueError("timeout must be greater than 0 and no more than 240 seconds")


def _redact_query_text(value: str, redact_texts: Sequence[str]) -> str:
    """Remove exact request text wherever retained public output still echoes it."""
    redacted = value
    for text in sorted(
        {str(item) for item in redact_texts if str(item or "").strip()},
        key=len,
        reverse=True,
    ):
        redacted = re.sub(re.escape(text), REDACTED_QUERY_TEXT, redacted, flags=re.IGNORECASE)
    return redacted


def sanitize_public_value(
    value: Any,
    *,
    depth: int = 0,
    redact_texts: Sequence[str] = (),
    removed_keys: frozenset[str] | set[str] = frozenset(REMOVED_KEYS),
) -> Any:
    """Return a bounded JSON-safe copy with sensitive/internal fields removed."""
    if depth > MAX_DEPTH:
        return "<max-depth>"
    if isinstance(value, Mapping):
        sanitized: dict[str, Any] = {}
        for raw_key, child in value.items():
            key = str(raw_key)
            if key.lower() in removed_keys:
                continue
            sanitized[key] = sanitize_public_value(
                child,
                depth=depth + 1,
                redact_texts=redact_texts,
                removed_keys=removed_keys,
            )
        return sanitized
    if isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)):
        rows = [
            sanitize_public_value(
                child,
                depth=depth + 1,
                redact_texts=redact_texts,
                removed_keys=removed_keys,
            )
            for child in value[:MAX_LIST_ITEMS]
        ]
        if len(value) > MAX_LIST_ITEMS:
            rows.append({"_truncated_items": len(value) - MAX_LIST_ITEMS})
        return rows
    if isinstance(value, str):
        sanitized_text = _redact_query_text(value, redact_texts)
        if len(sanitized_text) <= MAX_STRING_LENGTH:
            return sanitized_text
        return sanitized_text[:MAX_STRING_LENGTH] + f"… <truncated {len(sanitized_text) - MAX_STRING_LENGTH} chars>"
    if value is None or isinstance(value, (bool, int, float)):
        return value
    return str(value)[:MAX_STRING_LENGTH]


def _fixture(
    scenario: str,
    response: JsonResponse,
    *,
    request_fingerprint: str,
    redact_texts: Sequence[str] = (),
    removed_keys: frozenset[str] | set[str] = frozenset(REMOVED_KEYS),
) -> dict[str, Any]:
    headers = {key.lower(): value for key, value in response.headers.items() if key.lower() in SAFE_HEADERS}
    return {
        "schema_version": FIXTURE_SCHEMA_VERSION,
        "scenario": scenario,
        "request_fingerprint": request_fingerprint,
        "observed_at": response.observed_at,
        "status": response.status,
        "headers": headers,
        "payload": sanitize_public_value(
            response.payload,
            redact_texts=redact_texts,
            removed_keys=removed_keys,
        ),
    }


def _require_success(response: JsonResponse, scenario: str) -> None:
    if response.status >= 500 or response.status in {408, 425, 429}:
        raise ProviderUnavailableError(f"Public Radar capture failed for {scenario}")
    if response.status >= 400:
        raise UpstreamContractError(
            f"Public Radar rejected capture scenario: {scenario}",
            details={"status": response.status, "url": response.url},
        )


def _resolve_route_id(listing: JsonResponse, requested_id: str) -> str:
    _require_success(listing, "project-list")
    items = listing.payload.get("items")
    if not isinstance(items, Sequence) or isinstance(items, (str, bytes)):
        raise UpstreamContractError("Project-list capture is missing items")
    normalized = requested_id.strip().lower()
    for item in items:
        if not isinstance(item, Mapping):
            continue
        aliases = {
            _project_id(item),
            str(item.get("id") or "").strip().lower(),
            str(item.get("repo") or "").strip().lower(),
        }
        if normalized in aliases:
            return str(item.get("id") or _project_id(item)).strip()
    raise UpstreamContractError(
        "The requested fixture project was not found in the public project list",
        details={"project_id": requested_id},
    )


def capture_public_contracts(
    *,
    transport: JsonTransport,
    output_dir: Path,
    locale: str,
    project_id: str,
    formal_query: str,
    no_match_query: str,
    no_match_filters: Mapping[str, Any] | None = None,
    timeout: float = 30.0,
) -> dict[str, Any]:
    """Capture four sanitized public response fixtures and a manifest."""
    if locale not in {"zh", "en"}:
        raise ValueError("locale must be zh or en")
    if not project_id.strip():
        raise ValueError("project_id is required")
    if not formal_query.strip() or not no_match_query.strip():
        raise ValueError("formal_query and no_match_query are required")
    _validate_timeout(timeout)
    output_dir.mkdir(parents=True, exist_ok=True)

    listing = transport.request(
        "GET",
        f"{PUBLIC_API_PREFIX}/projects",
        query={"lang": locale, "q": project_id, "limit": 20, "offset": 0},
        timeout=timeout,
    )
    route_id = _resolve_route_id(listing, project_id)
    encoded_route_id = urllib.parse.quote(route_id, safe="")
    detail = transport.request(
        "GET",
        f"{PUBLIC_API_PREFIX}/projects/{encoded_route_id}",
        query={"lang": locale},
        timeout=timeout,
    )
    _require_success(detail, "project-detail")

    formal = transport.request(
        "POST",
        f"{PUBLIC_API_PREFIX}/selector",
        body={"lang": locale, "query": formal_query, "use_model": False, "client_id": "aiworkstation-osi-contract-capture"},
        timeout=timeout,
    )
    _require_success(formal, "selector-formal")
    no_match = transport.request(
        "POST",
        f"{PUBLIC_API_PREFIX}/selector",
        body={
            "lang": locale,
            "query": no_match_query,
            "filters": dict(no_match_filters or DEFAULT_NO_MATCH_FILTERS),
            "use_model": False,
            "client_id": "aiworkstation-osi-contract-capture",
        },
        timeout=timeout,
    )
    _require_success(no_match, "selector-no-match")

    fixtures = {
        "project-list.json": _fixture(
            "project-list", listing,
            request_fingerprint=_hash_text(f"{locale}:project-list:{project_id}"),
        ),
        "project-detail.json": _fixture(
            "project-detail", detail,
            request_fingerprint=_hash_text(f"{locale}:project-detail:{project_id}"),
        ),
        "selector-formal.json": _fixture(
            "selector-formal", formal,
            request_fingerprint=_hash_text(f"{locale}:selector-formal:{formal_query}"),
            redact_texts=(formal_query,),
            removed_keys=SELECTOR_REMOVED_KEYS,
        ),
        "selector-no-match.json": _fixture(
            "selector-no-match", no_match,
            request_fingerprint=_hash_text(
                f"{locale}:selector-no-match:{json.dumps(dict(no_match_filters or DEFAULT_NO_MATCH_FILTERS), sort_keys=True, separators=(',', ':'))}"
            ),
            redact_texts=(no_match_query,),
            removed_keys=SELECTOR_REMOVED_KEYS,
        ),
    }
    for filename, payload in fixtures.items():
        (output_dir / filename).write_text(
            json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )

    manifest = {
        "schema_version": CAPTURE_SCHEMA_VERSION,
        "generated_at": utc_now_iso(),
        "locale": locale,
        "project_id": project_id,
        "fixture_files": sorted(fixtures),
        "sanitization": {
            "removed_keys": sorted(REMOVED_KEYS),
            "selector_removed_keys": sorted(SELECTOR_REMOVED_KEYS),
            "max_string_length": MAX_STRING_LENGTH,
            "max_list_items": MAX_LIST_ITEMS,
            "stores_query_text": False,
            "query_text_redaction": "selector_metadata_removed_plus_exact_echo_redaction",
        },
    }
    (output_dir / "manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    return manifest


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="osi-capture-contracts")
    parser.add_argument("--base-url", default="https://aiworkstation.cn")
    parser.add_argument("--locale", choices=("zh", "en"), default="en")
    parser.add_argument("--project-id", default="infiniflow/ragflow")
    parser.add_argument("--formal-query")
    parser.add_argument("--no-match-query")
    parser.add_argument("--timeout", type=float, default=30.0)
    parser.add_argument("--output-dir", type=Path, required=True)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    formal_query = args.formal_query or DEFAULT_FORMAL_QUERY[args.locale]
    no_match_query = args.no_match_query or DEFAULT_NO_MATCH_QUERY[args.locale]
    try:
        manifest = capture_public_contracts(
            transport=SafeUrllibJsonTransport(args.base_url),
            output_dir=args.output_dir,
            locale=args.locale,
            project_id=args.project_id,
            formal_query=formal_query,
            no_match_query=no_match_query,
            timeout=args.timeout,
        )
    except (ProviderUnavailableError, UpstreamContractError, ValueError) as exc:
        print(json.dumps({"ok": False, "error": {"code": getattr(exc, "code", "INVALID_CONFIGURATION"), "message": str(exc)}}, ensure_ascii=False, indent=2))
        return 1
    print(json.dumps({"ok": True, **manifest}, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
