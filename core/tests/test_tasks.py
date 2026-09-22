from unittest.mock import patch

from tasks import send_ticket_email
from tests.factories import EventFactory, TicketTypeFactory


def test_send_ticket_email():
    event = EventFactory(name="Test Event")
    ticket_type = TicketTypeFactory(
        event_id=event.id,
        name="General Admission",
    )

    with patch("mailer.send") as send:
        send_ticket_email(ticket_type.id, "test@example.com", 2)

        send.assert_called_once_with(
            "test@example.com",
            "Your tickets",
            f"You bought 2 {ticket_type.name} ticket(s) for {event.name}.",
        )
