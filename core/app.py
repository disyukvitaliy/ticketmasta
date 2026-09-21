from application import create_app
from db import configure_sessions, create_primary_engine, create_replica_engine

configure_sessions(
    create_primary_engine(),
    create_replica_engine(),
)

app = create_app()
