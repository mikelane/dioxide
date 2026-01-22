"""Adapter implementations using dioxide decorators.

The @adapter.for_() decorator replaces dependency-injector's providers.Singleton/Factory.
Profile-based registration replaces manual container overrides.
"""

import os

from dioxide import Profile, adapter

from app.ports import CachePort, EmailPort, UserRepositoryPort


@adapter.for_(UserRepositoryPort, profile=Profile.PRODUCTION)
class PostgresUserRepository:
    """PostgreSQL implementation of UserRepositoryPort.

    Configuration comes from environment variables, not container config.
    This follows 12-Factor App principles.
    """

    def __init__(self) -> None:
        self.connection_string = os.environ.get(
            "DATABASE_URL", "postgresql://localhost/mydb"
        )
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


@adapter.for_(EmailPort, profile=Profile.PRODUCTION)
class SendGridEmailAdapter:
    """SendGrid implementation of EmailPort."""

    def __init__(self) -> None:
        self.api_key = os.environ.get("SENDGRID_API_KEY", "")

    async def send(self, to: str, subject: str, body: str) -> bool:
        print(f"[SendGrid] Sending email to {to}: {subject}")
        return True


@adapter.for_(CachePort, profile=Profile.PRODUCTION)
class RedisCacheAdapter:
    """Redis implementation of CachePort."""

    def __init__(self) -> None:
        self.redis_url = os.environ.get("REDIS_URL", "redis://localhost:6379")
        self._cache: dict[str, str] = {}

    async def get(self, key: str) -> str | None:
        return self._cache.get(key)

    async def set(self, key: str, value: str, ttl: int = 300) -> None:
        self._cache[key] = value

    async def delete(self, key: str) -> None:
        self._cache.pop(key, None)


@adapter.for_(UserRepositoryPort, profile=Profile.TEST)
class FakeUserRepository:
    """In-memory fake for testing.

    With dioxide, test fakes are just adapters with Profile.TEST.
    No container overrides needed.
    """

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

    def clear(self) -> None:
        """Clear all users."""
        self._users.clear()
        self._next_id = 1


@adapter.for_(EmailPort, profile=Profile.TEST)
class FakeEmailAdapter:
    """In-memory fake for testing."""

    def __init__(self) -> None:
        self.sent_emails: list[dict] = []

    async def send(self, to: str, subject: str, body: str) -> bool:
        self.sent_emails.append({"to": to, "subject": subject, "body": body})
        return True

    def clear(self) -> None:
        """Clear sent emails."""
        self.sent_emails.clear()


@adapter.for_(CachePort, profile=Profile.TEST)
class FakeCacheAdapter:
    """In-memory fake for testing."""

    def __init__(self) -> None:
        self._cache: dict[str, str] = {}

    async def get(self, key: str) -> str | None:
        return self._cache.get(key)

    async def set(self, key: str, value: str, ttl: int = 300) -> None:
        self._cache[key] = value

    async def delete(self, key: str) -> None:
        self._cache.pop(key, None)

    def clear(self) -> None:
        """Clear all cache entries."""
        self._cache.clear()
