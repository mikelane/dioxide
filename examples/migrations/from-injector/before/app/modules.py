"""Injector module configuration.

This is the verbose part where you bind interfaces to implementations.
dioxide replaces this with @adapter.for_() decorators.
"""

from injector import Binder, Module, singleton

from app.adapters import (
    EmailNotificationService,
    FakeNotificationService,
    FakeOrderRepository,
    FakePaymentGateway,
    PostgresOrderRepository,
    StripePaymentGateway,
)
from app.ports import NotificationService, OrderRepository, PaymentGateway


class ProductionModule(Module):
    """Production bindings for real implementations.

    In injector, you create Module classes that configure the Binder.
    Each binding maps an interface to an implementation.
    """

    def configure(self, binder: Binder) -> None:
        binder.bind(OrderRepository, to=PostgresOrderRepository, scope=singleton)
        binder.bind(NotificationService, to=EmailNotificationService, scope=singleton)
        binder.bind(PaymentGateway, to=StripePaymentGateway, scope=singleton)


class TestModule(Module):
    """Test bindings for fake implementations.

    For testing, you create a separate module with fake bindings.
    This requires maintaining parallel module definitions.
    """

    def configure(self, binder: Binder) -> None:
        binder.bind(OrderRepository, to=FakeOrderRepository, scope=singleton)
        binder.bind(NotificationService, to=FakeNotificationService, scope=singleton)
        binder.bind(PaymentGateway, to=FakePaymentGateway, scope=singleton)
