from datetime import datetime

from pydantic import Field

from schemas import RequestSchema, ResponseSchema
from ticketing.models import TicketHoldStatus


class CreateTicketHoldRequest(RequestSchema):
    quantity: int = Field(gt=0)


class TicketTypeResponse(ResponseSchema):
    id: int
    event_id: int
    name: str
    price_cents: int
    quantity: int


class TicketHoldResponse(ResponseSchema):
    id: int
    ticket_type_id: int
    status: TicketHoldStatus
    quantity: int
    expires_at: datetime
