import logging
import os
from datetime import datetime, timedelta
from time import perf_counter
from uuid import uuid4

import dramatiq
from flask import Flask, g, has_request_context, make_response, request
from sqlalchemy import func, select, update
from sqlalchemy.orm import Session

from app_logging import configure_logging
from db import create_primary_engine, create_replica_engine
from models import Event, TicketHold, TicketHoldStatus, TicketType, Venue
from tasks import broker, send_ticket_email


class RequestContextFilter(logging.Filter):
    def filter(self, record):
        request_id = g.get("request_id") if has_request_context() else None

        if request_id:
            record.fields["request_id"] = request_id

        return True


configure_logging(RequestContextFilter())

logger = logging.getLogger(__name__)


class EnqueueLoggingMiddleware(dramatiq.Middleware):
    def after_enqueue(self, broker, message, delay=None):
        logger.info(
            "Job enqueued",
            extra={"fields": {"actor": message.actor_name}},
        )


broker.add_middleware(EnqueueLoggingMiddleware())

if os.environ.get("CORE_ENV") == "development":
    logging.getLogger("werkzeug").setLevel(logging.WARNING)


def create_app(primary_engine, replica_engine):
    app = Flask(__name__)

    @app.before_request
    def set_current_user():
        g.user_id = request.headers.get("X-User-Id", type=int)

    @app.before_request
    def log_request_start():
        value = request.headers.get("X-Request-ID") or str(uuid4())

        g.request_id = value
        g.request_started_at = perf_counter()

        logger.info(
            "Request started",
            extra={
                "fields": {
                    "method": request.method,
                    "path": request.path,
                }
            },
        )

    @app.after_request
    def log_request_end(response):
        response.headers["X-Request-ID"] = g.request_id
        duration_ms = (perf_counter() - g.request_started_at) * 1000

        logger.info(
            "Request finished",
            extra={
                "fields": {
                    "method": request.method,
                    "path": request.path,
                    "status": response.status_code,
                    "duration_ms": round(duration_ms, 2),
                }
            },
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
                    user_id=g.user_id,
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

    @app.route("/ticket-holds/<int:ticket_hold_id>", methods=["DELETE"])
    def cancel_ticket_hold(ticket_hold_id):
        with Session(primary_engine) as session:
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

    @app.route("/ticket-holds/<int:ticket_hold_id>/complete", methods=["POST"])
    def complete_ticket_hold(ticket_hold_id):
        with Session(primary_engine) as session:
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

    @app.shell_context_processor
    def make_shell_context():
        from pprint import pprint

        return {
            "Event": Event,
            "TicketHold": TicketHold,
            "TicketHoldStatus": TicketHoldStatus,
            "TicketType": TicketType,
            "Venue": Venue,
            "Session": Session,
            "primary_engine": primary_engine,
            "select": select,
            "logger": logger,
            "pp": pprint,
        }

    return app


app = create_app(
    create_primary_engine(),
    create_replica_engine(),
)
