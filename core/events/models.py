from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from db import Base
from venues.models import Venue


class Event(Base):
    __tablename__ = "events"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(255))
    starts_at: Mapped[datetime] = mapped_column(DateTime())
    venue_id: Mapped[int] = mapped_column(ForeignKey("venues.id"))
    venue: Mapped[Venue] = relationship()
