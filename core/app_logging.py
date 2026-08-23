import logging


class ContextFilter(logging.Filter):
    def filter(self, record):
        fields = {**self.context_fields(), **getattr(record, "fields", {})}
        record.fields = fields
        record.context = format_context(fields)

        return True

    def context_fields(self):
        return {}


def format_context(fields):
    context = " ".join(f"{key}={value}" for key, value in fields.items())

    return f"{context} " if context else ""


def configure_logging(context_filter=None):
    root_logger = logging.getLogger()

    handler = logging.StreamHandler()

    handler.addFilter(context_filter or ContextFilter())

    handler.setFormatter(
        logging.Formatter("%(asctime)s %(levelname)s %(name)s %(context)s%(message)s")
    )

    root_logger.setLevel(logging.INFO)
    root_logger.addHandler(handler)
