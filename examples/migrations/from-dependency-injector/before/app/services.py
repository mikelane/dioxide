"""Business logic services using dependency-injector patterns."""

from app.ports import CacheService, EmailService, UserRepository


class UserService:
    """User management service.

    In dependency-injector, services receive dependencies via constructor.
    The container wires these using providers.
    """

    def __init__(
        self,
        repository: UserRepository,
        email: EmailService,
        cache: CacheService,
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
