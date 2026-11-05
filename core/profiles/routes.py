import logging

from flask import Blueprint, g
from sqlalchemy import select

from db import ReplicaSession
from profiles.models import Profile
from profiles.schemas import ProfileResponse

logger = logging.getLogger(__name__)

bp = Blueprint("profiles", __name__)


@bp.get("/profile")
def get_profile():
    with ReplicaSession() as session:
        profile = session.scalar(
            select(Profile).where(Profile.user_id == g.user_id)
        )

        if profile is None:
            logger.error(
                "Profile not found",
                extra={"fields": {"user_id": g.user_id}},
            )
            return {"error": "Not found"}, 404

        return ProfileResponse.serialize(profile)
