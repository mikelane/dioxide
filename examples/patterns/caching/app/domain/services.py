"""Domain services for the caching example."""

from dioxide import service

from .models import User
from .ports import UserRepositoryPort


@service
class UserService:
    """User management service.

    This service depends on UserRepositoryPort without knowing
    whether caching is involved. In production, it gets
    CachingUserRepository; in tests, it gets FakeUserRepository.
    """

    def __init__(self, repository: UserRepositoryPort) -> None:
        """Initialize with repository dependency."""
        self.repository = repository

    async def get_user(self, user_id: str) -> User | None:
        """Get a user by ID."""
        return await self.repository.get_by_id(user_id)

    async def get_user_by_email(self, email: str) -> User | None:
        """Get a user by email."""
        return await self.repository.get_by_email(email)

    async def create_user(self, user_id: str, name: str, email: str) -> User:
        """Create a new user."""
        user = User(id=user_id, name=name, email=email)
        await self.repository.save(user)
        return user

    async def update_user(self, user_id: str, name: str | None = None, email: str | None = None) -> User | None:
        """Update an existing user."""
        user = await self.repository.get_by_id(user_id)
        if user is None:
            return None

        if name is not None:
            user.name = name
        if email is not None:
            user.email = email

        await self.repository.save(user)
        return user

    async def delete_user(self, user_id: str) -> bool:
        """Delete a user."""
        user = await self.repository.get_by_id(user_id)
        if user is None:
            return False

        await self.repository.delete(user_id)
        return True

    async def list_users(self) -> list[User]:
        """List all users."""
        return await self.repository.list_all()
