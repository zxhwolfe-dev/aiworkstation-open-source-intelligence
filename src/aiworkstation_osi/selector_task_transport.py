"""Translate public selector calls into the bounded asynchronous task contract.

The AI Workstation website already treats selector execution as a long-running
operation. This transport adapter preserves the existing JsonTransport interface
for the hardened OSI provider while avoiding one long-held HTTP request.
"""

from __future__ import annotations

import re
import time
import urllib.parse
from collections.abc import Callable
from threading import BoundedSemaphore
from typing import Any, Mapping

from .errors import (
    ProviderOverloadedError,
    ProviderUnavailableError,
    UpstreamContractError,
)
from .http_provider import PUBLIC_API_PREFIX, JsonResponse, JsonTransport

SELECTOR_PATH = f"{PUBLIC_API_PREFIX}/selector"
SELECTOR_TASKS_PATH = f"{PUBLIC_API_PREFIX}/selector/tasks"
DEFAULT_SELECTOR_TASK_TIMEOUT_SECONDS = 60.0
DEFAULT_SELECTOR_TASK_POLL_INTERVAL_SECONDS = 1.0
MAX_SELECTOR_TASK_TIMEOUT_SECONDS = 240.0
MAX_SELECTOR_TASK_ID_LENGTH = 200
_TASK_ID_PATTERN = re.compile(r"^[A-Za-z0-9._~-]{1,200}$")
_TRANSIENT_STATUSES = {408, 425, 429}
_ACTIVE_STATES = {"queued", "running", "cancelling"}
_TERMINAL_FAILURE_STATES = {"failed", "cancelled", "interrupted"}


def _validate_selector_task_settings(task_timeout: float, poll_interval: float) -> None:
    if task_timeout <= 0 or task_timeout > MAX_SELECTOR_TASK_TIMEOUT_SECONDS:
        raise ValueError(
            f"selector task timeout must be greater than 0 and no more than {int(MAX_SELECTOR_TASK_TIMEOUT_SECONDS)} seconds"
        )
    if poll_interval < 0 or poll_interval > 10:
        raise ValueError("selector task poll interval must be between 0 and 10 seconds")


def _raise_for_task_response(response: JsonResponse, *, stage: str) -> None:
    if response.status in _TRANSIENT_STATUSES or response.status >= 500:
        raise ProviderUnavailableError("AI Workstation selector task service is temporarily unavailable")
    if response.status >= 400:
        # A task that disappears immediately after successful creation is an
        # availability failure, not evidence that the user's query is invalid.
        if stage == "poll" and response.status == 404:
            raise ProviderUnavailableError("AI Workstation selector task expired before completion")
        raise UpstreamContractError(
            "AI Workstation rejected the selector task request",
            details={"stage": stage, "status": response.status},
        )


class SelectorTaskJsonTransport:
    """Intercept synchronous selector requests and execute them through task polling."""

    def __init__(
        self,
        delegate: JsonTransport,
        *,
        task_timeout: float = DEFAULT_SELECTOR_TASK_TIMEOUT_SECONDS,
        poll_interval: float = DEFAULT_SELECTOR_TASK_POLL_INTERVAL_SECONDS,
        clock: Callable[[], float] = time.monotonic,
        sleeper: Callable[[float], None] = time.sleep,
        max_concurrent: int = 8,
        queue_timeout: float = 2.0,
    ) -> None:
        _validate_selector_task_settings(float(task_timeout), float(poll_interval))
        self.delegate = delegate
        self.task_timeout = float(task_timeout)
        self.poll_interval = float(poll_interval)
        self._clock = clock
        self._sleep = sleeper
        if max_concurrent < 1:
            raise ValueError("max_concurrent must be positive")
        if queue_timeout < 0:
            raise ValueError("queue_timeout must not be negative")
        self._capacity = BoundedSemaphore(max_concurrent)
        self.queue_timeout = float(queue_timeout)

    def request(
        self,
        method: str,
        path: str,
        *,
        query: Mapping[str, Any] | None = None,
        body: Mapping[str, Any] | None = None,
        timeout: float = 30.0,
    ) -> JsonResponse:
        if method.upper() == "POST" and path == SELECTOR_PATH:
            if query:
                raise UpstreamContractError("Selector task requests must not use URL query parameters")
            if not self._capacity.acquire(timeout=min(max(0.0, float(timeout)), self.queue_timeout)):
                raise ProviderOverloadedError()
            try:
                return self._selector_task(dict(body or {}), request_timeout=float(timeout))
            finally:
                self._capacity.release()
        return self.delegate.request(
            method,
            path,
            query=query,
            body=body,
            timeout=timeout,
        )

    def _bounded_request_timeout(self, request_timeout: float, deadline: float) -> float:
        remaining = deadline - self._clock()
        if remaining <= 0:
            return 0.0
        return max(0.1, min(max(0.1, request_timeout), 10.0, remaining))

    def _cancel_best_effort(self, task_id: str, request_timeout: float) -> None:
        encoded = urllib.parse.quote(task_id, safe="")
        try:
            self.delegate.request(
                "DELETE",
                f"{SELECTOR_TASKS_PATH}/{encoded}",
                timeout=max(0.1, min(request_timeout, 5.0)),
            )
        except Exception:
            return

    def _selector_task(self, body: Mapping[str, Any], *, request_timeout: float) -> JsonResponse:
        if request_timeout <= 0:
            raise ValueError("selector request timeout must be greater than 0")
        started = self._clock()
        deadline = started + self.task_timeout
        create_timeout = self._bounded_request_timeout(request_timeout, deadline)
        if create_timeout <= 0:
            raise ProviderUnavailableError("AI Workstation selector task timed out before creation")
        created = self.delegate.request(
            "POST",
            SELECTOR_TASKS_PATH,
            body=body,
            timeout=create_timeout,
        )
        _raise_for_task_response(created, stage="create")
        if created.status != 202:
            raise UpstreamContractError(
                "Selector task creation returned an unexpected success status",
                details={"stage": "create", "status": created.status},
            )
        task_id = str(created.payload.get("task_id") or "").strip()
        if not task_id or len(task_id) > MAX_SELECTOR_TASK_ID_LENGTH or not _TASK_ID_PATTERN.fullmatch(task_id):
            raise UpstreamContractError("Selector task creation is missing a valid task identifier")

        encoded = urllib.parse.quote(task_id, safe="")
        while True:
            poll_timeout = self._bounded_request_timeout(request_timeout, deadline)
            if poll_timeout <= 0:
                self._cancel_best_effort(task_id, request_timeout)
                raise ProviderUnavailableError("AI Workstation selector task timed out")
            snapshot = self.delegate.request(
                "GET",
                f"{SELECTOR_TASKS_PATH}/{encoded}",
                timeout=poll_timeout,
            )
            _raise_for_task_response(snapshot, stage="poll")
            if snapshot.status != 200:
                raise UpstreamContractError(
                    "Selector task status returned an unexpected success status",
                    details={"stage": "poll", "status": snapshot.status},
                )
            state = str(snapshot.payload.get("status") or "").strip().lower()
            if state == "completed":
                result = snapshot.payload.get("result")
                if not isinstance(result, Mapping):
                    raise UpstreamContractError("Completed selector task is missing a result object")
                # Use the task collection URL, never the ephemeral task-id URL, as
                # the public source identifier returned by higher provider layers.
                return JsonResponse(
                    status=200,
                    headers=snapshot.headers,
                    payload=dict(result),
                    url=created.url,
                    observed_at=snapshot.observed_at,
                )
            if state in _TERMINAL_FAILURE_STATES:
                raise ProviderUnavailableError("AI Workstation selector task did not complete successfully")
            if state not in _ACTIVE_STATES:
                raise UpstreamContractError(
                    "Selector task returned an unknown status",
                    details={"stage": "poll", "status": state or "missing"},
                )

            remaining = deadline - self._clock()
            if remaining <= 0:
                self._cancel_best_effort(task_id, request_timeout)
                raise ProviderUnavailableError("AI Workstation selector task timed out")
            if self.poll_interval:
                self._sleep(min(self.poll_interval, remaining))
