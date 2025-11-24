"""Tests for FastAPI example application.

These tests demonstrate dioxide's hexagonal architecture in action:
- Fast tests using in-memory fakes (no database, no email service)
- Tests verify behavior through the public API
- Tests can also inspect fake state for verification
- No mocking frameworks needed
"""

from fastapi.testclient import TestClient

from app.domain.ports import DatabasePort, EmailPort


class DescribeUserCreation:
    """Tests for POST /users endpoint."""

    def it_creates_a_user_and_sends_welcome_email(
        self, client: TestClient, db: DatabasePort, email: EmailPort
    ) -> None:
        """POST /users creates user and sends welcome email."""
        # Make request
        response = client.post(
            "/users", json={"name": "Alice Smith", "email": "alice@example.com"}
        )

        # Verify HTTP response
        assert response.status_code == 201
        user = response.json()
        assert user["name"] == "Alice Smith"
        assert user["email"] == "alice@example.com"
        assert "id" in user

        # Verify user was stored (checking fake state)
        stored_user = db.users.get(user["id"])
        assert stored_user is not None
        assert stored_user["name"] == "Alice Smith"

        # Verify welcome email was sent (checking fake state)
        assert len(email.sent_emails) == 1
        sent = email.sent_emails[0]
        assert sent["to"] == "alice@example.com"
        assert sent["name"] == "Alice Smith"
        assert sent["type"] == "welcome"

    def it_assigns_unique_ids_to_users(self, client: TestClient) -> None:
        """Each user gets a unique ID."""
        response1 = client.post(
            "/users", json={"name": "Alice", "email": "alice@example.com"}
        )
        response2 = client.post(
            "/users", json={"name": "Bob", "email": "bob@example.com"}
        )

        user1 = response1.json()
        user2 = response2.json()

        assert user1["id"] != user2["id"]

    def it_sends_email_for_each_user(
        self, client: TestClient, email: EmailPort
    ) -> None:
        """Each user creation sends a welcome email."""
        client.post("/users", json={"name": "Alice", "email": "alice@example.com"})
        client.post("/users", json={"name": "Bob", "email": "bob@example.com"})

        assert len(email.sent_emails) == 2
        assert email.sent_emails[0]["to"] == "alice@example.com"
        assert email.sent_emails[1]["to"] == "bob@example.com"


class DescribeUserRetrieval:
    """Tests for GET /users/{user_id} endpoint."""

    def it_retrieves_an_existing_user(
        self, client: TestClient, db: DatabasePort
    ) -> None:
        """GET /users/{id} returns user data."""
        # Create user first
        create_response = client.post(
            "/users", json={"name": "Alice", "email": "alice@example.com"}
        )
        user_id = create_response.json()["id"]

        # Retrieve user
        response = client.get(f"/users/{user_id}")

        assert response.status_code == 200
        user = response.json()
        assert user["id"] == user_id
        assert user["name"] == "Alice"
        assert user["email"] == "alice@example.com"

    def it_returns_404_for_nonexistent_user(self, client: TestClient) -> None:
        """GET /users/{id} returns 404 for unknown ID."""
        response = client.get("/users/999")

        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()


class DescribeUserListing:
    """Tests for GET /users endpoint."""

    def it_returns_empty_list_when_no_users(self, client: TestClient) -> None:
        """GET /users returns empty list initially."""
        response = client.get("/users")

        assert response.status_code == 200
        assert response.json() == []

    def it_returns_all_users(self, client: TestClient) -> None:
        """GET /users returns all created users."""
        # Create multiple users
        client.post("/users", json={"name": "Alice", "email": "alice@example.com"})
        client.post("/users", json={"name": "Bob", "email": "bob@example.com"})
        client.post("/users", json={"name": "Carol", "email": "carol@example.com"})

        # List all users
        response = client.get("/users")

        assert response.status_code == 200
        users = response.json()
        assert len(users) == 3

        names = {user["name"] for user in users}
        assert names == {"Alice", "Bob", "Carol"}


class DescribeHealthCheck:
    """Tests for GET /health endpoint."""

    def it_returns_healthy_status(self, client: TestClient) -> None:
        """GET /health returns healthy status."""
        response = client.get("/health")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["profile"] == "test"


class DescribeHexagonalArchitecture:
    """Tests demonstrating hexagonal architecture benefits."""

    def it_uses_fake_adapters_in_test_profile(
        self, db: DatabasePort, email: EmailPort
    ) -> None:
        """Container resolves to fake adapters in TEST profile."""
        # Verify we're using fakes by checking for fake-specific attributes
        assert hasattr(db, "users")  # FakeDatabaseAdapter has users dict
        assert hasattr(email, "sent_emails")  # FakeEmailAdapter has sent_emails list

    def it_allows_direct_fake_inspection(
        self, client: TestClient, db: DatabasePort, email: EmailPort
    ) -> None:
        """Tests can inspect fake state directly for verification."""
        # Create user via API
        response = client.post(
            "/users", json={"name": "Alice", "email": "alice@example.com"}
        )
        user_id = response.json()["id"]

        # Verify via API
        get_response = client.get(f"/users/{user_id}")
        assert get_response.status_code == 200

        # ALSO verify by inspecting fake directly
        assert user_id in db.users
        assert len(email.sent_emails) == 1

        # This dual verification demonstrates:
        # 1. API works correctly (HTTP response)
        # 2. Adapters behave correctly (fake state)


class DescribeTestSpeed:
    """Tests demonstrating fast test execution."""

    def it_runs_fast_with_no_io(self, client: TestClient) -> None:
        """Tests run fast because fakes do no I/O."""
        # Create 10 users - should be nearly instant
        for i in range(10):
            response = client.post(
                "/users",
                json={"name": f"User {i}", "email": f"user{i}@example.com"},
            )
            assert response.status_code == 201

        # List all users - also instant
        response = client.get("/users")
        assert response.status_code == 200
        assert len(response.json()) == 10

        # This would be slow with real database/email service
        # But fakes make it instantaneous


class DescribeFakeConvenience:
    """Tests demonstrating fake convenience methods."""

    def it_uses_fake_helper_methods(self, client: TestClient, email: EmailPort) -> None:
        """Fakes can provide convenient test helper methods."""
        # Create user
        client.post("/users", json={"name": "Alice", "email": "alice@example.com"})

        # Use fake's convenience method
        assert email.was_welcome_email_sent_to("alice@example.com")
        assert not email.was_welcome_email_sent_to("bob@example.com")

        # This is cleaner than:
        # assert any(e["to"] == "alice@example.com" for e in email.sent_emails)
