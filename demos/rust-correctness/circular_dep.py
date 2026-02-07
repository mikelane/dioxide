"""Demo: dioxide catches circular dependencies at startup."""

from __future__ import annotations

from dioxide import Container, lifecycle, service


@service
@lifecycle
class AuthService:
    def __init__(self, users: UserService):
        self.users = users

    async def initialize(self) -> None:
        pass

    async def dispose(self) -> None:
        pass


@service
@lifecycle
class UserService:
    def __init__(self, auth: AuthService):
        self.auth = auth

    async def initialize(self) -> None:
        pass

    async def dispose(self) -> None:
        pass


# A depends on B, B depends on A.
# dioxide's Rust graph validation catches this cycle:

container = Container()
container.scan()

print("Resolving AuthService...")
auth = container.resolve(AuthService)
