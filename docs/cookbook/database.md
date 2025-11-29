# Database Patterns

Recipes for database integration with SQLAlchemy and dioxide.

---

## Recipe: SQLAlchemy Async Adapter

### Problem

You want to use SQLAlchemy async with proper lifecycle management (connection pool initialization and cleanup).

### Solution

Create a database adapter with `@lifecycle` for connection pool management.

### Code

```python
"""SQLAlchemy async adapter with lifecycle management."""
from typing import Protocol

from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from dioxide import Profile, adapter, lifecycle, service


# Port for database access
class DatabasePort(Protocol):
    """Database connection port."""

    async def get_session(self) -> AsyncSession:
        """Get a database session."""
        ...


# Configuration service (see configuration.md)
@service
class DatabaseConfig:
    def __init__(self):
        import os
        self.url = os.getenv(
            "DATABASE_URL",
            "postgresql+asyncpg://localhost/myapp"
        )
        self.pool_size = int(os.getenv("DB_POOL_SIZE", "5"))
        self.pool_timeout = int(os.getenv("DB_POOL_TIMEOUT", "30"))


@adapter.for_(DatabasePort, profile=Profile.PRODUCTION)
@lifecycle
class SQLAlchemyAdapter:
    """Production database adapter with connection pooling.

    Uses @lifecycle for proper initialization and cleanup:
    - initialize(): Creates connection pool on app startup
    - dispose(): Closes all connections on app shutdown
    """

    def __init__(self, config: DatabaseConfig) -> None:
        self.config = config
        self.engine: AsyncEngine | None = None
        self.session_factory: async_sessionmaker[AsyncSession] | None = None

    async def initialize(self) -> None:
        """Create engine and session factory on startup."""
        self.engine = create_async_engine(
            self.config.url,
            pool_size=self.config.pool_size,
            pool_timeout=self.config.pool_timeout,
            echo=False,  # Set True for SQL logging
        )
        self.session_factory = async_sessionmaker(
            self.engine,
            expire_on_commit=False,
        )
        print(f"Database connected: {self.config.url}")

    async def dispose(self) -> None:
        """Close all connections on shutdown."""
        if self.engine:
            await self.engine.dispose()
            print("Database connections closed")

    async def get_session(self) -> AsyncSession:
        """Get a new database session."""
        if not self.session_factory:
            raise RuntimeError("Database not initialized")
        return self.session_factory()


# Usage with FastAPI
from contextlib import asynccontextmanager
from dioxide import Container, Profile
from fastapi import FastAPI


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Container lifecycle handles database init/cleanup."""
    async with Container(profile=Profile.PRODUCTION) as container:
        # SQLAlchemyAdapter.initialize() called here
        app.state.container = container
        yield
    # SQLAlchemyAdapter.dispose() called here


app = FastAPI(lifespan=lifespan)
```

### Explanation

1. **@lifecycle decorator**: Marks adapter for init/cleanup during container lifecycle
2. **initialize()**: Called when container starts (`async with container`)
3. **dispose()**: Called when container stops (cleanup connections)
4. **Connection pooling**: SQLAlchemy manages pool, dioxide manages lifecycle
5. **Config injection**: Database config injected via constructor

---

## Recipe: Repository Pattern

### Problem

You want a clean data access layer that separates database logic from business logic.

### Solution

Create repository ports and adapters that encapsulate database operations.

### Code

```python
"""Repository pattern with dioxide."""
from dataclasses import dataclass
from typing import Protocol
from datetime import datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from dioxide import Profile, adapter, service


# Domain model
@dataclass
class User:
    id: int | None
    email: str
    name: str
    created_at: datetime | None = None


# Repository port
class UserRepository(Protocol):
    """Port for user data access."""

    async def find_by_id(self, user_id: int) -> User | None:
        """Find user by ID."""
        ...

    async def find_by_email(self, email: str) -> User | None:
        """Find user by email."""
        ...

    async def save(self, user: User) -> User:
        """Save user (insert or update)."""
        ...

    async def delete(self, user_id: int) -> bool:
        """Delete user by ID."""
        ...

    async def list_all(self, limit: int = 100, offset: int = 0) -> list[User]:
        """List all users with pagination."""
        ...


# SQLAlchemy model
from sqlalchemy import Column, Integer, String, DateTime
from sqlalchemy.orm import declarative_base

Base = declarative_base()


class UserModel(Base):
    """SQLAlchemy user table model."""

    __tablename__ = "users"

    id = Column(Integer, primary_key=True)
    email = Column(String(255), unique=True, nullable=False)
    name = Column(String(255), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    def to_domain(self) -> User:
        """Convert to domain model."""
        return User(
            id=self.id,
            email=self.email,
            name=self.name,
            created_at=self.created_at,
        )

    @classmethod
    def from_domain(cls, user: User) -> "UserModel":
        """Create from domain model."""
        return cls(
            id=user.id,
            email=user.email,
            name=user.name,
            created_at=user.created_at,
        )


# Production repository adapter
@adapter.for_(UserRepository, profile=Profile.PRODUCTION)
class SQLAlchemyUserRepository:
    """Production user repository using SQLAlchemy."""

    def __init__(self, db: DatabasePort) -> None:
        self.db = db

    async def find_by_id(self, user_id: int) -> User | None:
        async with await self.db.get_session() as session:
            result = await session.get(UserModel, user_id)
            return result.to_domain() if result else None

    async def find_by_email(self, email: str) -> User | None:
        async with await self.db.get_session() as session:
            stmt = select(UserModel).where(UserModel.email == email)
            result = await session.execute(stmt)
            model = result.scalar_one_or_none()
            return model.to_domain() if model else None

    async def save(self, user: User) -> User:
        async with await self.db.get_session() as session:
            if user.id:
                # Update existing
                model = await session.get(UserModel, user.id)
                if model:
                    model.email = user.email
                    model.name = user.name
            else:
                # Insert new
                model = UserModel.from_domain(user)
                session.add(model)

            await session.commit()
            await session.refresh(model)
            return model.to_domain()

    async def delete(self, user_id: int) -> bool:
        async with await self.db.get_session() as session:
            model = await session.get(UserModel, user_id)
            if model:
                await session.delete(model)
                await session.commit()
                return True
            return False

    async def list_all(self, limit: int = 100, offset: int = 0) -> list[User]:
        async with await self.db.get_session() as session:
            stmt = select(UserModel).limit(limit).offset(offset)
            result = await session.execute(stmt)
            return [m.to_domain() for m in result.scalars()]


# Service using repository
@service
class UserService:
    """Business logic using repository."""

    def __init__(self, users: UserRepository) -> None:
        self.users = users

    async def register(self, email: str, name: str) -> User:
        """Register new user."""
        # Business logic: check if email exists
        existing = await self.users.find_by_email(email)
        if existing:
            raise ValueError(f"Email {email} already registered")

        user = User(id=None, email=email, name=name)
        return await self.users.save(user)
```

### Explanation

1. **Domain model**: Simple dataclass, no ORM dependencies
2. **Repository port**: Defines data access interface
3. **SQLAlchemy adapter**: Implements port with real database
4. **Model conversion**: `to_domain()` / `from_domain()` separate concerns
5. **Service uses port**: Business logic doesn't know about SQLAlchemy

---

## Recipe: In-Memory Repository Fake

### Problem

You need a fast, deterministic fake repository for testing.

### Solution

Create an in-memory implementation of the repository port.

### Code

```python
"""In-memory repository fake for testing."""
from dataclasses import dataclass, field
from datetime import datetime, UTC

from dioxide import Profile, adapter


@dataclass
class User:
    id: int | None
    email: str
    name: str
    created_at: datetime | None = None


@adapter.for_(UserRepository, profile=Profile.TEST)
class FakeUserRepository:
    """In-memory user repository for testing.

    Fast, deterministic, and provides test helpers.
    """

    def __init__(self) -> None:
        self.users: dict[int, User] = {}
        self._next_id = 1

    async def find_by_id(self, user_id: int) -> User | None:
        return self.users.get(user_id)

    async def find_by_email(self, email: str) -> User | None:
        for user in self.users.values():
            if user.email == email:
                return user
        return None

    async def save(self, user: User) -> User:
        if user.id is None:
            user.id = self._next_id
            self._next_id += 1
            user.created_at = datetime.now(UTC)

        self.users[user.id] = user
        return user

    async def delete(self, user_id: int) -> bool:
        if user_id in self.users:
            del self.users[user_id]
            return True
        return False

    async def list_all(self, limit: int = 100, offset: int = 0) -> list[User]:
        all_users = list(self.users.values())
        return all_users[offset : offset + limit]

    # Test helpers
    def seed(self, *users: User) -> None:
        """Seed multiple users for testing."""
        for user in users:
            if user.id is None:
                user.id = self._next_id
                self._next_id += 1
            if user.created_at is None:
                user.created_at = datetime.now(UTC)
            self.users[user.id] = user

    def clear(self) -> None:
        """Clear all data."""
        self.users.clear()
        self._next_id = 1

    def count(self) -> int:
        """Get total user count."""
        return len(self.users)


# Test usage
import pytest


@pytest.fixture
def fake_users(container) -> FakeUserRepository:
    """Typed access to fake repository."""
    repo = container.resolve(UserRepository)
    yield repo
    repo.clear()


class DescribeUserService:
    """Tests for UserService."""

    async def it_registers_new_user(self, container, fake_users):
        """Creates user in repository."""
        service = container.resolve(UserService)

        result = await service.register("alice@example.com", "Alice")

        assert result.id is not None
        assert result.email == "alice@example.com"
        assert fake_users.count() == 1

    async def it_rejects_duplicate_email(self, container, fake_users):
        """Raises error for duplicate email."""
        fake_users.seed(User(id=1, email="alice@example.com", name="Alice"))
        service = container.resolve(UserService)

        with pytest.raises(ValueError) as exc_info:
            await service.register("alice@example.com", "Another Alice")

        assert "already registered" in str(exc_info.value)

    async def it_paginates_user_list(self, container, fake_users):
        """Returns paginated results."""
        # Seed 10 users
        fake_users.seed(*[
            User(id=i, email=f"user{i}@example.com", name=f"User {i}")
            for i in range(1, 11)
        ])
        service = container.resolve(UserService)

        page1 = await service.list_users(limit=5, offset=0)
        page2 = await service.list_users(limit=5, offset=5)

        assert len(page1) == 5
        assert len(page2) == 5
        assert page1[0].id != page2[0].id
```

### Explanation

1. **Simple dict storage**: Fast in-memory operations
2. **Auto-ID generation**: Mimics database behavior
3. **seed() helper**: Convenient test setup
4. **Same interface**: Implements same port as production adapter
5. **No I/O**: Tests run in milliseconds

---

## Recipe: Transaction Management

### Problem

You need to handle database transactions (commit/rollback) correctly.

### Solution

Use context managers for transaction scope.

### Code

```python
"""Transaction management patterns."""
from contextlib import asynccontextmanager
from typing import AsyncIterator

from sqlalchemy.ext.asyncio import AsyncSession
from dioxide import Profile, adapter, service


class DatabasePort(Protocol):
    """Database port with transaction support."""

    async def get_session(self) -> AsyncSession: ...

    @asynccontextmanager
    async def transaction(self) -> AsyncIterator[AsyncSession]:
        """Get session in transaction context."""
        ...


@adapter.for_(DatabasePort, profile=Profile.PRODUCTION)
@lifecycle
class SQLAlchemyAdapter:
    """Database adapter with transaction support."""

    def __init__(self, config: DatabaseConfig) -> None:
        self.config = config
        self.engine = None
        self.session_factory = None

    async def initialize(self) -> None:
        self.engine = create_async_engine(self.config.url)
        self.session_factory = async_sessionmaker(
            self.engine,
            expire_on_commit=False,
        )

    async def dispose(self) -> None:
        if self.engine:
            await self.engine.dispose()

    async def get_session(self) -> AsyncSession:
        return self.session_factory()

    @asynccontextmanager
    async def transaction(self) -> AsyncIterator[AsyncSession]:
        """Provide transactional session with auto-commit/rollback."""
        session = self.session_factory()
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


# Repository using transactions
@adapter.for_(UserRepository, profile=Profile.PRODUCTION)
class SQLAlchemyUserRepository:
    def __init__(self, db: DatabasePort) -> None:
        self.db = db

    async def save(self, user: User) -> User:
        """Save with automatic transaction handling."""
        async with self.db.transaction() as session:
            model = UserModel.from_domain(user)
            session.add(model)
            # Commit happens automatically on exit
            await session.flush()  # Get ID before commit
            return model.to_domain()


# Service with multi-operation transaction
@service
class TransferService:
    """Service demonstrating multi-operation transactions."""

    def __init__(self, db: DatabasePort) -> None:
        self.db = db

    async def transfer_funds(
        self,
        from_account_id: int,
        to_account_id: int,
        amount: float,
    ) -> None:
        """Transfer funds atomically."""
        async with self.db.transaction() as session:
            # Both operations in same transaction
            from_account = await session.get(AccountModel, from_account_id)
            to_account = await session.get(AccountModel, to_account_id)

            if from_account.balance < amount:
                raise ValueError("Insufficient funds")

            from_account.balance -= amount
            to_account.balance += amount

            # Both changes commit together or both rollback


# Fake with transaction support
@adapter.for_(DatabasePort, profile=Profile.TEST)
class FakeDatabaseAdapter:
    """Fake database with transaction simulation."""

    def __init__(self) -> None:
        self.data: dict = {}
        self._in_transaction = False
        self._transaction_data: dict = {}

    @asynccontextmanager
    async def transaction(self) -> AsyncIterator["FakeDatabaseAdapter"]:
        """Simulate transaction with rollback on error."""
        self._in_transaction = True
        self._transaction_data = self.data.copy()
        try:
            yield self
            # Commit: keep changes
            self._in_transaction = False
        except Exception:
            # Rollback: restore original data
            self.data = self._transaction_data
            self._in_transaction = False
            raise
```

### Explanation

1. **Context manager**: Transaction scope is explicit
2. **Auto-commit**: Commit on successful exit
3. **Auto-rollback**: Rollback on exception
4. **Multi-operation**: Multiple changes in one transaction
5. **Fake support**: Test fake can simulate transactions

---

## Recipe: Database Migrations

### Problem

You need to run database migrations on application startup.

### Solution

Add migration step to the lifecycle initialization.

### Code

```python
"""Database migrations in lifecycle."""
from alembic.config import Config as AlembicConfig
from alembic import command
from dioxide import Profile, adapter, lifecycle


@adapter.for_(DatabasePort, profile=Profile.PRODUCTION)
@lifecycle
class SQLAlchemyAdapter:
    """Database adapter with migration support."""

    def __init__(self, config: DatabaseConfig) -> None:
        self.config = config
        self.engine = None
        self.session_factory = None

    async def initialize(self) -> None:
        """Initialize database and run migrations."""
        # Create engine
        self.engine = create_async_engine(self.config.url)
        self.session_factory = async_sessionmaker(self.engine)

        # Run migrations (sync operation)
        if self.config.run_migrations:
            await self._run_migrations()

        print("Database ready")

    async def _run_migrations(self) -> None:
        """Run Alembic migrations."""
        import asyncio

        def run_sync():
            alembic_cfg = AlembicConfig("alembic.ini")
            alembic_cfg.set_main_option("sqlalchemy.url", self.config.url)
            command.upgrade(alembic_cfg, "head")

        # Run sync migration in thread pool
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(None, run_sync)
        print("Migrations complete")

    async def dispose(self) -> None:
        if self.engine:
            await self.engine.dispose()


# Config with migration flag
@service
class DatabaseConfig:
    def __init__(self):
        import os
        self.url = os.getenv("DATABASE_URL", "")
        self.run_migrations = os.getenv("RUN_MIGRATIONS", "false").lower() == "true"


# Usage
# RUN_MIGRATIONS=true python -m uvicorn app:app
```

### Explanation

1. **Lifecycle hook**: Migrations run during `initialize()`
2. **Config flag**: Control whether to run migrations
3. **Sync in executor**: Alembic is sync, run in thread pool
4. **Production control**: Only run migrations when explicitly enabled

---

## Recipe: Read Replicas

### Problem

You want to use read replicas for query scalability.

### Solution

Create separate adapters for read and write operations.

### Code

```python
"""Read replica pattern with dioxide."""
from typing import Protocol

from dioxide import Profile, adapter, lifecycle, service


class WriteDatabase(Protocol):
    """Port for write operations (primary)."""

    async def save(self, data: dict) -> dict: ...
    async def delete(self, id: int) -> bool: ...


class ReadDatabase(Protocol):
    """Port for read operations (replica)."""

    async def find_by_id(self, id: int) -> dict | None: ...
    async def list_all(self, limit: int = 100) -> list[dict]: ...


@adapter.for_(WriteDatabase, profile=Profile.PRODUCTION)
@lifecycle
class PrimaryDatabaseAdapter:
    """Write operations go to primary."""

    def __init__(self, config: DatabaseConfig) -> None:
        self.url = config.primary_url

    async def initialize(self) -> None:
        self.engine = create_async_engine(self.url)
        self.session_factory = async_sessionmaker(self.engine)

    async def dispose(self) -> None:
        await self.engine.dispose()

    async def save(self, data: dict) -> dict:
        async with self.session_factory() as session:
            # Write to primary
            ...

    async def delete(self, id: int) -> bool:
        async with self.session_factory() as session:
            # Delete from primary
            ...


@adapter.for_(ReadDatabase, profile=Profile.PRODUCTION)
@lifecycle
class ReplicaDatabaseAdapter:
    """Read operations go to replica."""

    def __init__(self, config: DatabaseConfig) -> None:
        self.url = config.replica_url

    async def initialize(self) -> None:
        self.engine = create_async_engine(self.url)
        self.session_factory = async_sessionmaker(self.engine)

    async def dispose(self) -> None:
        await self.engine.dispose()

    async def find_by_id(self, id: int) -> dict | None:
        async with self.session_factory() as session:
            # Read from replica
            ...

    async def list_all(self, limit: int = 100) -> list[dict]:
        async with self.session_factory() as session:
            # Read from replica
            ...


# Service uses both
@service
class UserService:
    """Service with read/write separation."""

    def __init__(
        self,
        writer: WriteDatabase,
        reader: ReadDatabase,
    ) -> None:
        self.writer = writer
        self.reader = reader

    async def create_user(self, data: dict) -> dict:
        """Write to primary."""
        return await self.writer.save(data)

    async def get_user(self, user_id: int) -> dict | None:
        """Read from replica."""
        return await self.reader.find_by_id(user_id)

    async def list_users(self) -> list[dict]:
        """Read from replica."""
        return await self.reader.list_all()


# Config
@service
class DatabaseConfig:
    def __init__(self):
        import os
        self.primary_url = os.getenv("DATABASE_PRIMARY_URL", "")
        self.replica_url = os.getenv("DATABASE_REPLICA_URL", "")
```

### Explanation

1. **Separate ports**: Distinct interfaces for read vs write
2. **Separate adapters**: Connect to different database instances
3. **Service decides**: Business logic chooses read or write path
4. **Test simplification**: Fake can implement both ports in one class

---

## See Also

- [Configuration](configuration.md) - Database connection config
- [Testing Patterns](testing.md) - Repository testing with fakes
- [FastAPI Integration](fastapi.md) - Database with FastAPI lifecycle
