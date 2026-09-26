from schemas import ResponseSchema
from venues.schemas import VenueResponse


class EventResponse(ResponseSchema):
    id: int
    name: str
    venue: VenueResponse
