from datetime import datetime

from flask import Blueprint, request
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from db import ReplicaSession
from events.models import Event
from serializers import EventSerializer

bp = Blueprint("events", __name__)


@bp.get("/events")
@bp.get("/venues/<int:venue_id>/events")
def list_events(venue_id=None):
    page = request.args.get("page", default=1, type=int)
    with ReplicaSession() as session:
        select_stmt = (
            select(Event)
            .options(selectinload(Event.venue))
            .where(Event.starts_at >= datetime.now())
            .order_by(Event.starts_at)
            .offset((page - 1) * 10)
            .limit(10)
        )

        if venue_id:
            select_stmt = select_stmt.where(Event.venue_id == venue_id)

        events = session.scalars(select_stmt).all()

    return EventSerializer.serialize_many(events)


@bp.get("/events/<int:event_id>")
def get_event(event_id):
    with ReplicaSession() as session:
        event = session.get(Event, event_id)

        if event is None:
            return {"error": "Not found"}, 404

        return EventSerializer.serialize(event)
