"""FastAPI application with dioxide dependency injection.

This module demonstrates how to integrate dioxide's hexagonal architecture
with FastAPI's dependency injection and lifecycle management.

Key patterns demonstrated:
- Profile-based adapter selection via environment variable
- Container lifecycle integration with FastAPI lifespan
- FastAPI Depends() integration with dioxide container
- Clean separation of domain logic from HTTP concerns
"""

import os
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from dioxide import Container, Profile
from fastapi import Depends, FastAPI, HTTPException
from pydantic import BaseModel

from .domain.services import UserService

# Create container with profile from environment
# Default to 'development' for local testing
profile_name = os.getenv("PROFILE", "development")
profile = Profile(profile_name)

# Create and scan container
container = Container()
container.scan(package="app", profile=profile)

print(f"\n{'=' * 60}")
print("dioxide FastAPI Example")
print(f"{'=' * 60}")
print(f"Profile: {profile.value}")
print(f"{'=' * 60}\n")


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    """Manage container lifecycle with FastAPI.

    This lifespan context manager ensures that:
    1. All @lifecycle adapters are initialized before accepting requests
    2. All @lifecycle adapters are cleaned up on shutdown

    Example lifecycle flow:
        Startup:  FastAPI starts -> lifespan.__aenter__ -> container.__aenter__
                  -> initialize() called on all @lifecycle adapters
                  -> App ready to accept requests

        Shutdown: SIGTERM received -> container.__aexit__
                  -> dispose() called on all @lifecycle adapters (reverse order)
                  -> FastAPI shuts down

    This pattern ensures clean startup/shutdown of database connections,
    message queues, cache connections, etc.
    """
    print("[Lifespan] Starting application")

    # Enter container context - initializes all @lifecycle adapters
    async with container:
        print("[Lifespan] Container started - all adapters initialized")
        yield
        print("[Lifespan] Shutting down")

    print("[Lifespan] Container stopped - all adapters disposed")


# Create FastAPI app with lifespan
app = FastAPI(
    title="dioxide FastAPI Example",
    description="Hexagonal architecture with profile-based dependency injection",
    version="1.0.0",
    lifespan=lifespan,
)


# Dependency injection helpers
def get_user_service() -> UserService:
    """Resolve UserService from dioxide container.

    This function is used with FastAPI's Depends() to inject the UserService
    into route handlers. The service is resolved from the container, which
    automatically injects the correct adapters based on the active profile.

    Example:
        @app.post("/users")
        async def create_user(service: UserService = Depends(get_user_service)):
            ...
    """
    return container.resolve(UserService)


# Request/Response models
class CreateUserRequest(BaseModel):
    """Request body for creating a user."""

    name: str
    email: str


class UserResponse(BaseModel):
    """Response model for user data."""

    id: str
    name: str
    email: str


# API Routes
@app.post("/users", response_model=UserResponse, status_code=201)
async def create_user(
    request: CreateUserRequest,
    service: UserService = Depends(get_user_service),
) -> UserResponse:
    """Create a new user.

    This endpoint demonstrates:
    - Dependency injection via Depends(get_user_service)
    - Service orchestrates domain logic (create + email)
    - Adapters used are determined by active profile

    In production (PRODUCTION profile):
    - User saved to PostgreSQL
    - Email sent via SendGrid

    In tests (TEST profile):
    - User saved to in-memory fake
    - Email recorded by fake (not sent)

    In development (DEVELOPMENT profile):
    - User saved to in-memory fake
    - Email logged to console

    Args:
        request: User creation request with name and email
        service: UserService injected by dioxide

    Returns:
        Created user data

    Example:
        POST /users
        {
            "name": "Alice Smith",
            "email": "alice@example.com"
        }

        Response (201 Created):
        {
            "id": "1",
            "name": "Alice Smith",
            "email": "alice@example.com"
        }
    """
    user = await service.register_user(request.name, request.email)
    return UserResponse(**user)


@app.get("/users/{user_id}", response_model=UserResponse)
async def get_user(
    user_id: str,
    service: UserService = Depends(get_user_service),
) -> UserResponse:
    """Get a user by ID.

    Args:
        user_id: Unique identifier for the user
        service: UserService injected by dioxide

    Returns:
        User data

    Raises:
        HTTPException: 404 if user not found

    Example:
        GET /users/1

        Response (200 OK):
        {
            "id": "1",
            "name": "Alice Smith",
            "email": "alice@example.com"
        }
    """
    user = await service.get_user(user_id)
    if user is None:
        raise HTTPException(status_code=404, detail=f"User {user_id} not found")
    return UserResponse(**user)


@app.get("/users", response_model=list[UserResponse])
async def list_users(
    service: UserService = Depends(get_user_service),
) -> list[UserResponse]:
    """List all users.

    Args:
        service: UserService injected by dioxide

    Returns:
        List of all users

    Example:
        GET /users

        Response (200 OK):
        [
            {
                "id": "1",
                "name": "Alice Smith",
                "email": "alice@example.com"
            },
            {
                "id": "2",
                "name": "Bob Jones",
                "email": "bob@example.com"
            }
        ]
    """
    users = await service.list_all_users()
    return [UserResponse(**user) for user in users]


@app.get("/health")
async def health_check() -> dict[str, str]:
    """Health check endpoint.

    Returns:
        Health status and active profile

    Example:
        GET /health

        Response (200 OK):
        {
            "status": "healthy",
            "profile": "development"
        }
    """
    return {"status": "healthy", "profile": profile.value}
