import logging
from contextvars import ContextVar

from flask import g, has_request_context

job_id = ContextVar("job_id", default=None)


class ContextFilter(logging.Filter):
    def filter(self, record):
        context = []

        if has_request_context():
            context.append(f"request_id={g.get('request_id')}")

        if current_job_id := job_id.get():
            context.append(f"job_id={current_job_id}")

        record.context = f"{' '.join(context)} " if context else ""
        return True


class ContextFormatter(logging.Formatter):
    def format(self, record):
        message = super().format(record)

        if record.name.startswith("sqlalchemy.engine."):
            return " ".join(message.split())

        return message


def configure_logging():
    root_logger = logging.getLogger()

    if root_logger.handlers:
        return

    handler = logging.StreamHandler()
    handler.addFilter(ContextFilter())
    handler.setFormatter(
        ContextFormatter("%(asctime)s %(levelname)s %(name)s %(context)s%(message)s")
    )

    root_logger.setLevel(logging.INFO)
    root_logger.addHandler(handler)
