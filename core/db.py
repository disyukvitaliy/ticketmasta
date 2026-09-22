import logging
import os

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker


class Base(DeclarativeBase):
    pass


PrimarySession = sessionmaker()
ReplicaSession = sessionmaker()


def configure_sessions(primary_bind, replica_bind, **options):
    PrimarySession.configure(bind=primary_bind, **options)
    ReplicaSession.configure(bind=replica_bind, **options)


class SqlAlchemyMessageFilter(logging.Filter):
    def filter(self, record):
        record.msg = record.msg.replace("\n", "")

        return True


sqlalchemy_message_filter = SqlAlchemyMessageFilter()


def _create_engine(dsn, logging_name):
    engine = create_engine(dsn, logging_name=logging_name)
    engine.logger.addFilter(sqlalchemy_message_filter)
    engine.logger.setLevel(logging.INFO)

    return engine


def create_primary_engine():
    return _create_engine(os.environ["CORE_DB_DSN"], "primary")


def create_replica_engine():
    return _create_engine(os.environ["CORE_READ_DB_DSN"], "replica")
