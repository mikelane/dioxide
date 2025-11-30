"""Fake adapters for testing.

These adapters provide in-memory implementations for fast, deterministic tests.
They store state that can be inspected in tests to verify behavior.
"""

from dioxide import (
    Profile,
    adapter,
)

from ..domain.ports import (
    NotificationPort,
    OrderPort,
)


@adapter.for_(OrderPort, profile=Profile.TEST)
class FakeOrderAdapter:
    """In-memory order adapter for testing.

    Stores orders in a dictionary for easy inspection in tests.
    """

    def __init__(self) -> None:
        self.orders: dict[str, dict] = {
            'order-123': {
                'id': 'order-123',
                'user_id': 'user-1',
                'status': 'new',
                'items': ['item-1', 'item-2'],
            },
            'order-456': {
                'id': 'order-456',
                'user_id': 'user-2',
                'status': 'new',
                'items': ['item-3'],
            },
        }

    def get_order(self, order_id: str) -> dict:
        """Get order from in-memory store."""
        return self.orders[order_id]

    def update_status(self, order_id: str, status: str) -> None:
        """Update order status in in-memory store."""
        self.orders[order_id]['status'] = status


@adapter.for_(NotificationPort, profile=Profile.TEST)
class FakeNotificationAdapter:
    """In-memory notification adapter for testing.

    Stores sent notifications for verification in tests.
    """

    def __init__(self) -> None:
        self.sent: list[dict] = []

    def send(self, user_id: str, message: str) -> None:
        """Store notification for later inspection."""
        self.sent.append({'user_id': user_id, 'message': message})
