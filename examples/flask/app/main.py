"""Flask application with dioxide dependency injection.

This module demonstrates how to integrate dioxide's hexagonal architecture
with Flask using the dioxide.flask integration module.

Key patterns demonstrated:
- Single function setup with configure_dioxide()
- Automatic request scoping per HTTP request
- Clean injection with inject() helper
- Profile-based adapter selection via environment variable
- Clean separation of domain logic from HTTP concerns
"""

import os

from dioxide import Profile
from dioxide.flask import (
    configure_dioxide,
    inject,
)
from flask import (
    Flask,
    jsonify,
    request,
)

from .domain.services import UserService

# Get profile from environment, default to 'development'
profile_name = os.getenv("PROFILE", "development")
profile = Profile(profile_name)

print(f"\n{'=' * 60}")
print("dioxide Flask Example")
print(f"{'=' * 60}")
print(f"Profile: {profile.value}")
print(f"{'=' * 60}\n")

# Create Flask app
app = Flask(__name__)

# Single function handles container setup and request scoping:
# - Scans for components in the 'app' package at startup
# - Starts container (initializes @lifecycle components)
# - Creates ScopedContainer per HTTP request via before_request hook
# - Disposes ScopedContainer after request via teardown_request hook
configure_dioxide(app, profile=profile, packages=["app"])


# API Routes
@app.route("/users", methods=["POST"])
def create_user():
    """Create a new user.

    This endpoint demonstrates:
    - Dependency injection via inject(UserService)
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
    service = inject(UserService)
    data = request.get_json()
    user = service.register_user(data["name"], data["email"])
    return jsonify(user), 201


@app.route("/users/<user_id>", methods=["GET"])
def get_user(user_id: str):
    """Get a user by ID.

    Args:
        user_id: Unique identifier for the user

    Returns:
        User data or 404 if not found

    Example:
        GET /users/1

        Response (200 OK):
        {
            "id": "1",
            "name": "Alice Smith",
            "email": "alice@example.com"
        }
    """
    service = inject(UserService)
    user = service.get_user(user_id)
    if user is None:
        return jsonify({"error": f"User {user_id} not found"}), 404
    return jsonify(user)


@app.route("/users", methods=["GET"])
def list_users():
    """List all users.

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
    service = inject(UserService)
    users = service.list_all_users()
    return jsonify(users)


@app.route("/health", methods=["GET"])
def health_check():
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
    return jsonify({"status": "healthy", "profile": profile.value})
