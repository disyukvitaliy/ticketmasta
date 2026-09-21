from datetime import datetime, timedelta

from flask import Blueprint, g, request
from sqlalchemy import func, select, update

from db import PrimarySession, ReplicaSession
from events.models import Event
from tasks import send_ticket_email
from ticketing.models import TicketHold, TicketHoldStatus, TicketType

bp = Blueprint("ticketing", __name__)


@bp.get("/events/<int:event_id>/ticket-types")
def list_ticket_types(event_id):
    with ReplicaSession() as session:
        ticket_types = session.scalars(
            select(TicketType).where(TicketType.event_id == event_id)
        ).all()

    return [
        {
            "id": ticket_type.id,
            "name": ticket_type.name,
            "price_cents": ticket_type.price_cents,
            "quantity": ticket_type.quantity,
        }
        for ticket_type in ticket_types
    ]


@bp.get("/ticket-types/<int:ticket_type_id>")
def get_ticket_type(ticket_type_id):
    with PrimarySession() as session:
        ticket_type = session.get(TicketType, ticket_type_id)

        if ticket_type is None:
            return {"error": "Not found"}, 404

        return {
            "id": ticket_type.id,
            "event_id": ticket_type.event_id,
            "name": ticket_type.name,
            "price_cents": ticket_type.price_cents,
            "quantity": ticket_type.quantity,
        }


@bp.post("/ticket-types/<int:ticket_type_id>/holds")
def create_ticket_hold(ticket_type_id):
    quantity = request.form.get("quantity", type=int)

    if quantity is None:
        return {"error": "Quantity is required"}, 400

    with PrimarySession() as session:
        with session.begin():
            ticket_type = session.scalars(
                select(TicketType)
                .where(TicketType.id == ticket_type_id)
                .with_for_update()
            ).one()

            if ticket_type.quantity >= quantity:
                ticket_type.quantity = ticket_type.quantity - quantity
            else:
                return {"error": "Not enough tickets available"}, 400

            ticket_hold = TicketHold(
                ticket_type_id=ticket_type_id,
                user_id=g.user_id,
                quantity=quantity,
                expires_at=datetime.now() + timedelta(minutes=15),
            )
            session.add(ticket_hold)

        return {"id": ticket_hold.id}


@bp.get("/ticket-holds/<int:ticket_hold_id>")
def get_ticket_hold(ticket_hold_id):
    with PrimarySession() as session:
        ticket_hold = session.scalars(
            select(TicketHold).where(
                TicketHold.id == ticket_hold_id,
                TicketHold.user_id == g.user_id,
            )
        ).one_or_none()

        if ticket_hold is None:
            return {"error": "Not found"}, 404

        return {
            "id": ticket_hold.id,
            "ticket_type_id": ticket_hold.ticket_type_id,
            "status": ticket_hold.status,
            "quantity": ticket_hold.quantity,
            "expires_at": ticket_hold.expires_at,
        }


@bp.delete("/ticket-holds/<int:ticket_hold_id>")
def cancel_ticket_hold(ticket_hold_id):
    with PrimarySession() as session:
        ticket_hold = session.get(TicketHold, ticket_hold_id, with_for_update=True)
        if ticket_hold is None or ticket_hold.user_id != g.user_id:
            return {"error": "Not found"}, 404
        if ticket_hold.status != TicketHoldStatus.ACTIVE:
            return {"error": "Cannot cancel"}, 400

        ticket_hold.status = TicketHoldStatus.CANCELED

        session.execute(
            update(TicketType)
            .where(TicketType.id == ticket_hold.ticket_type_id)
            .values(quantity=TicketType.quantity + ticket_hold.quantity)
        )

        session.commit()

    return {}, 200


@bp.post("/ticket-holds/<int:ticket_hold_id>/complete")
def complete_ticket_hold(ticket_hold_id):
    with PrimarySession() as session:
        completed_hold = session.execute(
            update(TicketHold)
            .where(
                TicketHold.id == ticket_hold_id,
                TicketHold.user_id == g.user_id,
                TicketHold.status == TicketHoldStatus.ACTIVE,
                TicketHold.expires_at > func.now(),
            )
            .values(status=TicketHoldStatus.COMPLETED)
            .returning(
                TicketHold.id,
                TicketHold.ticket_type_id,
                TicketHold.quantity,
            )
        ).one_or_none()

        if completed_hold is None:
            return {"error": "Hold is unavailable"}, 400

        hold_id, ticket_type_id, quantity = completed_hold
        session.commit()

    with ReplicaSession() as session:
        ticket_type_name, event_name = session.execute(
            select(TicketType.name, Event.name)
            .join(Event)
            .where(TicketType.id == ticket_type_id)
        ).one()

    send_ticket_email.send(
        request.headers["X-User-Email"],
        event_name,
        ticket_type_name,
        quantity,
    )

    return {"id": hold_id}
