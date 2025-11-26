"""PostgreSQL adapter for production database operations.

This adapter demonstrates CONSTRUCTOR DEPENDENCY INJECTION - it depends on
ConfigPort to get its database URL instead of reading os.environ directly.

Why inject ConfigPort instead of using os.environ?
    1. Testability: Tests can provide fake config without env var manipulation
    2. Consistency: All configuration comes through the same interface
    3. Flexibility: Different profiles can have different config sources
    4. Explicitness: Dependencies are visible in the constructor signature
"""

from typing import Any

from dioxide import Profile, adapter, lifecycle

from ..domain.ports import ConfigPort, DatabasePort


@adapter.for_(DatabasePort, profile=Profile.PRODUCTION)
@lifecycle
class PostgresAdapter:
    """Production PostgreSQL adapter with connection pooling.

    This adapter demonstrates constructor dependency injection:

        def __init__(self, config: ConfigPort) -> None:
            self.database_url = config.get("DATABASE_URL")

    When dioxide resolves PostgresAdapter, it:
    1. Sees the constructor needs ConfigPort
    2. Resolves ConfigPort -> gets EnvConfigAdapter (production profile)
    3. Creates EnvConfigAdapter instance
    4. Passes it to PostgresAdapter.__init__

    This way, PostgresAdapter doesn't need to know WHERE config comes from -
    it just depends on the ConfigPort interface.
    """

    def __init__(self, config: ConfigPort) -> None:
        """Initialize adapter with injected configuration.

        Args:
            config: Configuration port - automatically injected by dioxide!

        Note: The config parameter is type-hinted with ConfigPort, so dioxide
        knows to inject it. The actual adapter instance (EnvConfigAdapter)
        is determined by the active profile.
        """
        # Get database URL from injected config (NOT os.environ directly)
        self.database_url = config.get(
            "DATABASE_URL", "postgresql://localhost/dioxide_example"
        )
        self.pool: Any | None = None
        self._users_table: dict[str, dict] = {}  # Mock storage for demo

    async def initialize(self) -> None:
        """Initialize database connection pool.

        Called automatically by dioxide container during startup.
        In production, this would create an asyncpg pool:

            import asyncpg
            self.pool = await asyncpg.create_pool(
                self.database_url,  # <-- Uses config from constructor
                min_size=5,
                max_size=20
            )
        """
        print(f"[PostgresAdapter] Connecting to {self.database_url}")

        # Mock pool creation - replace with real asyncpg in production
        self.pool = f"Connection pool to {self.database_url}"
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
