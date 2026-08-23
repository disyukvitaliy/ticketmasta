import logging
import os

from sqlalchemy import create_engine


class SqlAlchemyMessageFilter(logging.Filter):
    def filter(self, record):
        record.msg = record.msg.replace("\n", "")

        return True


sqlalchemy_message_filter = SqlAlchemyMessageFilter()


def _create_engine(dsn, logging_name):
    logging.getLogger(
        f"sqlalchemy.engine.Engine.{logging_name}"
    ).addFilter(sqlalchemy_message_filter)

    return create_engine(dsn, logging_name=logging_name)


def create_primary_engine():
    return _create_engine(os.environ["CORE_DB_DSN"], "primary")


def create_replica_engine():
    return _create_engine(os.environ["CORE_READ_DB_DSN"], "replica")
