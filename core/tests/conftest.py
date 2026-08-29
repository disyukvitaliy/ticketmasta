import pytest
from factories import Factory
from sqlalchemy.orm import Session

from app import create_app
from db import create_primary_engine


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


@pytest.fixture
def app(connection):
    app = create_app(primary_engine=connection, replica_engine=connection)
    app.config.update(TESTING=True)

    return app


@pytest.fixture
def client(app):
    return app.test_client()


@pytest.fixture
def session(connection):
    with Session(connection) as session:
        yield session


@pytest.fixture
def factory(session):
    return Factory(session)
