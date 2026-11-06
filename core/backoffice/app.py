from sqlalchemy.orm import sessionmaker

from backoffice.application import create_app
from db import create_primary_engine

session_factory = sessionmaker(bind=create_primary_engine())
app = create_app(session_factory)
