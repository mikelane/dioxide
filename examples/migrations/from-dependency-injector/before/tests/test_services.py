"""Tests using dependency-injector's override pattern.

With dependency-injector, testing requires:
1. Creating the production container
2. Overriding providers with fakes
3. Getting the service from the container
"""

import pytest
from dependency_injector import providers

from app.adapters import FakeCacheService, FakeEmailService, FakeUserRepository
from app.container import Container


@pytest.fixture
def container() -> Container:
    """Create container with fake implementations."""
    container = Container()

    container.user_repository.override(providers.Singleton(FakeUserRepository))
    container.email_service.override(providers.Singleton(FakeEmailService))
    container.cache_service.override(providers.Singleton(FakeCacheService))

    return container


class DescribeUserService:
    """Tests for UserService."""

    class DescribeCreateUser:
        """Tests for create_user method."""

        async def it_creates_user_and_sends_welcome_email(
            self, container: Container
        ) -> None:
            service = container.user_service()
            fake_email = container.email_service()

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
            service = container.user_service()
            fake_repo = container.user_repository()

            fake_repo.seed({"id": "1", "name": "Bob", "email": "bob@example.com"})

            user = await service.get_user("1")

            assert user is not None
            assert user["name"] == "Bob"

        async def it_returns_none_for_nonexistent_user(
            self, container: Container
        ) -> None:
            service = container.user_service()

            user = await service.get_user("nonexistent")

            assert user is None

        async def it_caches_user_after_first_fetch(self, container: Container) -> None:
            service = container.user_service()
            fake_repo = container.user_repository()
            fake_cache = container.cache_service()

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
            service = container.user_service()
            fake_repo = container.user_repository()
            fake_cache = container.cache_service()

            fake_repo.seed({"id": "1", "name": "Dave", "email": "dave@example.com"})
            await fake_cache.set("user:1", '{"id": "1", "name": "Dave"}')

            result = await service.delete_user("1")

            assert result is True
            assert await fake_repo.get("1") is None
            assert await fake_cache.get("user:1") is None

        async def it_returns_false_for_nonexistent_user(
            self, container: Container
        ) -> None:
            service = container.user_service()

            result = await service.delete_user("nonexistent")

            assert result is False
