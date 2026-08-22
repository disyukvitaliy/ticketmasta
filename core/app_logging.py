import logging


class ContextFormatter(logging.Formatter):
    def format(self, record):
        message = super().format(record)

        if record.name.startswith("sqlalchemy.engine."):
            return " ".join(message.split())

        return message


def configure_logging(key=None, context_filter=None):
    root_logger = logging.getLogger()

    handler = logging.StreamHandler()

    if context_filter:
        handler.addFilter(context_filter)

    context_format = f"%({key})s" if key else ""
    handler.setFormatter(
        ContextFormatter(
            "%(asctime)s %(levelname)s %(name)s " + context_format + "%(message)s"
        )
    )

    root_logger.setLevel(logging.INFO)
    root_logger.addHandler(handler)
