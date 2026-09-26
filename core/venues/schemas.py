from schemas import ResponseSchema


class VenueResponse(ResponseSchema):
    id: int
    name: str
