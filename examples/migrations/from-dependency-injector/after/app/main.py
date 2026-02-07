"""Application entry point using dioxide.

Notice there's no container.py file - dioxide uses decorators and scanning
instead of explicit provider configuration.
"""

import asyncio

from dioxide import Container, Profile

import app.adapters as _adapters  # noqa: F401 — register adapters for autoscan
from app.services import UserService


async def main() -> None:
    """Run the application.

    Configuration comes from environment variables (12-Factor App),
    not from container config dictionaries.
    """
    container = Container(profile=Profile.PRODUCTION)

    service = container.resolve(UserService)

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
