"""Pytest configuration and fixtures for Celery example tests."""

import os

import pytest
from celery import Celery
from dioxide import (
    Container,
    Profile,
    _clear_registry,
)
from dioxide.celery import configure_dioxide

# Set test profile before importing app modules
os.environ['PROFILE'] = 'test'


@pytest.fixture(autouse=True)
def clear_registry():
    """Clear the dioxide registry before each test."""
    _clear_registry()


@pytest.fixture
def celery_app():
    """Create a Celery app configured for eager testing."""
    app = Celery('test_tasks')
    app.conf.update(
        task_always_eager=True,
        task_eager_propagates=True,
        broker_url='memory://',
        result_backend='cache+memory://',
    )
    return app


@pytest.fixture
def container(celery_app):
    """Create and configure a dioxide container for testing."""
    # Import adapters to register them
    from app.adapters import fakes  # noqa: F401

    container = Container()
    configure_dioxide(celery_app, profile=Profile.TEST, container=container)
    return container


@pytest.fixture
def order_adapter(container):
    """Get the fake order adapter for test assertions."""
    from app.domain.ports import OrderPort

    return container.resolve(OrderPort)


@pytest.fixture
def notification_adapter(container):
    """Get the fake notification adapter for test assertions."""
    from app.domain.ports import NotificationPort

    return container.resolve(NotificationPort)
