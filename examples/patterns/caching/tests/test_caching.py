"""Tests for caching adapter pattern.

These tests use Profile.TEST which provides FakeUserRepository
(simple, no caching). This demonstrates that:
1. Tests don't need caching complexity
2. Profile switching changes implementation
3. Service works the same regardless of caching
"""

from dioxide import Container

from app.domain import User, UserService
from app.domain.ports import CachePort, UserRepositoryPort


class DescribeUserService:
    """Tests for UserService with fake repository."""

    async def it_creates_and_retrieves_user(
        self,
        container: Container,
        seeded_repository: UserRepositoryPort,
    ) -> None:
        """UserService CRUD operations work with fakes."""
        service = container.resolve(UserService)

        user = await service.create_user("user-3", "Charlie", "charlie@example.com")

        assert user.id == "user-3"
        assert user.name == "Charlie"

        retrieved = await service.get_user("user-3")
        assert retrieved is not None
        assert retrieved.name == "Charlie"

    async def it_retrieves_user_by_email(
        self,
        container: Container,
        seeded_repository: UserRepositoryPort,
    ) -> None:
        """UserService can lookup by email."""
        service = container.resolve(UserService)

        user = await service.get_user_by_email("alice@example.com")

        assert user is not None
        assert user.name == "Alice"

    async def it_updates_user(
        self,
        container: Container,
        seeded_repository: UserRepositoryPort,
    ) -> None:
        """UserService can update users."""
        service = container.resolve(UserService)

        user = await service.update_user("user-1", name="Alice Updated")

        assert user is not None
        assert user.name == "Alice Updated"

        retrieved = await service.get_user("user-1")
        assert retrieved.name == "Alice Updated"

    async def it_deletes_user(
        self,
        container: Container,
        seeded_repository: UserRepositoryPort,
    ) -> None:
        """UserService can delete users."""
        service = container.resolve(UserService)

        deleted = await service.delete_user("user-1")

        assert deleted is True

        retrieved = await service.get_user("user-1")
        assert retrieved is None

    async def it_lists_all_users(
        self,
        container: Container,
        seeded_repository: UserRepositoryPort,
    ) -> None:
        """UserService can list all users."""
        service = container.resolve(UserService)

        users = await service.list_users()

        assert len(users) == 2
        names = {u.name for u in users}
        assert names == {"Alice", "Bob"}


class DescribeFakeRepository:
    """Tests demonstrating fake repository behavior."""

    async def it_uses_fake_repository_in_test_profile(
        self,
        container: Container,
    ) -> None:
        """TEST profile uses FakeUserRepository."""
        repository = container.resolve(UserRepositoryPort)

        assert hasattr(repository, "users")
        assert hasattr(repository, "seed")

    async def it_provides_test_helpers(
        self,
        container: Container,
    ) -> None:
        """FakeUserRepository has convenient test helpers."""
        repository = container.resolve(UserRepositoryPort)

        repository.seed(
            User(id="test-1", name="Test User", email="test@example.com"),
        )

        user = await repository.get_by_id("test-1")
        assert user is not None
        assert user.name == "Test User"

        repository.clear()
        user = await repository.get_by_id("test-1")
        assert user is None


class DescribeFakeCache:
    """Tests demonstrating fake cache behavior."""

    async def it_tracks_cache_operations(
        self,
        container: Container,
        cache: CachePort,
    ) -> None:
        """FakeCache tracks operations for testing."""
        await cache.set("key1", "value1")
        await cache.get("key1")
        await cache.get("key2")

        assert cache.set_count == 1
        assert cache.hit_count == 1
        assert cache.miss_count == 1

    async def it_supports_pattern_deletion(
        self,
        container: Container,
        cache: CachePort,
    ) -> None:
        """FakeCache supports pattern-based deletion."""
        await cache.set("user:1", {"id": "1"})
        await cache.set("user:2", {"id": "2"})
        await cache.set("product:1", {"id": "1"})

        await cache.delete_pattern("user:*")

        assert not cache.was_cached("user:1")
        assert not cache.was_cached("user:2")
        assert cache.was_cached("product:1")


class DescribeTestIsolation:
    """Tests demonstrating test isolation."""

    async def it_starts_with_empty_repository(
        self,
        container: Container,
    ) -> None:
        """Each test gets a fresh container."""
        repository = container.resolve(UserRepositoryPort)

        users = await repository.list_all()
        assert len(users) == 0

    async def it_also_starts_with_empty_cache(
        self,
        container: Container,
        cache: CachePort,
    ) -> None:
        """Each test gets a fresh cache."""
        assert cache.hit_count == 0
        assert cache.miss_count == 0
        assert len(cache.data) == 0
