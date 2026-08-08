from __future__ import annotations

import io
import json
import unittest
import urllib.error
from unittest.mock import patch

from aiworkstation_osi.hosted_backend import (
    HostedBackendClient,
    HostedBackendConfig,
    HostedBackendError,
    load_hosted_backend_config,
)


class FakeResponse:
    def __init__(self, payload, status=200):
        self.status = status
        self.raw = json.dumps(payload).encode("utf-8")

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False

    def read(self, limit=-1):
        return self.raw if limit < 0 else self.raw[:limit]


class FakeOpener:
    def __init__(self, responses):
        self.responses = list(responses)
        self.requests = []

    def open(self, request, timeout=0):
        self.requests.append((request, timeout))
        if not self.responses:
            raise AssertionError("unexpected request")
        item = self.responses.pop(0)
        if isinstance(item, Exception):
            raise item
        return item


class HostedBackendTests(unittest.TestCase):
    def setUp(self) -> None:
        self.config = HostedBackendConfig(
            base_url="https://aiworkstation.cn",
            service_token="service-secret",
            timeout_seconds=5,
        )

    def test_entitlement_sends_only_service_token_and_opaque_subject(self) -> None:
        opener = FakeOpener([FakeResponse({"ok": True, "entitlement": {"plan": "free"}})])
        client = HostedBackendClient(self.config)
        client._opener = opener
        result = client.entitlement("oidc_opaque")
        self.assertEqual(result["plan"], "free")
        request, timeout = opener.requests[0]
        self.assertEqual(timeout, 5)
        self.assertEqual(request.full_url, "https://aiworkstation.cn/api/v1/ai/githubai/mcp/entitlement")
        headers = {key.lower(): value for key, value in request.header_items()}
        self.assertEqual(headers["x-aiworkstation-mcp-service-token"], "service-secret")
        self.assertEqual(headers["x-aiworkstation-mcp-subject"], "oidc_opaque")
        self.assertNotIn("authorization", headers)

    def test_premium_research_contract_is_bounded_to_expected_payload(self) -> None:
        opener = FakeOpener([
            FakeResponse({
                "ok": True,
                "selection": {"snapshot_id": "sha256:test", "projects": []},
                "premium": {"analysis": "result", "entitlement": {"ai_credits": 0}},
            })
        ])
        client = HostedBackendClient(self.config)
        client._opener = opener
        result = client.premium_research(
            "oidc_opaque",
            query="Deep research",
            focus="research",
            locale="en",
            filters={"deployment": "docker"},
        )
        self.assertEqual(result["premium"]["analysis"], "result")
        request, _ = opener.requests[0]
        body = json.loads(request.data.decode("utf-8"))
        self.assertEqual(body["query"], "Deep research")
        self.assertEqual(body["focus"], "research")
        self.assertEqual(body["filters"], {"deployment": "docker"})
        self.assertNotIn("service-secret", json.dumps(body))

    def test_upgrade_error_exposes_only_safe_entitlement_details(self) -> None:
        payload = {
            "detail": {
                "code": "UPGRADE_REQUIRED",
                "message": "upgrade",
                "entitlement": {"trial_available": False, "ai_credits": 0},
                "provider_customer_id": "private-customer",
            }
        }
        raw = json.dumps(payload).encode("utf-8")
        error = urllib.error.HTTPError(
            "https://aiworkstation.cn/api/v1/ai/githubai/mcp/premium-research",
            402,
            "Payment Required",
            {},
            io.BytesIO(raw),
        )
        client = HostedBackendClient(self.config)
        client._opener = FakeOpener([error])
        with self.assertRaises(HostedBackendError) as context:
            client.premium_research(
                "oidc_opaque", query="Deep", focus="research", locale="en"
            )
        exc = context.exception
        self.assertEqual(exc.code, "UPGRADE_REQUIRED")
        self.assertEqual(exc.status, 402)
        self.assertEqual(exc.details["entitlement"]["ai_credits"], 0)
        self.assertNotIn("provider_customer_id", repr(exc.details))
        self.assertNotIn("private-customer", repr(exc.details))

    def test_checkout_rejects_non_https_provider_url(self) -> None:
        client = HostedBackendClient(self.config)
        client._opener = FakeOpener([
            FakeResponse({"ok": True, "checkout": {"checkout_url": "javascript:alert(1)"}})
        ])
        with self.assertRaises(HostedBackendError) as context:
            client.create_checkout("oidc_opaque")
        self.assertEqual(context.exception.code, "BACKEND_CONTRACT_ERROR")

    def test_config_requires_https_backend_and_service_secret(self) -> None:
        good = {
            "OSI_BACKEND_BASE_URL": "https://aiworkstation.cn",
            "OSI_BACKEND_SERVICE_TOKEN": "secret",
        }
        with patch.dict("os.environ", good, clear=True):
            config = load_hosted_backend_config()
        self.assertEqual(config.base_url, "https://aiworkstation.cn")

        bad = dict(good)
        bad["OSI_BACKEND_BASE_URL"] = "http://aiworkstation.cn"
        with patch.dict("os.environ", bad, clear=True), self.assertRaises(ValueError):
            load_hosted_backend_config()
        bad = dict(good)
        bad["OSI_BACKEND_SERVICE_TOKEN"] = ""
        with patch.dict("os.environ", bad, clear=True), self.assertRaises(ValueError):
            load_hosted_backend_config()


if __name__ == "__main__":
    unittest.main()
