from datetime import datetime

from flask import Blueprint, request
from sqlalchemy import select

from db import ReplicaSession
from events.models import Event
from venues.models import Venue

bp = Blueprint("events", __name__)


@bp.get("/events")
@bp.get("/venues/<int:venue_id>/events")
def list_events(venue_id=None):
    page = request.args.get("page", default=1, type=int)
    with ReplicaSession() as session:
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

    return [
        {"id": event.id, "name": event.name, "venue": {"name": venue.name}}
        for event, venue in events
    ]


@bp.get("/events/<int:event_id>")
def get_event(event_id):
    with ReplicaSession() as session:
        event = session.get(Event, event_id)

        if event is None:
            return {"error": "Not found"}, 404

        return {"id": event.id, "name": event.name, "venue_id": event.venue_id}
