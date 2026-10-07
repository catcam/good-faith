import random
import time

import httpx

RETRYABLE_STATUS = {429, 500, 502, 503, 504}


class RetryClient:
    """HTTP GET with exponential backoff and jitter."""

    def __init__(self, max_attempts: int = 5, base_delay: float = 0.5, max_delay: float = 30.0,
                 timeout: float = 10.0):
        self.max_attempts = max_attempts
        self.base_delay = base_delay
        self.max_delay = max_delay
        self.client = httpx.Client(timeout=timeout)

    def _delay(self, attempt: int, retry_after: str = None) -> float:
        if retry_after is not None:
            try:
                return min(max(0.0, float(retry_after)), self.max_delay)
            except ValueError:
                pass
        delay = self.base_delay * (2 ** attempt)
        return min(delay, self.max_delay) * random.uniform(0.5, 1.0)

    def get(self, url: str, **kwargs) -> httpx.Response:
        last_exc = None
        for attempt in range(self.max_attempts):
            try:
                resp = self.client.get(url, **kwargs)
            except httpx.TransportError as exc:
                last_exc = exc
                time.sleep(self._delay(attempt))
                continue
            if resp.status_code in RETRYABLE_STATUS:
                time.sleep(self._delay(attempt, resp.headers.get("Retry-After")))
                continue
            return resp
        raise RuntimeError(f"giving up on {url} after {self.max_attempts} attempts") from last_exc

    def get_json(self, url: str, **kwargs):
        resp = self.get(url, **kwargs)
        return resp.json()

    def close(self) -> None:
        self.client.close()

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        self.close()
        return True
