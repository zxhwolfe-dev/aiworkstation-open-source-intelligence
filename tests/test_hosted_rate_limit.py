from __future__ import annotations

import unittest

from aiworkstation_osi.hosted_rate_limit import HostedRateLimitConfig, HostedRateLimiter


class HostedRateLimitTests(unittest.TestCase):
    def test_ordinary_minute_limit(self) -> None:
        now = [1000.0]
        limiter = HostedRateLimiter(
            HostedRateLimitConfig(per_minute=2, per_hour=5, premium_per_minute=1, max_subjects=100),
            clock=lambda: now[0],
        )
        limiter.check_subject("subject")
        limiter.check_subject("subject")
        with self.assertRaises(ValueError) as context:
            limiter.check_subject("subject")
        self.assertIn("RATE_LIMITED", str(context.exception))
        now[0] += 61
        limiter.check_subject("subject")

    def test_hourly_limit_survives_minute_window_reset(self) -> None:
        now = [2000.0]
        limiter = HostedRateLimiter(
            HostedRateLimitConfig(per_minute=2, per_hour=3, premium_per_minute=1, max_subjects=100),
            clock=lambda: now[0],
        )
        limiter.check_subject("subject")
        now[0] += 61
        limiter.check_subject("subject")
        now[0] += 61
        limiter.check_subject("subject")
        now[0] += 61
        with self.assertRaises(ValueError) as context:
            limiter.check_subject("subject")
        self.assertIn("hourly", str(context.exception))
        now[0] += 3601
        limiter.check_subject("subject")

    def test_premium_limit_is_stricter_and_also_counts_as_ordinary(self) -> None:
        limiter = HostedRateLimiter(
            HostedRateLimitConfig(per_minute=5, per_hour=20, premium_per_minute=1, max_subjects=100),
            clock=lambda: 3000.0,
        )
        limiter.check_subject("subject", premium=True)
        with self.assertRaises(ValueError) as context:
            limiter.check_subject("subject", premium=True)
        self.assertIn("premium AI", str(context.exception))
        # Another ordinary data call is still permitted because only one of the
        # five ordinary minute slots was consumed.
        limiter.check_subject("subject", premium=False)

    def test_subjects_are_isolated(self) -> None:
        limiter = HostedRateLimiter(
            HostedRateLimitConfig(per_minute=1, per_hour=2, premium_per_minute=1, max_subjects=100),
            clock=lambda: 4000.0,
        )
        limiter.check_subject("subject-a")
        limiter.check_subject("subject-b")
        with self.assertRaises(ValueError):
            limiter.check_subject("subject-a")

    def test_state_is_bounded_by_authenticated_subject_capacity(self) -> None:
        # Config enforces >=100 to prevent accidentally tiny production state;
        # use the smallest supported capacity and show that older identities can
        # be evicted without affecting the process.
        limiter = HostedRateLimiter(
            HostedRateLimitConfig(per_minute=10, per_hour=100, premium_per_minute=2, max_subjects=100),
            clock=lambda: 5000.0,
        )
        for index in range(110):
            limiter.check_subject(f"subject-{index}")
        self.assertLessEqual(len(limiter._ordinary), 100)

    def test_empty_subject_fails_closed(self) -> None:
        limiter = HostedRateLimiter(HostedRateLimitConfig())
        with self.assertRaises(ValueError) as context:
            limiter.check_subject("")
        self.assertIn("AUTH_REQUIRED", str(context.exception))


if __name__ == "__main__":
    unittest.main()
