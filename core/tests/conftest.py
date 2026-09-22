import pytest

from application import create_app
from db import configure_sessions, create_primary_engine
from tests.db import TestSession


@pytest.fixture(scope="session")
def engine():
    engine = create_primary_engine()
    yield engine
    engine.dispose()


@pytest.fixture
def connection(engine):
    connection = engine.connect()
    transaction = connection.begin()

    yield connection

    transaction.rollback()
    connection.close()


@pytest.fixture(autouse=True)
def session(connection):
    configure_sessions(
        connection,
        connection,
        join_transaction_mode="create_savepoint",
    )
    TestSession.configure(
        bind=connection,
        join_transaction_mode="create_savepoint",
    )

    yield TestSession()

    TestSession.remove()


@pytest.fixture
def client():
    app = create_app()
    app.config.update(TESTING=True)
    return app.test_client()
