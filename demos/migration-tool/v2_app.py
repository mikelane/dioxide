# v2.0 — the new dioxide API
from dioxide import adapter, service
from dioxide import Profile


class CachePort:
    def get(self, key: str) -> str | None: ...
    def set(self, key: str, val: str) -> None: ...


@adapter.for_(CachePort, profile=Profile.PRODUCTION)
class RedisCache:
    def get(self, key: str) -> str | None:
        return f"redis:{key}"

    def set(self, key: str, val: str) -> None:
        pass


@service
class UserService:
    def __init__(self, cache: CachePort):
        self.cache = cache

    def lookup(self, uid: str) -> str:
        return self.cache.get(uid) or "unknown"
