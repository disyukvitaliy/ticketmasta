import logging


class ContextFormatter(logging.Formatter):
    def format(self, record):
        fields = getattr(record, "fields", {})
        record.context = " ".join(f"{key}={value}" for key, value in fields.items())

        if record.context:
            record.context += " "

        message = super().format(record)

        if record.name.startswith("sqlalchemy.engine."):
            return " ".join(message.split())

        return message


def configure_logging(context_filter=None):
    root_logger = logging.getLogger()

    handler = logging.StreamHandler()

    if context_filter:
        handler.addFilter(context_filter)

    handler.setFormatter(
        ContextFormatter("%(asctime)s %(levelname)s %(name)s %(context)s%(message)s")
    )

    root_logger.setLevel(logging.INFO)
    root_logger.addHandler(handler)
