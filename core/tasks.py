import os
from datetime import datetime

import dramatiq
from dramatiq.brokers.redis import RedisBroker
from sqlalchemy import select, text

import mailer
from db import PrimarySession, ReplicaSession
from events.models import Event
from ticketing.models import TicketHoldStatus, TicketType

broker = RedisBroker(url=os.environ["CORE_REDIS_URL"])
dramatiq.set_broker(broker)

EXPIRE_TICKET_HOLDS_BATCH = text("""
    WITH holds_to_expire AS (
        SELECT id
        FROM ticket_holds
        WHERE status = :active_status
          AND expires_at <= :expires_before
        ORDER BY expires_at, id
        LIMIT :batch_size
        FOR UPDATE SKIP LOCKED
    ),
    expired_holds AS (
        UPDATE ticket_holds AS ticket_hold
        SET status = :expired_status
        FROM holds_to_expire
        WHERE ticket_hold.id = holds_to_expire.id
        RETURNING ticket_hold.ticket_type_id, ticket_hold.quantity
    ),
    restored_inventory AS (
        SELECT ticket_type_id, SUM(quantity) AS quantity
        FROM expired_holds
        GROUP BY ticket_type_id
    )
    UPDATE ticket_types AS ticket_type
    SET quantity = ticket_type.quantity + restored_inventory.quantity
    FROM restored_inventory
    WHERE ticket_type.id = restored_inventory.ticket_type_id
    RETURNING ticket_type.id
""")


@dramatiq.actor(queue_name="maintenance")
def expire_ticket_holds():
    expires_before = datetime.now()

    while True:
        with PrimarySession() as session:
            updated_ticket_types = session.scalars(
                EXPIRE_TICKET_HOLDS_BATCH,
                {
                    "active_status": TicketHoldStatus.ACTIVE.value,
                    "expired_status": TicketHoldStatus.EXPIRED.value,
                    "batch_size": 1000,
                    "expires_before": expires_before,
                },
            ).all()
            session.commit()

        if not updated_ticket_types:
            return


@dramatiq.actor(queue_name="email", max_retries=3)
def send_ticket_email(ticket_type_id, recipient, quantity):
    with ReplicaSession() as session:
        ticket_type_name, event_name = session.execute(
            select(TicketType.name, Event.name)
            .join(Event)
            .where(TicketType.id == ticket_type_id)
        ).one()

    mailer.send(
        recipient,
        "Your tickets",
        f"You bought {quantity} {ticket_type_name} ticket(s) for {event_name}.",
    )
