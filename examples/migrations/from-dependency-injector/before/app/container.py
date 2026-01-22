"""Explicit container configuration for dependency-injector.

This is the verbose part that dioxide eliminates with decorators.
"""

from dependency_injector import containers, providers

from app.adapters import (
    PostgresUserRepository,
    RedisCacheService,
    SendGridEmailService,
)
from app.services import UserService


class Container(containers.DeclarativeContainer):
    """Application container with explicit provider configuration.

    In dependency-injector, you must:
    1. Define a Configuration provider for settings
    2. Create providers for each adapter (Singleton/Factory)
    3. Wire dependencies explicitly
    4. Override providers for testing
    """

    config = providers.Configuration()

    user_repository = providers.Singleton(
        PostgresUserRepository,
        connection_string=config.database.url,
    )

    email_service = providers.Singleton(
        SendGridEmailService,
        api_key=config.email.api_key,
    )

    cache_service = providers.Singleton(
        RedisCacheService,
        redis_url=config.cache.redis_url,
    )

    user_service = providers.Factory(
        UserService,
        repository=user_repository,
        email=email_service,
        cache=cache_service,
    )
