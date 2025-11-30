"""FastAPI application with dioxide dependency injection.

This module demonstrates how to integrate dioxide's hexagonal architecture
with FastAPI using the dioxide.fastapi integration module.

Key patterns demonstrated:
- Single middleware setup with DioxideMiddleware
- Automatic request scoping per HTTP request
- Clean injection with Inject() helper
- Profile-based adapter selection via environment variable
- Clean separation of domain logic from HTTP concerns
"""

import os

from dioxide import Profile
from dioxide.fastapi import DioxideMiddleware, Inject
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from .domain.services import UserService

# Get profile from environment, default to 'development'
profile_name = os.getenv("PROFILE", "development")
profile = Profile(profile_name)

print(f"\n{'=' * 60}")
print("dioxide FastAPI Example")
print(f"{'=' * 60}")
print(f"Profile: {profile.value}")
print(f"{'=' * 60}\n")

# Create FastAPI app
app = FastAPI(
    title="dioxide FastAPI Example",
    description="Hexagonal architecture with profile-based dependency injection",
    version="1.0.0",
)

# Single middleware handles both lifecycle and request scoping:
# - Scans for components in the 'app' package at startup
# - Starts/stops container with FastAPI lifespan
# - Creates ScopedContainer per HTTP request
app.add_middleware(DioxideMiddleware, profile=profile, packages=["app"])


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
    service: UserService = Inject(UserService),
) -> UserResponse:
    """Create a new user.

    This endpoint demonstrates:
    - Dependency injection via Inject(UserService)
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
    service: UserService = Inject(UserService),
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
    service: UserService = Inject(UserService),
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
