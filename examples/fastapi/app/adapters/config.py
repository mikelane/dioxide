"""Configuration adapters for different profiles.

This module demonstrates CONSTRUCTOR DEPENDENCY INJECTION - other adapters
(like PostgresAdapter and SendGridAdapter) can depend on ConfigPort to get
their configuration settings.

How constructor injection works:
    When dioxide sees an adapter/service with constructor parameters that have
    type hints, it automatically resolves those dependencies from the container.

    For example:
        @adapter.for_(EmailPort, profile=Profile.PRODUCTION)
        class SendGridAdapter:
            def __init__(self, config: ConfigPort) -> None:  # <-- Auto-injected!
                self.api_key = config.get("SENDGRID_API_KEY")

    dioxide:
    1. Sees SendGridAdapter needs ConfigPort
    2. Looks up ConfigPort in the container
    3. Finds EnvConfigAdapter (for PRODUCTION profile)
    4. Creates EnvConfigAdapter instance
    5. Passes it to SendGridAdapter's __init__

The key insight: The dependency (ConfigPort) must be registered in the
container. Here we register config adapters for each profile.
"""

import os

from dioxide import Profile, adapter

from ..domain.ports import ConfigPort


@adapter.for_(ConfigPort, profile=Profile.PRODUCTION)
class EnvConfigAdapter:
    """Production configuration from environment variables.

    This adapter reads configuration from environment variables, which is
    the standard approach for production deployments (12-factor app).

    Other adapters can depend on this:
        @adapter.for_(DatabasePort, profile=Profile.PRODUCTION)
        class PostgresAdapter:
            def __init__(self, config: ConfigPort) -> None:
                self.url = config.get("DATABASE_URL")
    """

    def get(self, key: str, default: str = "") -> str:
        """Get configuration from environment variables.

        Args:
            key: Environment variable name
            default: Default value if not set

        Returns:
            Environment variable value or default
        """
        return os.environ.get(key, default)


@adapter.for_(ConfigPort, profile=Profile.DEVELOPMENT)
class DevConfigAdapter:
    """Development configuration with sensible defaults.

    For local development, this adapter provides default values that work
    out of the box without requiring environment setup.
    """

    def __init__(self) -> None:
        """Initialize with development defaults."""
        self._defaults = {
            "DATABASE_URL": "sqlite:///dev.db",
            "SENDGRID_API_KEY": "",  # Empty = logging only
            "SENDGRID_FROM_EMAIL": "dev@localhost",
            "LOG_LEVEL": "DEBUG",
        }

    def get(self, key: str, default: str = "") -> str:
        """Get configuration with development defaults.

        Args:
            key: Configuration key
            default: Default if not in defaults dict

        Returns:
            Configuration value
        """
        # Check environment first, fall back to development defaults
        return os.environ.get(key, self._defaults.get(key, default))


@adapter.for_(ConfigPort, profile=Profile.TEST)
class FakeConfigAdapter:
    """Fake configuration for testing.

    Test adapters often don't need external dependencies - they just store
    data in memory. This fake config adapter provides predictable values
    for tests.

    Unlike production/dev adapters, this one doesn't read environment
    variables, making tests deterministic and isolated.
    """

    def __init__(self) -> None:
        """Initialize with test configuration.

        Note: No dependencies needed! Test fakes are typically simple
        and don't require constructor injection.
        """
        self.values: dict[str, str] = {
            "DATABASE_URL": ":memory:",
            "SENDGRID_API_KEY": "test-api-key",
            "SENDGRID_FROM_EMAIL": "test@example.com",
            "LOG_LEVEL": "WARNING",
        }

    def get(self, key: str, default: str = "") -> str:
        """Get configuration from in-memory storage.

        Args:
            key: Configuration key
            default: Default if not set

        Returns:
            Test configuration value
        """
        return self.values.get(key, default)

    def set(self, key: str, value: str) -> None:
        """Set a configuration value for testing.

        This method is only available on the test fake - it allows tests
        to control configuration values.

        Args:
            key: Configuration key
            value: Configuration value
        """
        self.values[key] = value
