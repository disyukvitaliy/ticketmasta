from collections.abc import Iterable
from datetime import datetime
from typing import Any, Self

from pydantic import BaseModel, ConfigDict

from ticketing.models import TicketHoldStatus


class Serializer(BaseModel):
    """Converts application objects into the JSON shape exposed by the API."""

    model_config = ConfigDict(from_attributes=True)

    @classmethod
    def from_model(cls, model: object) -> Self:
        return cls.model_validate(model)

    @classmethod
    def serialize(cls, model: object) -> dict[str, Any]:
        return cls.from_model(model).model_dump(mode="json")

    @classmethod
    def serialize_many(cls, models: Iterable[object]) -> list[dict[str, Any]]:
        return [cls.serialize(model) for model in models]


class VenueSerializer(Serializer):
    id: int
    name: str


class EventSerializer(Serializer):
    id: int
    name: str
    venue: VenueSerializer


class TicketTypeSerializer(Serializer):
    id: int
    event_id: int
    name: str
    price_cents: int
    quantity: int


class TicketHoldSerializer(Serializer):
    id: int
    ticket_type_id: int
    status: TicketHoldStatus
    quantity: int
    expires_at: datetime
