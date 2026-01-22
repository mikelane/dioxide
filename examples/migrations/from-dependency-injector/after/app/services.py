"""Business logic services using dioxide @service decorator.

The @service decorator replaces dependency-injector's provider wiring.
Dependencies are resolved automatically from type hints.
"""

from dioxide import service

from app.ports import CachePort, EmailPort, UserRepositoryPort


@service
class UserService:
    """User management service.

    With dioxide, the @service decorator marks this as injectable.
    Dependencies are inferred from the constructor's type hints.

    No @inject decorator needed - just use type hints.
    """

    def __init__(
        self,
        repository: UserRepositoryPort,
        email: EmailPort,
        cache: CachePort,
    ) -> None:
        self._repository = repository
        self._email = email
        self._cache = cache

    async def get_user(self, user_id: str) -> dict | None:
        """Get a user, checking cache first."""
        cached = await self._cache.get(f"user:{user_id}")
        if cached:
            import json

            return json.loads(cached)

        user = await self._repository.get(user_id)
        if user:
            import json

            await self._cache.set(f"user:{user_id}", json.dumps(user))
        return user

    async def create_user(self, name: str, email: str) -> dict:
        """Create a new user and send welcome email."""
        user = await self._repository.save({"name": name, "email": email})
        await self._email.send(
            to=email,
            subject="Welcome!",
            body=f"Hello {name}, welcome to our platform!",
        )
        return user

    async def delete_user(self, user_id: str) -> bool:
        """Delete a user and invalidate cache."""
        result = await self._repository.delete(user_id)
        if result:
            await self._cache.delete(f"user:{user_id}")
        return result
