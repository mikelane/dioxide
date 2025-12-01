"""Tests for Celery background tasks.

These tests use Celery's eager mode to execute tasks synchronously,
allowing for fast, deterministic testing with fake adapters.
"""

from dioxide.celery import scoped_task

from app.domain.services import (
    NotificationService,
    OrderService,
)


class DescribeOrderProcessing:
    """Tests for order processing task."""

    def it_processes_order_and_updates_status(self, celery_app, container, order_adapter):
        """Processing an order updates its status."""

        @scoped_task(celery_app)
        def process_order(scope, order_id: str) -> dict:
            service = scope.resolve(OrderService)
            return service.process(order_id)

        result = process_order.delay('order-123')

        assert order_adapter.orders['order-123']['status'] == 'processing'
        assert result.get()['id'] == 'order-123'

    def it_sends_notification_when_processing_order(
        self, celery_app, container, notification_adapter
    ):
        """Processing an order sends a notification to the user."""

        @scoped_task(celery_app)
        def process_order(scope, order_id: str) -> dict:
            service = scope.resolve(OrderService)
            return service.process(order_id)

        process_order.delay('order-123')

        assert len(notification_adapter.sent) == 1
        assert notification_adapter.sent[0]['user_id'] == 'user-1'
        assert 'order-123' in notification_adapter.sent[0]['message']


class DescribeNotificationTask:
    """Tests for notification task."""

    def it_sends_notification_to_user(self, celery_app, container, notification_adapter):
        """Notification task sends message to the specified user."""

        @scoped_task(celery_app)
        def send_notification(scope, user_id: str, message: str) -> None:
            service = scope.resolve(NotificationService)
            service.notify_user(user_id, message)

        send_notification.delay('user-42', 'Your order shipped!')

        assert len(notification_adapter.sent) == 1
        assert notification_adapter.sent[0]['user_id'] == 'user-42'
        assert notification_adapter.sent[0]['message'] == 'Your order shipped!'


class DescribeTaskIsolation:
    """Tests for task scope isolation."""

    def it_creates_fresh_scope_per_task_execution(
        self, celery_app, container, order_adapter
    ):
        """Each task execution gets its own isolated scope."""

        @scoped_task(celery_app)
        def process_order(scope, order_id: str) -> dict:
            service = scope.resolve(OrderService)
            return service.process(order_id)

        # Process two different orders
        result1 = process_order.delay('order-123')
        result2 = process_order.delay('order-456')

        # Both orders should be processed independently
        assert result1.get()['id'] == 'order-123'
        assert result2.get()['id'] == 'order-456'
        assert order_adapter.orders['order-123']['status'] == 'processing'
        assert order_adapter.orders['order-456']['status'] == 'processing'
