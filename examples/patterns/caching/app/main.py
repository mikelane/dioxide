"""Entry point demonstrating the caching adapter pattern.

This example shows how CachingUserRepository wraps PostgresUserRepository
with transparent caching using Redis.
"""

import asyncio

from dioxide import Container, Profile

from . import adapters as _adapters  # noqa: F401 — register adapters for autoscan
from .domain import UserService


async def main() -> None:
    """Demonstrate caching adapter pattern."""
    print("=" * 70)
    print("Caching Adapter Pattern Example")
    print("=" * 70)
    print()
    print("Architecture:")
    print("  UserService")
    print("    -> UserRepositoryPort")
    print("       -> CachingUserRepository")
    print("          -> DatabaseUserRepositoryPort (PostgresUserRepository)")
    print("          -> CachePort (RedisCache)")
    print()

    container = Container(profile=Profile.PRODUCTION)

    service = container.resolve(UserService)

    print()
    print("-" * 70)
    print("First read: Cache MISS, fetches from database")
    print("-" * 70)
    print()

    user = await service.get_user("user-1")
    if user:
        print(f"  Result: {user.name} ({user.email})")

    print()
    print("-" * 70)
    print("Second read: Cache HIT, no database query")
    print("-" * 70)
    print()

    user = await service.get_user("user-1")
    if user:
        print(f"  Result: {user.name} ({user.email})")

    print()
    print("-" * 70)
    print("Read by email: Cache MISS, then cached")
    print("-" * 70)
    print()

    user = await service.get_user_by_email("bob@example.com")
    if user:
        print(f"  Result: {user.name} ({user.email})")

    print()
    print("-" * 70)
    print("Read by email again: Cache HIT")
    print("-" * 70)
    print()

    user = await service.get_user_by_email("bob@example.com")
    if user:
        print(f"  Result: {user.name} ({user.email})")

    print()
    print("-" * 70)
    print("Update user: Invalidates cache")
    print("-" * 70)
    print()

    user = await service.update_user("user-1", name="Alice Updated")
    if user:
        print(f"  Updated: {user.name}")

    print()
    print("-" * 70)
    print("Read updated user: Cache MISS (was invalidated)")
    print("-" * 70)
    print()

    user = await service.get_user("user-1")
    if user:
        print(f"  Result: {user.name}")

    print()
    print("=" * 70)
    print("Key Takeaways:")
    print("1. Caching is transparent to UserService")
    print("2. Cache hits avoid database queries")
    print("3. Writes invalidate cache entries")
    print("4. Profile.TEST would use FakeUserRepository (no caching)")
    print("=" * 70)


if __name__ == "__main__":
    asyncio.run(main())
