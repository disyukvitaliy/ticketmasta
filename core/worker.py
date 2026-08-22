import logging
from contextvars import ContextVar

import dramatiq

from app_logging import configure_logging
from tasks import broker

job_id = ContextVar("job_id", default=None)

logger = logging.getLogger(__name__)

logging.getLogger("sqlalchemy.engine").setLevel(logging.INFO)


class JobContextFilter(logging.Filter):
    def filter(self, record):
        fields = dict(getattr(record, "fields", {}))
        current_job_id = job_id.get()

        if current_job_id:
            fields = {"job_id": current_job_id, **fields}

        record.fields = fields
        return True


class JobLoggingMiddleware(dramatiq.Middleware):
    def after_process_boot(self, broker):
        configure_logging(JobContextFilter())

    def before_process_message(self, broker, message):
        job_id.set(message.message_id)

        logger.info(
            "Job started",
            extra={"fields": {"actor": message.actor_name}},
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
                "Job finished",
                extra={"fields": {"actor": message.actor_name}},
            )

        self._clear_context()

    def after_skip_message(self, broker, message):
        logger.info(
            "Job skipped",
            extra={"fields": {"actor": message.actor_name}},
        )

        self._clear_context()

    def _clear_context(self):
        job_id.set(None)


broker.add_middleware(JobLoggingMiddleware())
