"""Adapter implementations for dependency-injector example."""

from app.ports import CacheService, EmailService, UserRepository


class PostgresUserRepository(UserRepository):
    """PostgreSQL implementation of UserRepository."""

    def __init__(self, connection_string: str) -> None:
        self.connection_string = connection_string
        self._users: dict[str, dict] = {}
        self._next_id = 1

    async def get(self, user_id: str) -> dict | None:
        return self._users.get(user_id)

    async def save(self, user: dict) -> dict:
        if "id" not in user:
            user["id"] = str(self._next_id)
            self._next_id += 1
        self._users[user["id"]] = user
        return user

    async def delete(self, user_id: str) -> bool:
        if user_id in self._users:
            del self._users[user_id]
            return True
        return False


class SendGridEmailService(EmailService):
    """SendGrid implementation of EmailService."""

    def __init__(self, api_key: str) -> None:
        self.api_key = api_key

    async def send(self, to: str, subject: str, body: str) -> bool:
        print(f"[SendGrid] Sending email to {to}: {subject}")
        return True


class RedisCacheService(CacheService):
    """Redis implementation of CacheService."""

    def __init__(self, redis_url: str) -> None:
        self.redis_url = redis_url
        self._cache: dict[str, str] = {}

    async def get(self, key: str) -> str | None:
        return self._cache.get(key)

    async def set(self, key: str, value: str, ttl: int = 300) -> None:
        self._cache[key] = value

    async def delete(self, key: str) -> None:
        self._cache.pop(key, None)


class FakeUserRepository(UserRepository):
    """In-memory fake for testing."""

    def __init__(self) -> None:
        self._users: dict[str, dict] = {}
        self._next_id = 1

    async def get(self, user_id: str) -> dict | None:
        return self._users.get(user_id)

    async def save(self, user: dict) -> dict:
        if "id" not in user:
            user["id"] = str(self._next_id)
            self._next_id += 1
        self._users[user["id"]] = user
        return user

    async def delete(self, user_id: str) -> bool:
        if user_id in self._users:
            del self._users[user_id]
            return True
        return False

    def seed(self, *users: dict) -> None:
        """Seed with test data."""
        for user in users:
            self._users[user["id"]] = user


class FakeEmailService(EmailService):
    """In-memory fake for testing."""

    def __init__(self) -> None:
        self.sent_emails: list[dict] = []

    async def send(self, to: str, subject: str, body: str) -> bool:
        self.sent_emails.append({"to": to, "subject": subject, "body": body})
        return True


class FakeCacheService(CacheService):
    """In-memory fake for testing."""

    def __init__(self) -> None:
        self._cache: dict[str, str] = {}

    async def get(self, key: str) -> str | None:
        return self._cache.get(key)

    async def set(self, key: str, value: str, ttl: int = 300) -> None:
        self._cache[key] = value

    async def delete(self, key: str) -> None:
        self._cache.pop(key, None)
