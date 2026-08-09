from flask import Flask, g, has_request_context, make_response, request
from flask.logging import default_handler
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, Session
from sqlalchemy import String, DateTime, ForeignKey, create_engine, select
from datetime import datetime
from time import perf_counter
from uuid import uuid4
import logging
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


class RequestFormatter(logging.Formatter):
    def format(self, record):
        record.request_id = g.get('request_id', '-') if has_request_context() else '-'
        return super().format(record)


default_handler.setFormatter(RequestFormatter(
    '%(asctime)s %(levelname)s request_id=%(request_id)s %(message)s'
))
app.logger.setLevel(logging.INFO)

if os.environ.get('CORE_ENV') == 'development':
    logging.getLogger('werkzeug').setLevel(logging.WARNING)


@app.before_request
def assign_request_id():
    g.request_id = request.headers.get('X-Request-ID') or str(uuid4())
    g.request_started_at = perf_counter()


@app.after_request
def log_request(response):
    response.headers['X-Request-ID'] = g.request_id
    duration_ms = (perf_counter() - g.request_started_at) * 1000
    app.logger.info(
        'request_completed method=%s path=%s status=%s duration_ms=%.2f',
        request.method,
        request.path,
        response.status_code,
        duration_ms,
    )
    return response


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

@app.route('/venues')
def list_venues():
    page = request.args.get('page', default=1, type=int)
    with Session(engine) as session:
        select_stmt = (
            select(Venue)
            .order_by(Venue.name)
            .offset((page - 1) * 10)
            .limit(10)
        )
        venues = session.scalars(select_stmt).all()

    return [{'id': venue.id, 'name': venue.name} for venue in venues]

@app.route('/venues/<int:venue_id>')
def get_venue(venue_id):
    with Session(engine) as session:
        venue = session.get(Venue, venue_id)

        if venue is None:
            return {'error': 'Not found'}, 404

        return {'id': venue.id, 'name': venue.name}

@app.route('/events')
@app.route('/venues/<int:venue_id>/events')
def list_events(venue_id=None):
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

        if venue_id:
            select_stmt = select_stmt.where(Venue.id == venue_id)

        events = session.execute(select_stmt).all()

    return [{'id': event.id, 'name': event.name, 'venue': {'name': venue.name}} for event, venue in events]
