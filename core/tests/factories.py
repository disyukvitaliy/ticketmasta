from datetime import datetime, timedelta

import factory
from factory.alchemy import SQLAlchemyModelFactory

from events.models import Event
from tests.db import TestSession
from ticketing.models import TicketHold, TicketHoldStatus, TicketType
from venues.models import Venue


class BaseFactory(SQLAlchemyModelFactory):
    class Meta:
        abstract = True
        sqlalchemy_session = TestSession
        sqlalchemy_session_persistence = "flush"


class VenueFactory(BaseFactory):
    class Meta:
        model = Venue

    name = factory.Sequence(lambda number: f"Venue {number}")


class EventFactory(BaseFactory):
    class Meta:
        model = Event

    venue_id = factory.LazyFunction(lambda: VenueFactory().id)
    name = factory.Sequence(lambda number: f"Event {number}")
    starts_at = factory.LazyFunction(lambda: datetime.now() + timedelta(days=1))


class TicketTypeFactory(BaseFactory):
    class Meta:
        model = TicketType

    event_id = factory.LazyFunction(lambda: EventFactory().id)
    name = factory.Sequence(lambda number: f"Ticket type {number}")
    price_cents = 1_000
    quantity = 3


class TicketHoldFactory(BaseFactory):
    class Meta:
        model = TicketHold

    ticket_type_id = factory.LazyFunction(lambda: TicketTypeFactory().id)
    user_id = 1
    quantity = 1
    status = TicketHoldStatus.ACTIVE
    expires_at = factory.LazyFunction(lambda: datetime.now() + timedelta(minutes=15))
