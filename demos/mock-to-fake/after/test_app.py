"""Same mock tests from before — now broken after the refactoring."""

from unittest.mock import MagicMock, patch

from app import send_welcome_email


@patch("app.smtplib.SMTP")
def test_sends_welcome_email(mock_smtp):
    mock_server = MagicMock()
    mock_smtp.return_value.__enter__ = MagicMock(return_value=mock_server)
    mock_smtp.return_value.__exit__ = MagicMock(return_value=False)

    send_welcome_email("Alice", "alice@example.com")

    mock_server.starttls.assert_called_once()
    mock_server.login.assert_called_once_with("noreply@example.com", "secret")
    mock_server.send_message.assert_called_once()
