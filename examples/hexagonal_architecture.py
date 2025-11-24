"""Complete hexagonal architecture example using dioxide.

This example demonstrates:
- Defining ports (interfaces) as Protocols
- Creating adapters for different environments
- Writing core business logic as services
- Profile-based dependency injection
- Testing with fakes instead of mocks
"""

import asyncio
from typing import Protocol

from dioxide import Container, Profile, adapter, service

# ============================================================================
# PORTS (Interfaces) - Define what operations we need
# ============================================================================


class EmailPort(Protocol):
    """Port for sending emails.

    This is the seam - the boundary between core logic and infrastructure.
    """

    async def send(self, to: str, subject: str, body: str) -> None:
        """Send an email."""
        ...


class DatabasePort(Protocol):
    """Port for database operations."""

    async def save_user(self, name: str, email: str) -> int:
        """Save a user and return their ID."""
        ...

    async def get_user(self, user_id: int) -> dict[str, str] | None:
        """Get a user by ID."""
        ...


# ============================================================================
# ADAPTERS (Implementations) - Connect to real infrastructure
# ============================================================================


@adapter.for_(EmailPort, profile=Profile.PRODUCTION)
class SendGridAdapter:
    """Production email adapter using SendGrid API."""

    async def send(self, to: str, subject: str, body: str) -> None:
        """Send email via SendGrid."""
        # In real code, this would call SendGrid API
        print(f'📧 [SendGrid] Sending to {to}: {subject}')
        # await sendgrid_client.send(...)


@adapter.for_(EmailPort, profile=Profile.TEST)
class FakeEmailAdapter:
    """Test email adapter that records sent emails."""

    def __init__(self) -> None:
        self.sent_emails: list[dict[str, str]] = []

    async def send(self, to: str, subject: str, body: str) -> None:
        """Record email instead of sending."""
        email = {'to': to, 'subject': subject, 'body': body}
        self.sent_emails.append(email)
        print(f'✅ [Fake] Recorded email to {to}: {subject}')


@adapter.for_(EmailPort, profile=Profile.DEVELOPMENT)
class ConsoleEmailAdapter:
    """Development email adapter that logs to console."""

    async def send(self, to: str, subject: str, body: str) -> None:
        """Print email to console."""
        print(f'📝 [Console] Email to {to}')
        print(f'   Subject: {subject}')
        print(f'   Body: {body}')


@adapter.for_(DatabasePort, profile=[Profile.PRODUCTION, Profile.DEVELOPMENT])
class PostgresAdapter:
    """Production and development database adapter using PostgreSQL."""

    def __init__(self) -> None:
        self.next_id = 1

    async def save_user(self, name: str, email: str) -> int:
        """Save user to PostgreSQL."""
        # In real code, this would use asyncpg or similar
        user_id = self.next_id
        self.next_id += 1
        print(f'💾 [Postgres] Saved user {user_id}: {name} ({email})')
        # await conn.execute("INSERT INTO users ...")
        return user_id

    async def get_user(self, user_id: int) -> dict[str, str] | None:
        """Get user from PostgreSQL."""
        # In real code, this would query the database
        print(f'🔍 [Postgres] Looking up user {user_id}')
        return {'id': str(user_id), 'name': 'John Doe', 'email': 'john@example.com'}


@adapter.for_(DatabasePort, profile=Profile.TEST)
class InMemoryDatabaseAdapter:
    """Test database adapter using in-memory storage."""

    def __init__(self) -> None:
        self.users: dict[int, dict[str, str]] = {}
        self.next_id = 1

    async def save_user(self, name: str, email: str) -> int:
        """Save user to in-memory storage."""
        user_id = self.next_id
        self.next_id += 1
        self.users[user_id] = {'name': name, 'email': email}
        print(f'💾 [InMemory] Saved user {user_id}: {name}')
        return user_id

    async def get_user(self, user_id: int) -> dict[str, str] | None:
        """Get user from in-memory storage."""
        print(f'🔍 [InMemory] Looking up user {user_id}')
        return self.users.get(user_id)


# ============================================================================
# SERVICES (Core Business Logic) - Depends on ports, not adapters
# ============================================================================


@service
class UserRegistrationService:
    """Core business logic for user registration.

    This service has ZERO knowledge of SendGrid, PostgreSQL, or any
    infrastructure. It only knows about the EmailPort and DatabasePort
    interfaces (ports).
    """

    def __init__(self, email: EmailPort, db: DatabasePort) -> None:
        """Initialize with port dependencies."""
        self.email = email
        self.db = db

    async def register_user(self, name: str, email: str) -> int:
        """Register a new user.

        Core business logic:
        1. Save user to database
        2. Send welcome email
        3. Return user ID
        """
        # Save to database (via DatabasePort)
        user_id = await self.db.save_user(name, email)

        # Send welcome email (via EmailPort)
        await self.email.send(to=email, subject='Welcome!', body=f'Hello {name}, welcome to our platform!')

        return user_id


@service
class UserLookupService:
    """Core business logic for looking up users."""

    def __init__(self, db: DatabasePort) -> None:
        """Initialize with database port."""
        self.db = db

    async def get_user_info(self, user_id: int) -> dict[str, str] | None:
        """Look up user information."""
        return await self.db.get_user(user_id)


# ============================================================================
# USAGE EXAMPLES
# ============================================================================


async def production_example() -> None:
    """Example: Production usage with real infrastructure."""
    print('\n' + '=' * 70)
    print('PRODUCTION EXAMPLE - Real SendGrid + PostgreSQL')
    print('=' * 70 + '\n')

    # Create production container
    container = Container()
    container.scan(profile=Profile.PRODUCTION)

    # Resolve service (gets SendGrid + Postgres adapters automatically)
    registration_service = container.resolve(UserRegistrationService)

    # Use the service - infrastructure details are hidden
    user_id = await registration_service.register_user('Alice Smith', 'alice@example.com')

    print(f'\n✅ User registered with ID: {user_id}')


async def test_example() -> None:
    """Example: Testing with fast fakes (no mocks!)."""
    print('\n' + '=' * 70)
    print('TEST EXAMPLE - Fake Email + In-Memory Database')
    print('=' * 70 + '\n')

    # Create test container
    test_container = Container()
    test_container.scan(profile=Profile.TEST)

    # Resolve service (gets fake adapters automatically)
    registration_service = test_container.resolve(UserRegistrationService)

    # Use the service
    user_id = await registration_service.register_user('Bob Jones', 'bob@test.com')

    # Verify behavior using the fake adapters (no mocks!)
    fake_email = test_container.resolve(EmailPort)
    fake_db = test_container.resolve(DatabasePort)

    assert len(fake_email.sent_emails) == 1
    assert fake_email.sent_emails[0]['to'] == 'bob@test.com'
    assert fake_email.sent_emails[0]['subject'] == 'Welcome!'

    saved_user = await fake_db.get_user(user_id)
    assert saved_user is not None
    assert saved_user['name'] == 'Bob Jones'
    assert saved_user['email'] == 'bob@test.com'

    print(f'\n✅ All assertions passed! User ID: {user_id}')


async def development_example() -> None:
    """Example: Development usage with console logging."""
    print('\n' + '=' * 70)
    print('DEVELOPMENT EXAMPLE - Console Email + Postgres')
    print('=' * 70 + '\n')

    # Create development container
    dev_container = Container()
    dev_container.scan(profile=Profile.DEVELOPMENT)

    # Resolve service
    registration_service = dev_container.resolve(UserRegistrationService)

    # Use the service
    user_id = await registration_service.register_user('Charlie Brown', 'charlie@dev.local')

    print(f'\n✅ User registered with ID: {user_id}')


async def main() -> None:
    """Run all examples."""
    print('\n🎯 Hexagonal Architecture with dioxide\n')

    await production_example()
    await test_example()
    await development_example()

    print('\n' + '=' * 70)
    print('KEY TAKEAWAYS')
    print('=' * 70)
    print('✅ Core logic (services) has ZERO infrastructure knowledge')
    print('✅ Testing uses fast fakes, not slow mocks')
    print('✅ Swapping implementations = changing one line (profile)')
    print('✅ Type-safe dependency injection via constructor hints')
    print('✅ Ports (Protocols) define clear boundaries')
    print('=' * 70 + '\n')


if __name__ == '__main__':
    asyncio.run(main())
