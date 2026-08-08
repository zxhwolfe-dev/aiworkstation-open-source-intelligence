"""Bounded in-process rate limits for the single-process hosted MCP.

Identity comes from the verified OAuth issuer+subject pair, never from IP,
client-supplied usernames, or raw access-token strings. A production gateway may
add connection/IP abuse controls on top of these per-user application limits.
"""

from __future__ import annotations

import os
import threading
import time
from collections import OrderedDict, deque
from dataclasses import dataclass
from typing import Callable, Deque

from mcp.server.auth.middleware.auth_context import get_access_token
from mcp.server.auth.provider import AccessToken

from .hosted_auth import entitlement_subject


@dataclass(frozen=True, slots=True)
class HostedRateLimitConfig:
    per_minute: int = 60
    per_hour: int = 300
    premium_per_minute: int = 5
    max_subjects: int = 10_000


def load_hosted_rate_limit_config() -> HostedRateLimitConfig:
    try:
        per_minute = int(os.getenv("OSI_RATE_LIMIT_PER_MINUTE", "60"))
        per_hour = int(os.getenv("OSI_RATE_LIMIT_PER_HOUR", "300"))
        premium = int(os.getenv("OSI_PREMIUM_RATE_LIMIT_PER_MINUTE", "5"))
        max_subjects = int(os.getenv("OSI_RATE_LIMIT_MAX_SUBJECTS", "10000"))
    except ValueError as exc:
        raise ValueError("hosted MCP rate-limit settings must be integers") from exc
    if not 1 <= per_minute <= 10_000:
        raise ValueError("OSI_RATE_LIMIT_PER_MINUTE must be between 1 and 10000")
    if not per_minute <= per_hour <= 100_000:
        raise ValueError("OSI_RATE_LIMIT_PER_HOUR must be at least the minute limit and no more than 100000")
    if not 1 <= premium <= per_minute:
        raise ValueError("OSI_PREMIUM_RATE_LIMIT_PER_MINUTE must be between 1 and the ordinary minute limit")
    if not 100 <= max_subjects <= 100_000:
        raise ValueError("OSI_RATE_LIMIT_MAX_SUBJECTS must be between 100 and 100000")
    return HostedRateLimitConfig(
        per_minute=per_minute,
        per_hour=per_hour,
        premium_per_minute=premium,
        max_subjects=max_subjects,
    )


class HostedRateLimiter:
    """Thread-safe dual-window limiter with bounded authenticated-subject state."""

    def __init__(
        self,
        config: HostedRateLimitConfig,
        *,
        clock: Callable[[], float] = time.monotonic,
    ) -> None:
        self.config = config
        self._clock = clock
        self._ordinary: OrderedDict[str, Deque[float]] = OrderedDict()
        self._premium: OrderedDict[str, Deque[float]] = OrderedDict()
        self._lock = threading.Lock()

    def _bucket(self, mapping: OrderedDict[str, Deque[float]], subject: str) -> Deque[float]:
        bucket = mapping.get(subject)
        if bucket is None:
            while len(mapping) >= self.config.max_subjects:
                mapping.popitem(last=False)
            bucket = deque()
            mapping[subject] = bucket
        else:
            mapping.move_to_end(subject)
        return bucket

    @staticmethod
    def _trim(bucket: Deque[float], now: float, window: float) -> None:
        cutoff = now - window
        while bucket and bucket[0] <= cutoff:
            bucket.popleft()

    def check_subject(self, subject: str, *, premium: bool = False) -> None:
        value = str(subject or "").strip()
        if not value:
            raise ValueError("AUTH_REQUIRED: hosted MCP OAuth identity is required")
        now = float(self._clock())
        with self._lock:
            ordinary = self._bucket(self._ordinary, value)
            self._trim(ordinary, now, 3600.0)
            minute_count = sum(1 for timestamp in ordinary if timestamp > now - 60.0)
            if minute_count >= self.config.per_minute:
                raise ValueError("RATE_LIMITED: ordinary hosted MCP minute quota exceeded")
            if len(ordinary) >= self.config.per_hour:
                raise ValueError("RATE_LIMITED: ordinary hosted MCP hourly quota exceeded")

            if premium:
                premium_bucket = self._bucket(self._premium, value)
                self._trim(premium_bucket, now, 60.0)
                if len(premium_bucket) >= self.config.premium_per_minute:
                    raise ValueError("RATE_LIMITED: premium AI minute quota exceeded")
                premium_bucket.append(now)
            ordinary.append(now)

    def current_subject(self) -> str:
        token: AccessToken | None = get_access_token()
        if token is None:
            raise ValueError("AUTH_REQUIRED: authenticated OAuth access is required")
        return entitlement_subject(token)

    def check_current(self, tool_name: str) -> None:
        self.check_subject(
            self.current_subject(),
            premium=str(tool_name) == "deep_research_ai_projects",
        )
