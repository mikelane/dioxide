"""PostgreSQL adapter for direct database access."""

from datetime import datetime

from dioxide import Profile, adapter

from ..domain.models import User
from ..domain.ports import DatabaseUserRepositoryPort


@adapter.for_(DatabaseUserRepositoryPort, profile=Profile.PRODUCTION)
class PostgresUserRepository:
    """PostgreSQL user repository (simulated).

    In a real application, this would use asyncpg or SQLAlchemy.
    This is the "inner" repository that CachingUserRepository wraps.
    """

    def __init__(self) -> None:
        """Initialize with sample data."""
        self._users: dict[str, User] = {
            "user-1": User(id="user-1", name="Alice", email="alice@example.com", created_at=datetime.now()),
            "user-2": User(id="user-2", name="Bob", email="bob@example.com", created_at=datetime.now()),
        }
        self._email_index: dict[str, str] = {
            "alice@example.com": "user-1",
            "bob@example.com": "user-2",
        }
        print("  [Postgres] Repository initialized with sample data")

    async def get_by_id(self, user_id: str) -> User | None:
        """Get user from PostgreSQL (simulated)."""
        print(f"  [Postgres] Querying user by ID: {user_id}")
        return self._users.get(user_id)

    async def get_by_email(self, email: str) -> User | None:
        """Get user by email from PostgreSQL (simulated)."""
        print(f"  [Postgres] Querying user by email: {email}")
        user_id = self._email_index.get(email)
        if user_id:
            return self._users.get(user_id)
        return None

    async def save(self, user: User) -> None:
        """Save user to PostgreSQL (simulated)."""
        print(f"  [Postgres] Saving user: {user.id}")
        if user.created_at is None:
            user.created_at = datetime.now()
        self._users[user.id] = user
        self._email_index[user.email] = user.id

    async def delete(self, user_id: str) -> None:
        """Delete user from PostgreSQL (simulated)."""
        print(f"  [Postgres] Deleting user: {user_id}")
        user = self._users.get(user_id)
        if user:
            del self._users[user_id]
            if user.email in self._email_index:
                del self._email_index[user.email]

    async def list_all(self) -> list[User]:
        """List all users from PostgreSQL (simulated)."""
        print(f"  [Postgres] Listing all users (count: {len(self._users)})")
        return list(self._users.values())
