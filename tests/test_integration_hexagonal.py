"""Integration tests for complete hexagonal architecture workflows.

This module tests the end-to-end integration of dioxide's hexagonal architecture
support, including:
- Services depending on ports (Protocol interfaces)
- Adapters implementing ports with profile-based selection
- Complete dependency injection across the hexagonal architecture
- Profile swapping for testing
"""

from typing import Protocol

import pytest

from dioxide import (
    Container,
    Profile,
    _clear_registry,
    adapter,
    profile,
    service,
)


@pytest.fixture(autouse=True)
def clear_registry() -> None:
    """Clear the component registry before each test to ensure test isolation."""
    _clear_registry()


class DescribeHexagonalArchitectureBasicEndToEnd:
    """Basic end-to-end integration tests for hexagonal architecture."""

    def it_swaps_adapters_by_profile(self) -> None:
        """Production profile uses real adapter, test profile uses fake."""

        # Define port (interface)
        class EmailPort(Protocol):
            """Port for sending emails."""

            async def send(self, to: str, subject: str, body: str) -> None:
                """Send an email."""
                ...

        # Production adapter (real implementation)
        @adapter.for_(EmailPort, profile=Profile.PRODUCTION)
        class SendGridAdapter:
            """SendGrid email adapter for production."""

            async def send(self, to: str, subject: str, body: str) -> None:
                """Send email via SendGrid API."""
                pass  # Real implementation would call SendGrid API

        # Test adapter (fake for testing)
        @adapter.for_(EmailPort, profile=Profile.TEST)
        class FakeEmailAdapter:
            """Fake email adapter for testing."""

            def __init__(self) -> None:
                self.sent_emails: list[dict[str, str]] = []

            async def send(self, to: str, subject: str, body: str) -> None:
                """Record email instead of sending."""
                self.sent_emails.append({'to': to, 'subject': subject, 'body': body})

        # Service depending on port
        @service
        class UserService:
            """User service using email port."""

            def __init__(self, email: EmailPort) -> None:
                self.email = email

            async def register(self, email: str) -> None:
                """Register user and send welcome email."""
                await self.email.send(to=email, subject='Welcome', body='Welcome to our service!')

        # Production container - uses SendGridAdapter
        prod_container = Container()
        prod_container.scan(profile=Profile.PRODUCTION)
        prod_service = prod_container.resolve(UserService)
        assert isinstance(prod_service.email, SendGridAdapter)

        # Test container - uses FakeEmailAdapter
        test_container = Container()
        test_container.scan(profile=Profile.TEST)
        test_service = test_container.resolve(UserService)

        # Verify test adapter is injected
        fake_adapter = test_container.resolve(EmailPort)
        assert isinstance(fake_adapter, FakeEmailAdapter)
        assert test_service.email is fake_adapter

        # Use service and verify fake captures emails
        import asyncio

        asyncio.run(test_service.register('test@example.com'))

        assert len(fake_adapter.sent_emails) == 1
        assert fake_adapter.sent_emails[0]['to'] == 'test@example.com'
        assert fake_adapter.sent_emails[0]['subject'] == 'Welcome'
        assert fake_adapter.sent_emails[0]['body'] == 'Welcome to our service!'

    def it_injects_port_implementation_into_service(self) -> None:
        """Services receive port implementations automatically."""

        # Define port
        class LoggerPort(Protocol):
            """Port for logging."""

            def log(self, message: str) -> None:
                """Log a message."""
                ...

        # Adapter implementation
        @adapter.for_(LoggerPort, profile=Profile.TEST)
        class InMemoryLogger:
            """In-memory logger for testing."""

            def __init__(self) -> None:
                self.logs: list[str] = []

            def log(self, message: str) -> None:
                """Store log message in memory."""
                self.logs.append(message)

        # Service using port
        @service
        class OrderService:
            """Order service using logger port."""

            def __init__(self, logger: LoggerPort) -> None:
                self.logger = logger

            def create_order(self, order_id: str) -> None:
                """Create an order."""
                self.logger.log(f'Order created: {order_id}')

        # Container resolves service with adapter
        container = Container()
        container.scan(profile=Profile.TEST)

        order_service = container.resolve(OrderService)
        logger_adapter = container.resolve(LoggerPort)

        assert isinstance(logger_adapter, InMemoryLogger)
        assert order_service.logger is logger_adapter

        # Verify it works
        order_service.create_order('ORDER-123')
        assert len(logger_adapter.logs) == 1
        assert logger_adapter.logs[0] == 'Order created: ORDER-123'

    def it_supports_singleton_adapters_across_services(self) -> None:
        """Multiple services share same singleton adapter instance."""

        # Define port
        class CachePort(Protocol):
            """Port for caching."""

            def set(self, key: str, value: str) -> None:
                """Set cache value."""
                ...

            def get(self, key: str) -> str | None:
                """Get cache value."""
                ...

        # Singleton adapter
        @adapter.for_(CachePort, profile=Profile.TEST)
        class InMemoryCacheAdapter:
            """In-memory cache adapter."""

            def __init__(self) -> None:
                self.cache: dict[str, str] = {}

            def set(self, key: str, value: str) -> None:
                """Store in memory."""
                self.cache[key] = value

            def get(self, key: str) -> str | None:
                """Retrieve from memory."""
                return self.cache.get(key)

        # Two services using same port
        @service
        class ProductService:
            """Product service using cache."""

            def __init__(self, cache: CachePort) -> None:
                self.cache = cache

        @service
        class InventoryService:
            """Inventory service using cache."""

            def __init__(self, cache: CachePort) -> None:
                self.cache = cache

        # Resolve services
        container = Container()
        container.scan(profile=Profile.TEST)

        product_service = container.resolve(ProductService)
        inventory_service = container.resolve(InventoryService)

        # Both services share same cache instance (singleton)
        assert product_service.cache is inventory_service.cache

        # Verify shared state
        product_service.cache.set('product:123', 'Laptop')
        assert inventory_service.cache.get('product:123') == 'Laptop'


class DescribeMultiPortServiceDependencies:
    """Integration tests for services depending on multiple ports."""

    def it_injects_multiple_ports_into_single_service(self) -> None:
        """Service can depend on multiple different ports."""

        # Define two ports
        class EmailPort(Protocol):
            """Port for sending emails."""

            def send(self, to: str, subject: str, body: str) -> None:
                """Send an email."""
                ...

        class SmsPort(Protocol):
            """Port for sending SMS."""

            def send(self, to: str, message: str) -> None:
                """Send an SMS."""
                ...

        # Adapters for each port
        @adapter.for_(EmailPort, profile=Profile.TEST)
        class FakeEmailAdapter:
            """Fake email adapter."""

            def __init__(self) -> None:
                self.sent_emails: list[dict[str, str]] = []

            def send(self, to: str, subject: str, body: str) -> None:
                """Record email."""
                self.sent_emails.append({'to': to, 'subject': subject, 'body': body})

        @adapter.for_(SmsPort, profile=Profile.TEST)
        class FakeSmsAdapter:
            """Fake SMS adapter."""

            def __init__(self) -> None:
                self.sent_sms: list[dict[str, str]] = []

            def send(self, to: str, message: str) -> None:
                """Record SMS."""
                self.sent_sms.append({'to': to, 'message': message})

        # Service depending on both ports
        @service
        class NotificationService:
            """Notification service using email and SMS."""

            def __init__(self, email: EmailPort, sms: SmsPort) -> None:
                self.email = email
                self.sms = sms

            def notify_user(self, email_addr: str, phone: str, message: str) -> None:
                """Send notification via email and SMS."""
                self.email.send(to=email_addr, subject='Notification', body=message)
                self.sms.send(to=phone, message=message)

        # Resolve service with both ports injected
        container = Container()
        container.scan(profile=Profile.TEST)

        notification_service = container.resolve(NotificationService)
        email_adapter = container.resolve(EmailPort)
        sms_adapter = container.resolve(SmsPort)

        assert isinstance(email_adapter, FakeEmailAdapter)
        assert isinstance(sms_adapter, FakeSmsAdapter)
        assert notification_service.email is email_adapter
        assert notification_service.sms is sms_adapter

        # Use service
        notification_service.notify_user('user@example.com', '+1234567890', 'Hello!')

        assert len(email_adapter.sent_emails) == 1
        assert email_adapter.sent_emails[0]['to'] == 'user@example.com'
        assert email_adapter.sent_emails[0]['body'] == 'Hello!'

        assert len(sms_adapter.sent_sms) == 1
        assert sms_adapter.sent_sms[0]['to'] == '+1234567890'
        assert sms_adapter.sent_sms[0]['message'] == 'Hello!'

    def it_handles_service_with_port_and_regular_dependencies(self) -> None:
        """Service can mix port dependencies with regular component dependencies."""

        # Port
        class LoggerPort(Protocol):
            """Port for logging."""

            def log(self, message: str) -> None:
                """Log a message."""
                ...

        # Adapter
        @adapter.for_(LoggerPort, profile=Profile.TEST)
        class InMemoryLogger:
            """In-memory logger."""

            def __init__(self) -> None:
                self.logs: list[str] = []

            def log(self, message: str) -> None:
                """Store log."""
                self.logs.append(message)

        # Regular component
        @service
        class ConfigService:
            """Configuration service."""

            def __init__(self) -> None:
                self.app_name = 'MyApp'

        # Service mixing port and regular dependencies
        @service
        class ApplicationService:
            """Application service with mixed dependencies."""

            def __init__(self, logger: LoggerPort, config: ConfigService) -> None:
                self.logger = logger
                self.config = config

            def start(self) -> None:
                """Start application."""
                self.logger.log(f'{self.config.app_name} starting...')

        # Resolve and verify
        container = Container()
        container.scan(profile=Profile.TEST)

        app_service = container.resolve(ApplicationService)
        logger_adapter = container.resolve(LoggerPort)
        config = container.resolve(ConfigService)

        assert isinstance(logger_adapter, InMemoryLogger)
        assert isinstance(config, ConfigService)
        assert app_service.logger is logger_adapter
        assert app_service.config is config

        app_service.start()
        assert len(logger_adapter.logs) == 1
        assert logger_adapter.logs[0] == 'MyApp starting...'

    def it_supports_multiple_services_sharing_multiple_ports(self) -> None:
        """Multiple services can share multiple singleton port adapters."""

        # Define ports
        class DatabasePort(Protocol):
            """Port for database access."""

            def query(self, sql: str) -> list[str]:
                """Execute query."""
                ...

        class CachePort(Protocol):
            """Port for caching."""

            def get(self, key: str) -> str | None:
                """Get cached value."""
                ...

            def set(self, key: str, value: str) -> None:
                """Set cached value."""
                ...

        # Adapters
        @adapter.for_(DatabasePort, profile=Profile.TEST)
        class InMemoryDatabase:
            """In-memory database."""

            def __init__(self) -> None:
                self.data: list[str] = []

            def query(self, sql: str) -> list[str]:
                """Return stored data."""
                return self.data.copy()

        @adapter.for_(CachePort, profile=Profile.TEST)
        class InMemoryCache:
            """In-memory cache."""

            def __init__(self) -> None:
                self.cache: dict[str, str] = {}

            def get(self, key: str) -> str | None:
                """Get from cache."""
                return self.cache.get(key)

            def set(self, key: str, value: str) -> None:
                """Set in cache."""
                self.cache[key] = value

        # Two services using both ports
        @service
        class UserRepository:
            """User repository."""

            def __init__(self, db: DatabasePort, cache: CachePort) -> None:
                self.db = db
                self.cache = cache

        @service
        class ProductRepository:
            """Product repository."""

            def __init__(self, db: DatabasePort, cache: CachePort) -> None:
                self.db = db
                self.cache = cache

        # Resolve services
        container = Container()
        container.scan(profile=Profile.TEST)

        user_repo = container.resolve(UserRepository)
        product_repo = container.resolve(ProductRepository)

        # Both services share same adapter instances (singletons)
        assert user_repo.db is product_repo.db
        assert user_repo.cache is product_repo.cache

        # Verify shared state across services
        user_repo.cache.set('shared-key', 'shared-value')
        assert product_repo.cache.get('shared-key') == 'shared-value'


class DescribeComplexDependencyChains:
    """Integration tests for complex service dependency chains."""

    def it_resolves_service_depending_on_service_depending_on_port(self) -> None:
        """Service A → Service B → Port creates complete chain."""

        # Port
        class DatabasePort(Protocol):
            """Port for database access."""

            def save(self, data: str) -> None:
                """Save data."""
                ...

            def load(self) -> list[str]:
                """Load data."""
                ...

        # Adapter
        @adapter.for_(DatabasePort, profile=Profile.TEST)
        class InMemoryDatabase:
            """In-memory database."""

            def __init__(self) -> None:
                self.data: list[str] = []

            def save(self, data: str) -> None:
                """Store data."""
                self.data.append(data)

            def load(self) -> list[str]:
                """Return all data."""
                return self.data.copy()

        # Service B (depends on port)
        @service
        class UserRepository:
            """User repository depending on database port."""

            def __init__(self, db: DatabasePort) -> None:
                self.db = db

            def create_user(self, username: str) -> None:
                """Create user."""
                self.db.save(f'user:{username}')

            def get_users(self) -> list[str]:
                """Get all users."""
                return self.db.load()

        # Service A (depends on Service B)
        @service
        class UserController:
            """User controller depending on repository."""

            def __init__(self, repository: UserRepository) -> None:
                self.repository = repository

            def register_user(self, username: str) -> None:
                """Register a user."""
                self.repository.create_user(username)

        # Resolve entire chain
        container = Container()
        container.scan(profile=Profile.TEST)

        controller = container.resolve(UserController)
        repository = container.resolve(UserRepository)
        db_adapter = container.resolve(DatabasePort)

        # Verify chain
        assert isinstance(db_adapter, InMemoryDatabase)
        assert isinstance(repository, UserRepository)
        assert isinstance(controller, UserController)
        assert controller.repository is repository
        assert repository.db is db_adapter

        # Verify functionality through chain
        controller.register_user('alice')
        controller.register_user('bob')

        users = repository.get_users()
        assert len(users) == 2
        assert 'user:alice' in users
        assert 'user:bob' in users

    def it_handles_multi_level_service_chains_with_multiple_ports(self) -> None:
        """Complex chain: Service A → Service B → (Port1 + Port2)."""

        # Two ports
        class LoggerPort(Protocol):
            """Port for logging."""

            def log(self, message: str) -> None:
                """Log a message."""
                ...

        class CachePort(Protocol):
            """Port for caching."""

            def get(self, key: str) -> str | None:
                """Get cached value."""
                ...

            def set(self, key: str, value: str) -> None:
                """Set cached value."""
                ...

        # Adapters
        @adapter.for_(LoggerPort, profile=Profile.TEST)
        class InMemoryLogger:
            """In-memory logger."""

            def __init__(self) -> None:
                self.logs: list[str] = []

            def log(self, message: str) -> None:
                """Store log."""
                self.logs.append(message)

        @adapter.for_(CachePort, profile=Profile.TEST)
        class InMemoryCache:
            """In-memory cache."""

            def __init__(self) -> None:
                self.cache: dict[str, str] = {}

            def get(self, key: str) -> str | None:
                """Get from cache."""
                return self.cache.get(key)

            def set(self, key: str, value: str) -> None:
                """Set in cache."""
                self.cache[key] = value

        # Service B (depends on both ports)
        @service
        class DataService:
            """Data service with logging and caching."""

            def __init__(self, logger: LoggerPort, cache: CachePort) -> None:
                self.logger = logger
                self.cache = cache

            def get_data(self, key: str) -> str:
                """Get data with caching and logging."""
                cached = self.cache.get(key)
                if cached:
                    self.logger.log(f'Cache hit: {key}')
                    return cached

                self.logger.log(f'Cache miss: {key}')
                value = f'computed-{key}'
                self.cache.set(key, value)
                return value

        # Service A (depends on Service B)
        @service
        class ApiController:
            """API controller depending on data service."""

            def __init__(self, data_service: DataService) -> None:
                self.data_service = data_service

            def handle_request(self, key: str) -> str:
                """Handle API request."""
                return self.data_service.get_data(key)

        # Resolve entire chain
        container = Container()
        container.scan(profile=Profile.TEST)

        controller = container.resolve(ApiController)
        data_service = container.resolve(DataService)
        logger = container.resolve(LoggerPort)
        cache = container.resolve(CachePort)

        # Verify chain structure
        assert controller.data_service is data_service
        assert data_service.logger is logger
        assert data_service.cache is cache
        assert isinstance(logger, InMemoryLogger)
        assert isinstance(cache, InMemoryCache)

        # Verify functionality
        result1 = controller.handle_request('key1')
        assert result1 == 'computed-key1'
        assert 'Cache miss: key1' in logger.logs

        result2 = controller.handle_request('key1')
        assert result2 == 'computed-key1'
        assert 'Cache hit: key1' in logger.logs

    def it_resolves_diamond_dependency_with_ports(self) -> None:
        """Diamond dependency: Service A → (Service B + Service C) → Port."""

        # Shared port
        class EventPort(Protocol):
            """Port for event publishing."""

            def publish(self, event: str) -> None:
                """Publish an event."""
                ...

        # Adapter
        @adapter.for_(EventPort, profile=Profile.TEST)
        class InMemoryEventBus:
            """In-memory event bus."""

            def __init__(self) -> None:
                self.events: list[str] = []

            def publish(self, event: str) -> None:
                """Store event."""
                self.events.append(event)

        # Two services depending on same port
        @service
        class UserEventService:
            """User event service."""

            def __init__(self, events: EventPort) -> None:
                self.events = events

            def user_registered(self, username: str) -> None:
                """Publish user registered event."""
                self.events.publish(f'USER_REGISTERED:{username}')

        @service
        class AuditService:
            """Audit service."""

            def __init__(self, events: EventPort) -> None:
                self.events = events

            def log_action(self, action: str) -> None:
                """Publish audit event."""
                self.events.publish(f'AUDIT:{action}')

        # Top-level service depending on both
        @service
        class ApplicationOrchestrator:
            """Application orchestrator."""

            def __init__(
                self, user_events: UserEventService, audit: AuditService
            ) -> None:
                self.user_events = user_events
                self.audit = audit

            def register_user(self, username: str) -> None:
                """Register user with events and audit."""
                self.user_events.user_registered(username)
                self.audit.log_action(f'USER_REGISTRATION:{username}')

        # Resolve diamond dependency
        container = Container()
        container.scan(profile=Profile.TEST)

        orchestrator = container.resolve(ApplicationOrchestrator)
        user_events = container.resolve(UserEventService)
        audit = container.resolve(AuditService)
        event_bus = container.resolve(EventPort)

        # Verify diamond structure - both services share same port instance
        assert orchestrator.user_events is user_events
        assert orchestrator.audit is audit
        assert user_events.events is event_bus
        assert audit.events is event_bus
        assert isinstance(event_bus, InMemoryEventBus)

        # Verify functionality - both services publish to same event bus
        orchestrator.register_user('alice')

        assert len(event_bus.events) == 2
        assert 'USER_REGISTERED:alice' in event_bus.events
        assert 'AUDIT:USER_REGISTRATION:alice' in event_bus.events


class DescribeErrorScenarios:
    """Integration tests for error handling in hexagonal architecture."""

    def it_raises_error_when_no_adapter_registered_for_port(self) -> None:
        """Container raises clear error when port has no adapter."""

        # Define port but NO adapter
        class EmailPort(Protocol):
            """Port for sending emails."""

            def send(self, to: str, subject: str, body: str) -> None:
                """Send an email."""
                ...

        # Service depending on port
        @service
        class UserService:
            """User service using email port."""

            def __init__(self, email: EmailPort) -> None:
                self.email = email

        # Scan container
        container = Container()
        container.scan(profile=Profile.TEST)

        # Should raise when trying to resolve service with missing adapter
        with pytest.raises(KeyError, match='(EmailPort|email)'):
            container.resolve(UserService)

    def it_raises_error_when_adapter_profile_does_not_match(self) -> None:
        """Container raises error when adapter profile doesn't match scan profile."""

        # Port
        class DatabasePort(Protocol):
            """Port for database access."""

            def query(self, sql: str) -> list[str]:
                """Execute query."""
                ...

        # Adapter only for PRODUCTION profile
        @adapter.for_(DatabasePort, profile=Profile.PRODUCTION)
        class PostgresAdapter:
            """Postgres adapter."""

            def query(self, sql: str) -> list[str]:
                """Execute SQL."""
                return []

        # Service
        @service
        class DataService:
            """Data service."""

            def __init__(self, db: DatabasePort) -> None:
                self.db = db

        # Scan with TEST profile - adapter is PRODUCTION only
        container = Container()
        container.scan(profile=Profile.TEST)

        # Should raise when trying to resolve service (profile mismatch)
        with pytest.raises(KeyError):
            container.resolve(DataService)

    def it_handles_missing_service_dependency_gracefully(self) -> None:
        """Container raises clear error when service dependency is missing."""

        # Service A depends on non-existent Service B
        class ServiceB:
            """Service B (not decorated)."""

            pass

        @service
        class ServiceA:
            """Service A depending on unregistered service."""

            def __init__(self, service_b: ServiceB) -> None:
                self.service_b = service_b

        container = Container()
        container.scan(profile=Profile.TEST)

        # Should raise when trying to resolve (missing dependency)
        with pytest.raises(KeyError, match='ServiceB'):
            container.resolve(ServiceA)

    def it_detects_circular_dependencies(self) -> None:
        """Container detects and reports circular dependencies."""

        # Circular dependency: A → B → A
        # Note: Forward references needed for circular dependencies
        @service
        class ServiceA:
            """Service A."""

            def __init__(self, service_b: 'ServiceB') -> None:
                self.service_b = service_b

        @service
        class ServiceB:
            """Service B."""

            def __init__(self, service_a: ServiceA) -> None:
                self.service_a = service_a

        container = Container()
        container.scan(profile=Profile.TEST)

        # Should detect circular dependency
        with pytest.raises((RecursionError, RuntimeError, KeyError)):
            container.resolve(ServiceA)

    @pytest.mark.parametrize(
        'profile',
        [
            pytest.param(Profile.PRODUCTION, id='production'),
            pytest.param(Profile.TEST, id='test'),
            pytest.param(Profile.DEVELOPMENT, id='development'),
        ],
    )
    def it_handles_port_without_profile_decorator(self, profile: Profile) -> None:
        """Adapters without profile decorator are available in all profiles."""

        # Port
        class LoggerPort(Protocol):
            """Port for logging."""

            def log(self, message: str) -> None:
                """Log a message."""
                ...

        # Adapter without profile (should be available in all profiles)
        @adapter.for_(LoggerPort)
        class ConsoleLogger:
            """Console logger available in all profiles."""

            def __init__(self) -> None:
                self.logs: list[str] = []

            def log(self, message: str) -> None:
                """Store log."""
                self.logs.append(message)

        @service
        class Service:
            """Service using logger."""

            def __init__(self, logger: LoggerPort) -> None:
                self.logger = logger

        # Should work with any profile
        container = Container()
        container.scan(profile=profile)

        service = container.resolve(Service)
        logger = container.resolve(LoggerPort)

        assert isinstance(logger, ConsoleLogger)
        assert service.logger is logger

    def it_handles_multiple_adapters_for_same_port_different_profiles(self) -> None:
        """Multiple adapters for same port with different profiles coexist."""

        # Port
        class StoragePort(Protocol):
            """Port for storage."""

            def save(self, data: str) -> None:
                """Save data."""
                ...

        # Production adapter
        @adapter.for_(StoragePort, profile=Profile.PRODUCTION)
        class S3Storage:
            """S3 storage for production."""

            def __init__(self) -> None:
                self.saved_data: list[str] = []

            def save(self, data: str) -> None:
                """Save to S3."""
                self.saved_data.append(f's3:{data}')

        # Test adapter
        @adapter.for_(StoragePort, profile=Profile.TEST)
        class InMemoryStorage:
            """In-memory storage for testing."""

            def __init__(self) -> None:
                self.saved_data: list[str] = []

            def save(self, data: str) -> None:
                """Save to memory."""
                self.saved_data.append(f'memory:{data}')

        @service
        class FileService:
            """File service."""

            def __init__(self, storage: StoragePort) -> None:
                self.storage = storage

        # Production container gets S3
        prod_container = Container()
        prod_container.scan(profile=Profile.PRODUCTION)
        prod_service = prod_container.resolve(FileService)
        prod_storage = prod_container.resolve(StoragePort)

        assert isinstance(prod_storage, S3Storage)
        assert prod_service.storage is prod_storage

        prod_service.storage.save('file1')
        assert prod_storage.saved_data == ['s3:file1']

        # Test container gets InMemory
        test_container = Container()
        test_container.scan(profile=Profile.TEST)
        test_service = test_container.resolve(FileService)
        test_storage = test_container.resolve(StoragePort)

        assert isinstance(test_storage, InMemoryStorage)
        assert test_service.storage is test_storage

        test_service.storage.save('file2')
        assert test_storage.saved_data == ['memory:file2']

        # Verify isolation
        assert prod_storage.saved_data == ['s3:file1']  # Unchanged
