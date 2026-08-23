import logging


class ContextFilter(logging.Filter):
    def filter(self, record):
        record.fields = getattr(record, "fields", {})

        return True


class PlainTextFormatter(logging.Formatter):
    def formatMessage(self, record):
        context = " ".join(f"{key}={value}" for key, value in record.fields.items())
        record.context = f" {context} " if context else " "

        return super().formatMessage(record)


def configure_logging(context_filter=None):
    root_logger = logging.getLogger()

    handler = logging.StreamHandler()

    handler.addFilter(ContextFilter())

    if context_filter:
        handler.addFilter(context_filter)

    handler.setFormatter(
        PlainTextFormatter("%(asctime)s %(levelname)s %(name)s%(context)s%(message)s")
    )

    root_logger.setLevel(logging.INFO)
    root_logger.addHandler(handler)
