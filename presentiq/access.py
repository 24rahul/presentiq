"""Access checks and bounded use of study-funded provider credentials."""

import os
import secrets
import threading
import time
from collections import deque
from contextlib import contextmanager

DEFAULT_REQUESTS_PER_MINUTE = 120
DEFAULT_MAX_CONCURRENT_ANALYSES = 20


class CapacityError(RuntimeError):
    pass


def access_token_valid(token):
    expected = os.getenv("PRESENTIQ_ACCESS_TOKEN", "")
    return bool(expected and token) and secrets.compare_digest(
        token.encode("utf-8"), expected.encode("utf-8")
    )


class UsageLimits:
    """Limits are per process; multiple workers need a shared deployment limiter."""

    def __init__(
        self,
        requests_per_minute=DEFAULT_REQUESTS_PER_MINUTE,
        concurrent=DEFAULT_MAX_CONCURRENT_ANALYSES,
    ):
        self.requests_per_minute = requests_per_minute
        self.concurrent = concurrent
        self._requests = deque()
        self._active = 0
        self._lock = threading.Lock()

    @contextmanager
    def reserve(self):
        now = time.monotonic()
        with self._lock:
            while self._requests and self._requests[0] <= now - 60:
                self._requests.popleft()
            if self._active >= self.concurrent:
                raise CapacityError("All analysis slots are busy. Please try again shortly.")
            if len(self._requests) >= self.requests_per_minute:
                raise CapacityError(
                    "The study request limit has been reached. Please retry in a minute."
                )
            self._requests.append(now)
            self._active += 1
        try:
            yield
        finally:
            with self._lock:
                self._active -= 1


study_usage = UsageLimits(
    requests_per_minute=max(
        1, int(os.getenv("PRESENTIQ_REQUESTS_PER_MINUTE", str(DEFAULT_REQUESTS_PER_MINUTE)))
    ),
    concurrent=max(
        1, int(os.getenv("PRESENTIQ_MAX_CONCURRENT_ANALYSES", str(DEFAULT_MAX_CONCURRENT_ANALYSES)))
    ),
)
