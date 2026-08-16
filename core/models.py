from datetime import datetime
from enum import Enum

from sqlalchemy import DateTime, ForeignKey, String
from sqlalchemy import Enum as SqlEnum
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


class Venue(Base):
    __tablename__ = "venues"
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(255))


class Event(Base):
    __tablename__ = "events"
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(255))
    starts_at: Mapped[datetime] = mapped_column(DateTime())
    venue_id: Mapped[int] = mapped_column(ForeignKey("venues.id"))


class TicketType(Base):
    __tablename__ = "ticket_types"
    id: Mapped[int] = mapped_column(primary_key=True)
    event_id: Mapped[int] = mapped_column(ForeignKey("events.id"))
    name: Mapped[str] = mapped_column(String(255))
    price_cents: Mapped[int] = mapped_column()
    quantity: Mapped[int] = mapped_column()


class TicketHoldStatus(str, Enum):
    ACTIVE = "active"
    CANCELED = "canceled"
    COMPLETED = "completed"
    EXPIRED = "expired"


class TicketHold(Base):
    __tablename__ = "ticket_holds"
    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(nullable=False)
    ticket_type_id: Mapped[int] = mapped_column(
        ForeignKey("ticket_types.id"), nullable=False
    )
    quantity: Mapped[int] = mapped_column(nullable=False)
    status: Mapped[TicketHoldStatus] = mapped_column(
        SqlEnum(
            TicketHoldStatus,
            values_callable=lambda enum: [status.value for status in enum],
        ),
        default=TicketHoldStatus.ACTIVE,
        nullable=False,
    )
    expires_at: Mapped[datetime] = mapped_column(DateTime(), nullable=False)
