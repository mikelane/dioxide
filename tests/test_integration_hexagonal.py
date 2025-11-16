"""Integration tests for complete hexagonal architecture workflows.

This module tests the end-to-end integration of dioxide's hexagonal architecture
support, including:
- Services depending on ports (Protocol interfaces)
- Adapters implementing ports with profile-based selection
- Complete dependency injection across the hexagonal architecture
- Profile swapping for testing
"""

import asyncio
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
