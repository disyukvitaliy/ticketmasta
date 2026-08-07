from flask import Flask, make_response, request
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, Session
from sqlalchemy import String, DateTime, ForeignKey, create_engine, select
from datetime import datetime
import os

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
    starts_at: Mapped[datetime] = mapped_column(DateTime())
    venue_id: Mapped[int] = mapped_column(ForeignKey('venues.id'))

engine = create_engine(os.environ["CORE_DB_DSN"])

app = Flask(__name__)

@app.route('/profile')
def profile():
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
    page = request.args.get('page', default=1, type=int)
    with Session(engine) as session:
        select_stmt = (
            select(Event, Venue)
            .join(Venue)
            .where(Event.starts_at >= datetime.now())
            .order_by(Event.starts_at)
            .offset((page - 1) * 10)
            .limit(10)
        )

        events = session.execute(select_stmt).all()

    return [{'id': event.id, 'name': event.name, 'venue': {'name': venue.name}} for event, venue in events]
