from datetime import datetime, timedelta
from unittest.mock import patch

from tests.factories import EventFactory, TicketHoldFactory, TicketTypeFactory
from ticketing.models import TicketHold, TicketHoldStatus

USER_HEADERS = {"X-User-Id": "1"}


def test_list_ticket_types_returns_event_ticket_types(client):
    event = EventFactory()
    ticket_type = TicketTypeFactory(
        event_id=event.id,
        name="General Admission",
        price_cents=1_500,
        quantity=10,
    )

    response = client.get(f"/events/{event.id}/ticket-types")

    assert response.status_code == 200
    assert response.json == [
        {
            "id": ticket_type.id,
            "name": "General Admission",
            "price_cents": 1_500,
            "quantity": 10,
        }
    ]


def test_get_ticket_type_returns_ticket_type(client):
    ticket_type = TicketTypeFactory(name="General Admission")

    response = client.get(f"/ticket-types/{ticket_type.id}")

    assert response.status_code == 200
    assert response.json == {
        "id": ticket_type.id,
        "event_id": ticket_type.event_id,
        "name": "General Admission",
        "price_cents": 1_000,
        "quantity": 3,
    }


def test_create_ticket_hold_reserves_ticket_inventory(client, session):
    ticket_type = TicketTypeFactory(quantity=3)

    response = client.post(
        f"/ticket-types/{ticket_type.id}/holds",
        data={"quantity": 2},
        headers=USER_HEADERS,
    )

    assert response.status_code == 200

    ticket_hold = session.get(TicketHold, response.json["id"])
    session.refresh(ticket_type)

    assert ticket_hold.ticket_type_id == ticket_type.id
    assert ticket_hold.user_id == 1
    assert ticket_hold.quantity == 2
    assert ticket_hold.status == TicketHoldStatus.ACTIVE
    assert ticket_type.quantity == 1


def test_get_ticket_hold_returns_current_users_hold(client):
    ticket_hold = TicketHoldFactory(user_id=1, quantity=2)

    response = client.get(f"/ticket-holds/{ticket_hold.id}", headers=USER_HEADERS)

    assert response.status_code == 200
    assert response.json["id"] == ticket_hold.id
    assert response.json["ticket_type_id"] == ticket_hold.ticket_type_id
    assert response.json["quantity"] == 2
    assert response.json["status"] == "active"


def test_get_ticket_hold_hides_another_users_hold(client):
    ticket_hold = TicketHoldFactory(user_id=2)

    response = client.get(f"/ticket-holds/{ticket_hold.id}", headers=USER_HEADERS)

    assert response.status_code == 404
    assert response.json == {"error": "Not found"}


def test_cancel_ticket_hold_releases_ticket_inventory(client, session):
    ticket_type = TicketTypeFactory(quantity=2)
    ticket_hold = TicketHoldFactory(
        ticket_type_id=ticket_type.id, user_id=1, quantity=1
    )

    response = client.delete(f"/ticket-holds/{ticket_hold.id}", headers=USER_HEADERS)

    assert response.status_code == 200
    assert response.json == {}

    session.refresh(ticket_hold)
    session.refresh(ticket_type)

    assert ticket_hold.status == TicketHoldStatus.CANCELED
    assert ticket_type.quantity == 3


def test_complete_ticket_hold_enqueues_ticket_email(client, session):
    event = EventFactory(name="Concert")
    ticket_type = TicketTypeFactory(event_id=event.id, name="General Admission")
    ticket_hold = TicketHoldFactory(
        ticket_type_id=ticket_type.id, user_id=1, quantity=2
    )

    with patch("ticketing.routes.send_ticket_email.send") as send:
        response = client.post(
            f"/ticket-holds/{ticket_hold.id}/complete",
            headers={**USER_HEADERS, "X-User-Email": "test@example.com"},
        )

    assert response.status_code == 200
    assert response.json == {"id": ticket_hold.id}
    send.assert_called_once_with(ticket_type.id, "test@example.com", 2)

    session.refresh(ticket_hold)

    assert ticket_hold.status == TicketHoldStatus.COMPLETED


def test_complete_ticket_hold_rejects_expired_hold(client, session):
    ticket_hold = TicketHoldFactory(
        user_id=1,
        expires_at=datetime.now() - timedelta(minutes=1),
    )

    response = client.post(
        f"/ticket-holds/{ticket_hold.id}/complete",
        headers=USER_HEADERS,
    )

    assert response.status_code == 400
    assert response.json == {"error": "Hold is unavailable"}

    session.refresh(ticket_hold)

    assert ticket_hold.status == TicketHoldStatus.ACTIVE
