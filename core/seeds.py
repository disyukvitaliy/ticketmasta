import os
from datetime import UTC, datetime, timedelta

from sqlalchemy import create_engine, text

engine = create_engine(os.environ["CORE_DB_DSN"])

with engine.begin() as connection:
    connection.execute(
        text(
            "TRUNCATE ticket_holds, ticket_types, events, venues "
            "RESTART IDENTITY CASCADE"
        )
    )

    venue_ids = []

    for number in range(1, 51):
        venue_id = connection.execute(
            text("INSERT INTO venues (name) VALUES (:name) RETURNING id"),
            {"name": f"Venue {number:03}"},
        ).scalar_one()
        venue_ids.append(venue_id)

    connection.execute(
        text(
            "INSERT INTO events (name, venue_id, starts_at) "
            "VALUES (:name, :venue_id, :starts_at)"
        ),
        [
            {
                "name": f"Event {number:03}",
                "venue_id": venue_ids[(number - 1) % len(venue_ids)],
                "starts_at": datetime(2026, 1, 1, tzinfo=UTC) + timedelta(days=number),
            }
            for number in range(1, 501)
        ],
    )

    connection.execute(
        text(
            "INSERT INTO ticket_types (event_id, name, price_cents, quantity) "
            "SELECT events.id, ticket_types.name, ticket_types.price_cents, "
            "ticket_types.quantity "
            "FROM events CROSS JOIN "
            "(VALUES "
            "('General admission', 3500, 100), "
            "('VIP', 9000, 25), "
            "('Premium', 15000, 10)"
            ") AS ticket_types(name, price_cents, quantity)"
        )
    )

print("Created 50 venues, 500 events, and 1,500 ticket types.")
