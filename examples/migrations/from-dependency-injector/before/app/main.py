"""Application entry point using dependency-injector."""

import asyncio

from app.container import Container


async def main() -> None:
    """Run the application."""
    container = Container()
    container.config.from_dict(
        {
            "database": {"url": "postgresql://localhost/mydb"},
            "email": {"api_key": "sg_test_key"},
            "cache": {"redis_url": "redis://localhost:6379"},
        }
    )

    service = container.user_service()

    print("Creating user...")
    user = await service.create_user("Alice", "alice@example.com")
    print(f"Created user: {user}")

    print("\nFetching user (should hit database)...")
    fetched = await service.get_user(user["id"])
    print(f"Fetched user: {fetched}")

    print("\nFetching user again (should hit cache)...")
    cached = await service.get_user(user["id"])
    print(f"Cached user: {cached}")

    print("\nDeleting user...")
    deleted = await service.delete_user(user["id"])
    print(f"Deleted: {deleted}")


if __name__ == "__main__":
    asyncio.run(main())
