"""Logging adapters for development.

These adapters log operations instead of performing real actions,
useful for development and debugging.
"""

import logging

from dioxide import (
    Profile,
    adapter,
)

from ..domain.ports import (
    NotificationPort,
    OrderPort,
)

logger = logging.getLogger(__name__)


@adapter.for_(OrderPort, profile=Profile.DEVELOPMENT)
class LoggingOrderAdapter:
    """Order adapter that logs operations.

    Uses in-memory storage with logging for development visibility.
    """

    def __init__(self) -> None:
        self.orders: dict[str, dict] = {
            'order-123': {
                'id': 'order-123',
                'user_id': 'user-1',
                'status': 'new',
                'items': ['item-1', 'item-2'],
            },
        }
        logger.info('LoggingOrderAdapter initialized')

    def get_order(self, order_id: str) -> dict:
        """Get order and log the access."""
        logger.info(f'Getting order: {order_id}')
        return self.orders.get(order_id, {'id': order_id, 'user_id': 'unknown', 'status': 'unknown', 'items': []})

    def update_status(self, order_id: str, status: str) -> None:
        """Update order status and log the change."""
        logger.info(f'Updating order {order_id} status to: {status}')
        if order_id in self.orders:
            self.orders[order_id]['status'] = status


@adapter.for_(NotificationPort, profile=Profile.DEVELOPMENT)
class LoggingNotificationAdapter:
    """Notification adapter that logs instead of sending.

    Safe for development - no real notifications are sent.
    """

    def __init__(self) -> None:
        logger.info('LoggingNotificationAdapter initialized')

    def send(self, user_id: str, message: str) -> None:
        """Log the notification instead of sending."""
        logger.info(f'[NOTIFICATION] To user {user_id}: {message}')
