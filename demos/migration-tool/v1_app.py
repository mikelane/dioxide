# v1.x — the old rivet_di API
from rivet_di import container, adapter, service
from rivet_di.profiles import ProfileEnum


class CachePort:
    def get(self, key: str) -> str | None: ...
    def set(self, key: str, val: str) -> None: ...


@adapter.register(CachePort, profile=ProfileEnum.PROD)
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
