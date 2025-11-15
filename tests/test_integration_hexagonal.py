"""Integration tests for complete hexagonal architecture workflows.

This module tests the end-to-end integration of dioxide's hexagonal architecture
support, including:
- Services depending on ports (Protocol interfaces)
- Adapters implementing ports with profile-based selection
- Complete dependency injection across the hexagonal architecture
- Profile swapping for testing
"""

from typing import Protocol

from dioxide import (
    Container,
    Profile,
    adapter,
    service,
)


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
