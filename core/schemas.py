from pydantic import BaseModel, ConfigDict, ValidationError


class ResponseSchema(BaseModel):
    """Serializes application objects into their public API representation."""

    model_config = ConfigDict(from_attributes=True)

    @classmethod
    def from_model(cls, model):
        return cls.model_validate(model)

    @classmethod
    def serialize(cls, model):
        return cls.from_model(model).model_dump(mode="json")

    @classmethod
    def serialize_many(cls, models):
        return [cls.serialize(model) for model in models]


class RequestSchema(BaseModel):
    model_config = ConfigDict(extra="forbid")

    @classmethod
    def parse(cls, data):
        try:
            return cls.model_validate(data)
        except ValidationError as error:
            raise RequestValidationError(error) from error


class RequestValidationError(Exception):
    def __init__(self, error: ValidationError):
        self.errors = error.errors()
        super().__init__("Validation failed")
