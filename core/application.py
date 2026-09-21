import logging
import os
from time import perf_counter
from uuid import uuid4

import dramatiq
from flask import Flask, g, has_request_context, make_response, request
from sqlalchemy import select

from app_logging import configure_logging
from db import PrimarySession, ReplicaSession
from events.models import Event
from events.routes import bp as events_bp
from tasks import broker
from ticketing.models import TicketHold, TicketHoldStatus, TicketType
from ticketing.routes import bp as ticketing_bp
from venues.models import Venue
from venues.routes import bp as venues_bp


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


def create_app():
    app = Flask(__name__)

    app.register_blueprint(venues_bp)
    app.register_blueprint(events_bp)
    app.register_blueprint(ticketing_bp)

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

    @app.shell_context_processor
    def make_shell_context():
        from pprint import pprint

        return {
            "Event": Event,
            "TicketHold": TicketHold,
            "TicketHoldStatus": TicketHoldStatus,
            "TicketType": TicketType,
            "Venue": Venue,
            "PrimarySession": PrimarySession,
            "ReplicaSession": ReplicaSession,
            "select": select,
            "logger": logger,
            "pp": pprint,
        }

    return app
