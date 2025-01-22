"""Test that the mypy plugin implicitly transforms the right decorators into class methods."""

from pydantic import BaseModel, field_validator, model_serializer, model_validator


class Model(BaseModel):
    a: int

    @field_validator('a')
    def f_val(cls, value: int) -> int:
        reveal_type(cls)
        return value

    @model_validator(mode='before')
    def m_val_before(cls, values: dict[str, object]) -> dict[str, object]:
        reveal_type(cls)
        return values

    @model_validator(mode='after')
    def m_val_after(self) -> 'Model':
        reveal_type(self)
        return self

    @model_serializer
    def m_ser(self) -> dict[str, object]:
        reveal_type(self)
        return self.model_dump()
