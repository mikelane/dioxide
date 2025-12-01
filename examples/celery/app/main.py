"""Celery application with dioxide dependency injection.

This module sets up the Celery app with dioxide integration and defines
the background tasks that use scoped dependency injection.
"""

import os

from celery import Celery
from dioxide import Profile
from dioxide.celery import (
    configure_dioxide,
    scoped_task,
)

from .domain.services import (
    NotificationService,
    OrderService,
)

# Import adapters to register them with dioxide
from .adapters import fakes  # noqa: F401
from .adapters import logging  # noqa: F401

# Create Celery app
celery_app = Celery(
    'tasks',
    broker=os.getenv('CELERY_BROKER_URL', 'redis://localhost:6379/0'),
    backend=os.getenv('CELERY_RESULT_BACKEND', 'redis://localhost:6379/0'),
)

# Configure Celery
celery_app.conf.update(
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='UTC',
    enable_utc=True,
)

# Get profile from environment (default to development)
profile_name = os.getenv('PROFILE', 'development')
profile = Profile(profile_name)

# Configure dioxide with the Celery app
configure_dioxide(celery_app, profile=profile, packages=['app'])


@scoped_task(celery_app)
def process_order(scope, order_id: str) -> dict:
    """Process an order in the background.

    Args:
        scope: Injected ScopedContainer (automatic)
        order_id: The order to process

    Returns:
        The processed order data
    """
    service = scope.resolve(OrderService)
    return service.process(order_id)


@scoped_task(celery_app)
def send_notification(scope, user_id: str, message: str) -> None:
    """Send a notification to a user.

    Args:
        scope: Injected ScopedContainer (automatic)
        user_id: The user to notify
        message: The notification message
    """
    service = scope.resolve(NotificationService)
    service.notify_user(user_id, message)
