from collections import OrderedDict
from typing import Any, Callable, Hashable


class LRUCache:
    """Least-recently-used cache with a fixed maximum size."""

    def __init__(self, maxsize: int = 128):
        if maxsize < 1:
            raise ValueError("maxsize must be at least 1")
        self.maxsize = maxsize
        self.data = OrderedDict()
        self.hits = 0
        self.misses = 0

    def get(self, key: Hashable, default: Any = None) -> Any:
        if key in self.data:
            self.hits += 1
            return self.data[key]
        self.misses += 1
        return default

    def put(self, key: Hashable, value: Any) -> None:
        if key in self.data:
            self.data.move_to_end(key)
        self.data[key] = value
        if len(self.data) > self.maxsize:
            self.data.popitem(last=False)

    def delete(self, key: Hashable) -> bool:
        if key in self.data:
            del self.data[key]
            return True
        return False

    def clear(self) -> None:
        self.data.clear()
        self.hits = 0
        self.misses = 0

    def hit_rate(self) -> float:
        total = self.hits + self.misses
        return self.hits / total

    def __len__(self) -> int:
        return len(self.data)

    def __contains__(self, key: Hashable) -> bool:
        return key in self.data


def cached(maxsize: int = 128) -> Callable:
    """Decorator memoizing a function of positional, hashable arguments."""
    def wrap(fn: Callable) -> Callable:
        cache = LRUCache(maxsize)

        def inner(*args):
            result = cache.get(args)
            if result is None:
                result = fn(*args)
                cache.put(args, result)
            return result

        inner.cache = cache
        return inner
    return wrap
