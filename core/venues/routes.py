from flask import Blueprint, request
from sqlalchemy import select

from db import ReplicaSession
from venues.models import Venue
from venues.schemas import VenueResponse

bp = Blueprint("venues", __name__)


@bp.get("/venues")
def list_venues():
    page = request.args.get("page", default=1, type=int)
    with ReplicaSession() as session:
        select_stmt = (
            select(Venue)
            .order_by(Venue.name)
            .offset((page - 1) * 10)
            .limit(10)
        )
        venues = session.scalars(select_stmt).all()

    return VenueResponse.serialize_many(venues)


@bp.get("/venues/<int:venue_id>")
def get_venue(venue_id):
    with ReplicaSession() as session:
        venue = session.get(Venue, venue_id)

        if venue is None:
            return {"error": "Not found"}, 404

        return VenueResponse.serialize(venue)
