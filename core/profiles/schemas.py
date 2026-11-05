from schemas import ResponseSchema


class ProfileResponse(ResponseSchema):
    id: int
    email: str | None
    first_name: str | None
    last_name: str | None
