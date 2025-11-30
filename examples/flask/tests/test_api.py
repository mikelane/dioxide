"""API tests for Flask + dioxide example.

These tests demonstrate dioxide's testing philosophy:
- Use FAKES, not mocks
- Test through the public API (HTTP endpoints)
- Verify state in fakes, not implementation details
- Fast, deterministic, no I/O
"""


class DescribeUserCreation:
    """Tests for user creation endpoint."""

    def it_creates_a_user_and_sends_welcome_email(self, client, db, email):
        """POST /users creates user and sends welcome email."""
        response = client.post(
            "/users",
            json={"name": "Alice Smith", "email": "alice@example.com"},
        )

        # Verify HTTP response
        assert response.status_code == 201
        data = response.get_json()
        assert data["name"] == "Alice Smith"
        assert data["email"] == "alice@example.com"
        assert "id" in data

        # Verify database state (using fake)
        assert len(db.users) == 1
        user = db.users[data["id"]]
        assert user["name"] == "Alice Smith"

        # Verify email was "sent" (using fake)
        assert len(email.sent_emails) == 1
        assert email.was_welcome_email_sent_to("alice@example.com")

    def it_assigns_sequential_ids(self, client, db, email):
        """Multiple user creations get sequential IDs."""
        response1 = client.post(
            "/users",
            json={"name": "User One", "email": "one@example.com"},
        )
        response2 = client.post(
            "/users",
            json={"name": "User Two", "email": "two@example.com"},
        )

        assert response1.get_json()["id"] == "1"
        assert response2.get_json()["id"] == "2"


class DescribeUserRetrieval:
    """Tests for user retrieval endpoints."""

    def it_gets_user_by_id(self, client, db, email):
        """GET /users/<id> returns the user."""
        # Create a user first
        create_response = client.post(
            "/users",
            json={"name": "Bob Jones", "email": "bob@example.com"},
        )
        user_id = create_response.get_json()["id"]

        # Retrieve the user
        response = client.get(f"/users/{user_id}")

        assert response.status_code == 200
        data = response.get_json()
        assert data["name"] == "Bob Jones"
        assert data["email"] == "bob@example.com"

    def it_returns_404_for_nonexistent_user(self, client, db, email):
        """GET /users/<id> returns 404 for unknown ID."""
        response = client.get("/users/999")

        assert response.status_code == 404
        assert "not found" in response.get_json()["error"]

    def it_lists_all_users(self, client, db, email):
        """GET /users returns all users."""
        # Create some users
        client.post("/users", json={"name": "User 1", "email": "user1@example.com"})
        client.post("/users", json={"name": "User 2", "email": "user2@example.com"})

        # List all users
        response = client.get("/users")

        assert response.status_code == 200
        users = response.get_json()
        assert len(users) == 2
        names = [u["name"] for u in users]
        assert "User 1" in names
        assert "User 2" in names


class DescribeHealthCheck:
    """Tests for health check endpoint."""

    def it_returns_healthy_status(self, client):
        """GET /health returns healthy status and profile."""
        response = client.get("/health")

        assert response.status_code == 200
        data = response.get_json()
        assert data["status"] == "healthy"
        assert data["profile"] == "test"
