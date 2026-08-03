from flask import Flask, request, make_response
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, Session
from sqlalchemy import String, ForeignKey, create_engine, select
import os, sys

class Base(DeclarativeBase):
    pass

class Venue(Base):
    __tablename__ = 'venues'
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(255))

class Event(Base):
    __tablename__ = 'events'
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(255))
    venue_id: Mapped[int] = mapped_column(ForeignKey('venues.id'))

engine = create_engine(os.environ["CORE_DB_DSN"])

app = Flask(__name__)

@app.route('/')
def main_page():
    # return 'Main page'
    print(request.environ)
    sys.stdout.flush()
    headers = {key: value for key, value in request.headers.items()}
    return f'Headers: {headers}'

@app.route('/home')
def home_page():
    return 'Home page'

@app.route('/profile')
def profile_page():
    headers_to_include = ['X-User-Id', 'X-User-Email', 'X-User-Role']  # Adjust headers as needed
    headers_text = "\n".join(
        f"{header}: {request.headers.get(header, 'Not Provided')}"
        for header in headers_to_include
    )

    response = make_response(headers_text)
    response.mimetype = "text/plain"
    return response, 200

@app.route('/events')
def events_list():
    with Session(engine) as session:
        events = session.scalars(select(Event)).all()

    return [{'id': event.id, 'name': event.name} for event in events]
