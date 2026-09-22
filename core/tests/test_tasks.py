from unittest.mock import patch

from tasks import send_ticket_email


def test_send_ticket_email():
    with patch("mailer.send") as send:
        send_ticket_email("test@example.com", "Test Event", "General Admission", 2)

        send.assert_called_once_with(
            "test@example.com",
            "Your tickets",
            "You bought 2 General Admission ticket(s) for Test Event.",
        )
