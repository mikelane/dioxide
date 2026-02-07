"""Verify the migrated v2 API works correctly."""
from v2_app import CachePort, UserService


class FakeCache:
    def __init__(self):
        self.store: dict[str, str] = {}

    def get(self, key: str) -> str | None:
        return self.store.get(key)

    def set(self, key: str, val: str) -> None:
        self.store[key] = val


def test_lookup_returns_cached_user():
    cache = FakeCache()
    cache.set("u1", "Alice")
    svc = UserService(cache)
    assert svc.lookup("u1") == "Alice"


def test_lookup_returns_unknown_on_miss():
    cache = FakeCache()
    svc = UserService(cache)
    assert svc.lookup("missing") == "unknown"
