import logging
import os
from datetime import datetime, timedelta
from time import perf_counter
from uuid import uuid4

from flask import Flask, g, make_response, request
from sqlalchemy import DateTime, ForeignKey, String, create_engine, func, select, update
from sqlalchemy.orm import DeclarativeBase, Mapped, Session, mapped_column

from app_logging import configure_logging
from tasks import send_ticket_email


class Base(DeclarativeBase):
    pass


class Venue(Base):
    __tablename__ = "venues"
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(255))


class Event(Base):
    __tablename__ = "events"
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(255))
    starts_at: Mapped[datetime] = mapped_column(DateTime())
    venue_id: Mapped[int] = mapped_column(ForeignKey("venues.id"))


class TicketType(Base):
    __tablename__ = "ticket_types"
    id: Mapped[int] = mapped_column(primary_key=True)
    event_id: Mapped[int] = mapped_column(ForeignKey("events.id"))
    name: Mapped[str] = mapped_column(String(255))
    price_cents: Mapped[int] = mapped_column()
    quantity: Mapped[int] = mapped_column()


class TicketHold(Base):
    __tablename__ = "ticket_holds"
    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(nullable=False)
    ticket_type_id: Mapped[int] = mapped_column(
        ForeignKey("ticket_types.id"), nullable=False
    )
    quantity: Mapped[int] = mapped_column(nullable=False)
    status: Mapped[str] = mapped_column(String(255), nullable=False)
    expires_at: Mapped[datetime] = mapped_column(DateTime(), nullable=False)


configure_logging()

logger = logging.getLogger(__name__)
app = Flask(__name__)

logging.getLogger("sqlalchemy.engine").setLevel(logging.INFO)
primary_engine = create_engine(os.environ["CORE_DB_DSN"], logging_name="primary")
replica_engine = create_engine(os.environ["CORE_READ_DB_DSN"], logging_name="replica")


if os.environ.get("CORE_ENV") == "development":
    logging.getLogger("werkzeug").setLevel(logging.WARNING)


@app.before_request
def log_request_start():
    value = request.headers.get("X-Request-ID") or str(uuid4())

    g.request_id = value
    g.request_started_at = perf_counter()

    logger.info(
        "Request started: %s %s",
        request.method,
        request.path,
    )


@app.after_request
def log_request_end(response):
    response.headers["X-Request-ID"] = g.request_id
    duration_ms = (perf_counter() - g.request_started_at) * 1000
    logger.info(
        "Request finished: %s %s status=%s duration_ms=%.2f",
        request.method,
        request.path,
        response.status_code,
        duration_ms,
    )

    return response


@app.route("/profile")
def profile():
    headers_to_include = [
        "X-User-Id",
        "X-User-Email",
        "X-User-Role",
    ]  # Adjust headers as needed
    headers_text = "\n".join(
        f"{header}: {request.headers.get(header, 'Not Provided')}"
        for header in headers_to_include
    )

    response = make_response(headers_text)
    response.mimetype = "text/plain"
    return response, 200


@app.route("/venues")
def list_venues():
    page = request.args.get("page", default=1, type=int)
    with Session(replica_engine) as session:
        select_stmt = (
            select(Venue).order_by(Venue.name).offset((page - 1) * 10).limit(10)
        )
        venues = session.scalars(select_stmt).all()

    return [{"id": venue.id, "name": venue.name} for venue in venues]


@app.route("/venues/<int:venue_id>")
def get_venue(venue_id):
    with Session(replica_engine) as session:
        venue = session.get(Venue, venue_id)

        if venue is None:
            return {"error": "Not found"}, 404

        return {"id": venue.id, "name": venue.name}


@app.route("/events")
@app.route("/venues/<int:venue_id>/events")
def list_events(venue_id=None):
    page = request.args.get("page", default=1, type=int)
    with Session(replica_engine) as session:
        select_stmt = (
            select(Event, Venue)
            .join(Venue)
            .where(Event.starts_at >= datetime.now())
            .order_by(Event.starts_at)
            .offset((page - 1) * 10)
            .limit(10)
        )

        if venue_id:
            select_stmt = select_stmt.where(Venue.id == venue_id)

        events = session.execute(select_stmt).all()

    return [
        {"id": event.id, "name": event.name, "venue": {"name": venue.name}}
        for event, venue in events
    ]


@app.route("/events/<int:event_id>")
def get_event(event_id):
    with Session(replica_engine) as session:
        event = session.get(Event, event_id)

        if event is None:
            return {"error": "Not found"}, 404

        return {"id": event.id, "name": event.name, "venue_id": event.venue_id}


@app.route("/events/<int:event_id>/ticket-types")
def list_ticket_types(event_id):
    with Session(replica_engine) as session:
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


@app.route("/ticket-types/<int:ticket_type_id>")
def get_ticket_type(ticket_type_id):
    with Session(primary_engine) as session:
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


@app.route("/ticket-types/<int:ticket_type_id>/holds", methods=["POST"])
def create_ticket_hold(ticket_type_id):
    quantity = request.form.get("quantity", type=int)

    if quantity is None:
        return {"error": "Quantity is required"}, 400

    with Session(primary_engine) as session:
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
                user_id=request.headers.get("X-User-Id", type=int),
                status="active",
                quantity=quantity,
                expires_at=datetime.now() + timedelta(minutes=15),
            )
            session.add(ticket_hold)

        return {"id": ticket_hold.id}


@app.route("/ticket-holds/<int:ticket_hold_id>")
def get_ticket_hold(ticket_hold_id):
    with Session(primary_engine) as session:
        ticket_hold = session.scalars(
            select(TicketHold).where(
                TicketHold.id == ticket_hold_id,
                TicketHold.user_id == request.headers.get("X-User-Id", type=int),
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


@app.route("/ticket-holds/<int:ticket_hold_id>/complete", methods=["POST"])
def complete_ticket_hold(ticket_hold_id):
    with Session(primary_engine) as session:
        completed_hold = session.execute(
            update(TicketHold)
            .where(
                TicketHold.id == ticket_hold_id,
                TicketHold.user_id == request.headers.get("X-User-Id", type=int),
                TicketHold.status == "active",
                TicketHold.expires_at > func.now(),
            )
            .values(status="completed")
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

    with Session(replica_engine) as session:
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
