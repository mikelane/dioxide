"""Tests using dioxide's profile-based testing.

Notice the simplification compared to dependency-injector:
- No provider overrides
- No container configuration
- Just resolve and test
"""

from dioxide import Container

from app.ports import CachePort, EmailPort, UserRepositoryPort
from app.services import UserService


class DescribeUserService:
    """Tests for UserService."""

    class DescribeCreateUser:
        """Tests for create_user method."""

        async def it_creates_user_and_sends_welcome_email(
            self, container: Container
        ) -> None:
            service = container.resolve(UserService)
            fake_email = container.resolve(EmailPort)

            user = await service.create_user("Alice", "alice@example.com")

            assert user["name"] == "Alice"
            assert user["email"] == "alice@example.com"
            assert "id" in user

            assert len(fake_email.sent_emails) == 1
            assert fake_email.sent_emails[0]["to"] == "alice@example.com"
            assert "Welcome" in fake_email.sent_emails[0]["subject"]

    class DescribeGetUser:
        """Tests for get_user method."""

        async def it_returns_user_from_repository(self, container: Container) -> None:
            service = container.resolve(UserService)
            fake_repo = container.resolve(UserRepositoryPort)

            fake_repo.seed({"id": "1", "name": "Bob", "email": "bob@example.com"})

            user = await service.get_user("1")

            assert user is not None
            assert user["name"] == "Bob"

        async def it_returns_none_for_nonexistent_user(
            self, container: Container
        ) -> None:
            service = container.resolve(UserService)

            user = await service.get_user("nonexistent")

            assert user is None

        async def it_caches_user_after_first_fetch(self, container: Container) -> None:
            service = container.resolve(UserService)
            fake_repo = container.resolve(UserRepositoryPort)
            fake_cache = container.resolve(CachePort)

            fake_repo.seed({"id": "1", "name": "Carol", "email": "carol@example.com"})

            await service.get_user("1")
            cached_value = await fake_cache.get("user:1")

            assert cached_value is not None
            assert "Carol" in cached_value

    class DescribeDeleteUser:
        """Tests for delete_user method."""

        async def it_deletes_user_and_invalidates_cache(
            self, container: Container
        ) -> None:
            service = container.resolve(UserService)
            fake_repo = container.resolve(UserRepositoryPort)
            fake_cache = container.resolve(CachePort)

            fake_repo.seed({"id": "1", "name": "Dave", "email": "dave@example.com"})
            await fake_cache.set("user:1", '{"id": "1", "name": "Dave"}')

            result = await service.delete_user("1")

            assert result is True
            assert await fake_repo.get("1") is None
            assert await fake_cache.get("user:1") is None

        async def it_returns_false_for_nonexistent_user(
            self, container: Container
        ) -> None:
            service = container.resolve(UserService)

            result = await service.delete_user("nonexistent")

            assert result is False
