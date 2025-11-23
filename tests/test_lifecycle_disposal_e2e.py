"""End-to-end tests for lifecycle disposal with real resource management (#135).

These tests simulate real-world scenarios with actual resource acquisition and
release (temp files, state tracking) to verify that resources are properly cleaned
up when Container.stop() is called.
"""

import os
import tempfile
from pathlib import Path
from typing import Protocol

import pytest

from dioxide import (
    Container,
    Profile,
    adapter,
    lifecycle,
    service,
)


class DescribeLifecycleDisposalE2E:
    """E2E tests with real resource management."""

    @pytest.mark.asyncio
    async def it_cleans_up_all_temporary_files_on_disposal(self) -> None:
        """Cleans up all temporary files when all components are disposed.

        Simulates a real application where components create temp files during
        initialization and must clean them up during disposal.
        """
        # Track temp files for cleanup verification
        temp_files: dict[str, Path] = {}

        @service
        @lifecycle
        class Database:
            def __init__(self) -> None:
                self.db_file: Path | None = None

            async def initialize(self) -> None:
                # Create temp file to simulate database connection
                fd, path = tempfile.mkstemp(suffix='.db')
                os.close(fd)  # Close file descriptor (required on Windows)
                self.db_file = Path(path)
                temp_files['Database'] = self.db_file
                # Write some data
                self.db_file.write_text('database data')

            async def dispose(self) -> None:
                # Clean up temp file
                if self.db_file and self.db_file.exists():
                    self.db_file.unlink()

        @service
        @lifecycle
        class Cache:
            def __init__(self, db: Database) -> None:
                self.db = db
                self.cache_file: Path | None = None

            async def initialize(self) -> None:
                # Create temp file to simulate cache storage
                fd, path = tempfile.mkstemp(suffix='.cache')
                os.close(fd)  # Close file descriptor (required on Windows)
                self.cache_file = Path(path)
                temp_files['Cache'] = self.cache_file
                # Write some data
                self.cache_file.write_text('cache data')

            async def dispose(self) -> None:
                # Clean up temp file
                if self.cache_file and self.cache_file.exists():
                    self.cache_file.unlink()

        @service
        @lifecycle
        class LogFile:
            def __init__(self, db: Database, cache: Cache) -> None:
                self.db = db
                self.cache = cache
                self.log_file: Path | None = None

            async def initialize(self) -> None:
                # Create temp file to simulate log file
                fd, path = tempfile.mkstemp(suffix='.log')
                os.close(fd)  # Close file descriptor (required on Windows)
                self.log_file = Path(path)
                temp_files['LogFile'] = self.log_file
                # Write some data
                self.log_file.write_text('log data')

            async def dispose(self) -> None:
                # Clean up temp file
                if self.log_file and self.log_file.exists():
                    self.log_file.unlink()

        container = Container()
        container.scan()

        await container.start()

        # Verify all temp files were created
        assert temp_files['Database'].exists(), 'Database temp file should exist'
        assert temp_files['Cache'].exists(), 'Cache temp file should exist'
        assert temp_files['LogFile'].exists(), 'LogFile temp file should exist'

        await container.stop()

        # Verify all temp files were cleaned up (THIS IS THE BUG)
        assert not temp_files['Database'].exists(), 'Database temp file should be cleaned up'
        assert not temp_files['Cache'].exists(), 'Cache temp file should be cleaned up (BUG: likely still exists)'
        assert not temp_files['LogFile'].exists(), 'LogFile temp file should be cleaned up (BUG: likely still exists)'

    @pytest.mark.asyncio
    async def it_releases_all_resources_with_multiple_start_stop_cycles(self) -> None:
        """Releases all resources correctly across multiple start/stop cycles.

        Simulates an application that can be started and stopped multiple times
        (like a test suite that recreates the container for each test).
        """
        # Track created files across cycles
        all_created_files: list[Path] = []

        @service
        @lifecycle
        class ResourceManager:
            def __init__(self) -> None:
                self.resource_file: Path | None = None

            async def initialize(self) -> None:
                fd, path = tempfile.mkstemp(suffix='.resource')
                os.close(fd)  # Close file descriptor (required on Windows)
                self.resource_file = Path(path)
                all_created_files.append(self.resource_file)
                self.resource_file.write_text('resource data')

            async def dispose(self) -> None:
                if self.resource_file and self.resource_file.exists():
                    self.resource_file.unlink()

        container = Container()
        container.scan()

        # Cycle 1
        await container.start()
        assert len(all_created_files) == 1
        assert all_created_files[0].exists()

        await container.stop()
        assert not all_created_files[0].exists(), 'Cycle 1 resource should be cleaned'

        # Cycle 2
        await container.start()
        assert len(all_created_files) == 2
        assert all_created_files[1].exists()

        await container.stop()
        assert not all_created_files[1].exists(), 'Cycle 2 resource should be cleaned'

        # Cycle 3
        await container.start()
        assert len(all_created_files) == 3
        assert all_created_files[2].exists()

        await container.stop()
        assert not all_created_files[2].exists(), 'Cycle 3 resource should be cleaned'

    @pytest.mark.asyncio
    async def it_simulates_fastapi_startup_shutdown_lifecycle(self) -> None:
        """Simulates a FastAPI-like application lifecycle with startup/shutdown.

        This is a realistic scenario where:
        - Multiple services acquire resources during startup
        - Application runs (processes requests)
        - All resources are released during shutdown
        """
        # State tracking to simulate real application
        app_state = {
            'db_connected': False,
            'cache_connected': False,
            'email_initialized': False,
            'requests_processed': 0,
        }

        # Temp files to verify cleanup
        temp_files: dict[str, Path] = {}

        class EmailPort(Protocol):
            async def send(self, to: str, subject: str, body: str) -> None: ...

        @adapter.for_(EmailPort, profile=Profile.PRODUCTION)
        @lifecycle
        class SendGridAdapter:
            def __init__(self) -> None:
                self.log_file: Path | None = None

            async def initialize(self) -> None:
                app_state['email_initialized'] = True
                # Create log file for sent emails
                fd, path = tempfile.mkstemp(suffix='.email-log')
                os.close(fd)  # Close file descriptor (required on Windows)
                self.log_file = Path(path)
                temp_files['email'] = self.log_file
                self.log_file.write_text('email,subject\n')

            async def dispose(self) -> None:
                app_state['email_initialized'] = False
                if self.log_file and self.log_file.exists():
                    self.log_file.unlink()

            async def send(self, to: str, subject: str, body: str) -> None:
                # Append to log file
                if self.log_file:
                    with self.log_file.open('a') as f:
                        f.write(f'{to},{subject}\n')

        @service
        @lifecycle
        class Database:
            def __init__(self) -> None:
                self.db_file: Path | None = None

            async def initialize(self) -> None:
                app_state['db_connected'] = True
                # Create database file
                fd, path = tempfile.mkstemp(suffix='.db')
                os.close(fd)  # Close file descriptor (required on Windows)
                self.db_file = Path(path)
                temp_files['db'] = self.db_file
                self.db_file.write_text('users table\n')

            async def dispose(self) -> None:
                app_state['db_connected'] = False
                if self.db_file and self.db_file.exists():
                    self.db_file.unlink()

        @service
        @lifecycle
        class Cache:
            def __init__(self, db: Database) -> None:
                self.db = db
                self.cache_file: Path | None = None

            async def initialize(self) -> None:
                app_state['cache_connected'] = True
                # Create cache file
                fd, path = tempfile.mkstemp(suffix='.cache')
                os.close(fd)  # Close file descriptor (required on Windows)
                self.cache_file = Path(path)
                temp_files['cache'] = self.cache_file
                self.cache_file.write_text('cache entries\n')

            async def dispose(self) -> None:
                app_state['cache_connected'] = False
                if self.cache_file and self.cache_file.exists():
                    self.cache_file.unlink()

        @service
        class UserService:
            def __init__(self, db: Database, cache: Cache, email: EmailPort) -> None:
                self.db = db
                self.cache = cache
                self.email = email

            async def process_request(self, user_email: str) -> None:
                """Simulate processing a user request."""
                app_state['requests_processed'] += 1
                await self.email.send(user_email, 'Welcome', 'Hello!')

        container = Container()
        container.scan(profile=Profile.PRODUCTION)

        # Startup phase (like FastAPI startup event)
        await container.start()

        # Verify all resources initialized
        assert app_state['db_connected'], 'Database should be connected'
        assert app_state['cache_connected'], 'Cache should be connected'
        assert app_state['email_initialized'], 'Email service should be initialized'
        assert temp_files['db'].exists(), 'Database file should exist'
        assert temp_files['cache'].exists(), 'Cache file should exist'
        assert temp_files['email'].exists(), 'Email log file should exist'

        # Application running phase (processing requests)
        user_service = container.resolve(UserService)
        await user_service.process_request('alice@example.com')
        await user_service.process_request('bob@example.com')
        assert app_state['requests_processed'] == 2

        # Shutdown phase (like FastAPI shutdown event)
        await container.stop()

        # Verify all resources released
        assert not app_state['db_connected'], 'Database should be disconnected'
        assert not app_state['cache_connected'], 'Cache should be disconnected'
        assert not app_state['email_initialized'], 'Email service should be disposed'

        # Verify all temp files cleaned up (THIS IS THE BUG)
        assert not temp_files['db'].exists(), 'Database file should be cleaned up'
        assert not temp_files['cache'].exists(), 'Cache file should be cleaned up (BUG: likely still exists)'
        assert not temp_files['email'].exists(), 'Email log file should be cleaned up (BUG: likely still exists)'

    @pytest.mark.asyncio
    async def it_prevents_resource_leaks_across_test_suite(self) -> None:
        """Prevents resource leaks when container is created/destroyed per test.

        This simulates a test suite where each test creates a new container,
        starts it, runs tests, and stops it. Resources must be properly cleaned
        up between tests.
        """
        all_temp_files: list[Path] = []

        def create_lifecycle_service() -> type:
            """Factory to create a new service class (simulates test isolation)."""

            @service
            @lifecycle
            class TestResource:
                def __init__(self) -> None:
                    self.temp_file: Path | None = None

                async def initialize(self) -> None:
                    fd, path = tempfile.mkstemp(suffix='.test-resource')
                    os.close(fd)  # Close file descriptor (required on Windows)
                    self.temp_file = Path(path)
                    all_temp_files.append(self.temp_file)
                    self.temp_file.write_text('test data')

                async def dispose(self) -> None:
                    if self.temp_file and self.temp_file.exists():
                        self.temp_file.unlink()

            return TestResource

        # Simulate 3 test runs
        for test_num in range(1, 4):
            # Each test creates a new container
            container = Container()

            # Register service (simulates test setup)
            create_lifecycle_service()
            container.scan()

            # Test execution
            await container.start()

            # Verify resource created
            current_file = all_temp_files[-1]
            assert current_file.exists(), f'Test {test_num}: Resource should exist during test'

            # Test cleanup
            await container.stop()

            # Verify resource cleaned up (THIS IS THE BUG)
            assert not current_file.exists(), (
                f'Test {test_num}: Resource should be cleaned up after test. '
                f'Resource leaks can cause test failures and fill up disk space.'
            )

        # Verify no leaked files
        leaked_files = [f for f in all_temp_files if f.exists()]
        assert len(leaked_files) == 0, (
            f'{len(leaked_files)} files leaked: {leaked_files}. This indicates stop() is not disposing all components.'
        )

    @pytest.mark.asyncio
    async def it_handles_resource_cleanup_with_dispose_errors(self) -> None:
        """Continues cleanup even when some dispose() methods raise exceptions.

        This tests that if one component's dispose() fails, other components
        still get disposed (and their resources cleaned up).
        """
        temp_files: dict[str, Path] = {}

        @service
        @lifecycle
        class GoodResource1:
            def __init__(self) -> None:
                self.temp_file: Path | None = None

            async def initialize(self) -> None:
                fd, path = tempfile.mkstemp(suffix='.good1')
                os.close(fd)  # Close file descriptor (required on Windows)
                self.temp_file = Path(path)
                temp_files['good1'] = self.temp_file
                self.temp_file.write_text('good1 data')

            async def dispose(self) -> None:
                if self.temp_file and self.temp_file.exists():
                    self.temp_file.unlink()

        @service
        @lifecycle
        class FailingResource:
            def __init__(self, r1: GoodResource1) -> None:
                self.r1 = r1
                self.temp_file: Path | None = None

            async def initialize(self) -> None:
                fd, path = tempfile.mkstemp(suffix='.failing')
                os.close(fd)  # Close file descriptor (required on Windows)
                self.temp_file = Path(path)
                temp_files['failing'] = self.temp_file
                self.temp_file.write_text('failing data')

            async def dispose(self) -> None:
                # Fail to clean up AND raise exception
                raise RuntimeError('Dispose failed!')

        @service
        @lifecycle
        class GoodResource2:
            def __init__(self, r1: GoodResource1, failing: FailingResource) -> None:
                self.r1 = r1
                self.failing = failing
                self.temp_file: Path | None = None

            async def initialize(self) -> None:
                fd, path = tempfile.mkstemp(suffix='.good2')
                os.close(fd)  # Close file descriptor (required on Windows)
                self.temp_file = Path(path)
                temp_files['good2'] = self.temp_file
                self.temp_file.write_text('good2 data')

            async def dispose(self) -> None:
                if self.temp_file and self.temp_file.exists():
                    self.temp_file.unlink()

        container = Container()
        container.scan()

        await container.start()

        # All files should exist
        assert temp_files['good1'].exists()
        assert temp_files['failing'].exists()
        assert temp_files['good2'].exists()

        # Stop should not raise (swallows dispose errors)
        await container.stop()

        # Good resources should be cleaned up even though FailingResource raised
        assert not temp_files['good1'].exists(), 'GoodResource1 should be cleaned up despite FailingResource error'
        assert not temp_files['good2'].exists(), 'GoodResource2 should be cleaned up despite FailingResource error'

        # FailingResource file will still exist (it didn't clean up before raising)
        # But this is acceptable - the point is OTHER resources were cleaned up
