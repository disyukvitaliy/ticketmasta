from flask import Blueprint, request

from db import ReplicaSession
from events.models import Event
from events.queries import upcoming_events_query
from events.schemas import EventResponse

bp = Blueprint("events", __name__)


@bp.get("/events")
@bp.get("/venues/<int:venue_id>/events")
def list_events(venue_id=None):
    page = request.args.get("page", default=1, type=int)
    with ReplicaSession() as session:
        events = session.scalars(
            upcoming_events_query(
                page=page,
                venue_id=venue_id,
            )
        ).all()

    return EventResponse.serialize_many(events)


@bp.get("/events/<int:event_id>")
def get_event(event_id):
    with ReplicaSession() as session:
        event = session.get(Event, event_id)

        if event is None:
            return {"error": "Not found"}, 404

        return EventResponse.serialize(event)
