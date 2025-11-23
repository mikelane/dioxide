"""PostgreSQL adapter for production database operations.

This adapter implements DatabasePort using asyncpg for real PostgreSQL
connections. It uses the @lifecycle decorator for connection pool management.
"""

import os
from typing import Any

from dioxide import adapter, lifecycle, Profile

from ..domain.ports import DatabasePort


@adapter.for_(DatabasePort, profile=Profile.PRODUCTION)
@lifecycle
class PostgresAdapter:
    """Production PostgreSQL adapter with connection pooling.

    This adapter manages a connection pool that is initialized when the
    container starts and cleaned up when it stops. In a real application,
    you would use asyncpg or SQLAlchemy async.

    Example configuration via environment variables:
        DATABASE_URL=postgresql://user:pass@localhost/dbname
    """

    def __init__(self) -> None:
        """Initialize adapter (connection pool created in initialize())."""
        self.pool: Any | None = None
        self._users_table: dict[str, dict] = {}  # Mock storage for demo

    async def initialize(self) -> None:
        """Initialize database connection pool.

        Called automatically by dioxide container during startup.
        In production, this would create an asyncpg pool:

            import asyncpg
            self.pool = await asyncpg.create_pool(
                os.getenv("DATABASE_URL"),
                min_size=5,
                max_size=20
            )
        """
        database_url = os.getenv("DATABASE_URL", "postgresql://localhost/dioxide_example")
        print(f"[PostgresAdapter] Connecting to {database_url}")

        # Mock pool creation - replace with real asyncpg in production
        self.pool = f"Connection pool to {database_url}"
        print("[PostgresAdapter] Connection pool created")

    async def dispose(self) -> None:
        """Close database connection pool.

        Called automatically by dioxide container during shutdown.
        In production, this would close the asyncpg pool:

            if self.pool:
                await self.pool.close()
        """
        if self.pool:
            print("[PostgresAdapter] Closing connection pool")
            self.pool = None
            print("[PostgresAdapter] Connection pool closed")

    async def get_user(self, user_id: str) -> dict | None:
        """Retrieve a user by ID from PostgreSQL.

        In production, this would execute:
            async with self.pool.acquire() as conn:
                row = await conn.fetchrow(
                    "SELECT * FROM users WHERE id = $1", user_id
                )
                return dict(row) if row else None

        Args:
            user_id: Unique identifier for the user

        Returns:
            User dictionary if found, None otherwise
        """
        # Mock implementation - replace with real SQL query
        return self._users_table.get(user_id)

    async def create_user(self, name: str, email: str) -> dict:
        """Create a new user in PostgreSQL.

        In production, this would execute:
            async with self.pool.acquire() as conn:
                row = await conn.fetchrow(
                    "INSERT INTO users (name, email) VALUES ($1, $2) RETURNING *",
                    name, email
                )
                return dict(row)

        Args:
            name: User's full name
            email: User's email address

        Returns:
            Created user dictionary with ID
        """
        # Mock implementation - replace with real SQL insert
        user_id = str(len(self._users_table) + 1)
        user = {"id": user_id, "name": name, "email": email}
        self._users_table[user_id] = user
        return user

    async def list_users(self) -> list[dict]:
        """List all users from PostgreSQL.

        In production, this would execute:
            async with self.pool.acquire() as conn:
                rows = await conn.fetch("SELECT * FROM users ORDER BY id")
                return [dict(row) for row in rows]

        Returns:
            List of user dictionaries
        """
        # Mock implementation - replace with real SQL query
        return list(self._users_table.values())
