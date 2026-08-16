import logging
import os
import smtplib
from contextvars import ContextVar
from email.message import EmailMessage

import dramatiq
from dramatiq.brokers.redis import RedisBroker

from app_logging import configure_logging, job_id

broker = RedisBroker(url=os.environ["CORE_REDIS_URL"])
dramatiq.set_broker(broker)


configure_logging()


logger = logging.getLogger(__name__)

_job_id_token = ContextVar("_job_id_token", default=None)


class LoggingMiddleware(dramatiq.Middleware):
    def before_process_message(self, broker, message):
        token = job_id.set(message.message_id)
        _job_id_token.set(token)

        logger.info(
            "actor=%s Job started",
            message.actor_name,
        )

    def after_process_message(
        self,
        broker,
        message,
        *,
        result=None,
        exception=None,
    ):
        if exception is None:
            logger.info(
                "actor=%s Job finished",
                message.actor_name,
            )

        self._clear_context()

    def after_skip_message(self, broker, message):
        logger.info(
            "actor=%s Job skipped",
            message.actor_name,
        )

        self._clear_context()

    def _clear_context(self):
        token = _job_id_token.get()

        if token is not None:
            job_id.reset(token)
            _job_id_token.set(None)


broker.add_middleware(LoggingMiddleware())


@dramatiq.actor(queue_name="email", max_retries=3)
def send_ticket_email(recipient, event_name, ticket_type_name, quantity):
    message = EmailMessage()
    message["From"] = os.environ["CORE_EMAIL_FROM"]
    message["To"] = recipient
    message["Subject"] = "Your tickets"
    message.set_content(
        f"You bought {quantity} {ticket_type_name} ticket(s) for {event_name}."
    )

    with smtplib.SMTP(
        host=os.environ["CORE_SMTP_HOST"],
        port=int(os.environ["CORE_SMTP_PORT"]),
    ) as client:
        client.send_message(message)
