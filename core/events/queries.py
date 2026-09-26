from datetime import datetime

from sqlalchemy import select
from sqlalchemy.orm import selectinload

from events.models import Event

PAGE_SIZE = 10


def upcoming_events_query(
    *, page: int, venue_id: int | None = None
):
    select_stmt = (
        select(Event)
        .options(selectinload(Event.venue))
        .where(Event.starts_at >= datetime.now())
        .order_by(Event.starts_at)
        .offset((page - 1) * PAGE_SIZE)
        .limit(PAGE_SIZE)
    )

    if venue_id is not None:
        select_stmt = select_stmt.where(Event.venue_id == venue_id)

    return select_stmt
