import threading
import time


class TokenBucket:
    """Allow up to `rate` requests per second, with bursts up to `capacity`."""

    def __init__(self, rate: float, capacity: int):
        if rate <= 0 or capacity <= 0:
            raise ValueError("rate and capacity must be positive")
        self.rate = rate
        self.capacity = capacity
        self.tokens = capacity
        self.updated = time.monotonic()
        self.lock = threading.Lock()

    def _refill(self) -> None:
        now = time.monotonic()
        elapsed = now - self.updated
        self.tokens = self.tokens + elapsed * self.rate
        self.updated = now

    def try_acquire(self, n: int = 1) -> bool:
        with self.lock:
            self._refill()
            if self.tokens >= n:
                self.tokens -= n
                return True
            return False

    def wait_time(self, n: int = 1) -> float:
        with self.lock:
            self._refill()
            missing = n - self.tokens
            return max(0.0, missing / self.rate)


class KeyedLimiter:
    """One bucket per client key."""

    def __init__(self, rate: float, capacity: int):
        self.rate = rate
        self.capacity = capacity
        self.buckets = {}

    def allow(self, key: str) -> bool:
        if key not in self.buckets:
            self.buckets[key] = TokenBucket(self.rate, self.capacity)
        return self.buckets[key].try_acquire()

    def forget_idle(self, max_idle: float) -> int:
        now = time.monotonic()
        idle = [k for k, b in self.buckets.items() if now - b.updated > max_idle]
        for k in idle:
            del self.buckets[k]
        return len(idle)
