"""Test that the mypy plugin implicitly transforms the right decorators into class methods."""

from pydantic import BaseModel, field_validator, model_serializer, model_validator


class Model(BaseModel):
    a: int

    @field_validator('a')
    def f_val(cls, value: int) -> int:
        reveal_type(cls)
# MYPY: note: Revealed type is "type[tests.mypy.modules.decorator_implicit_classmethod.Model]"
        return value

    @model_validator(mode='before')
    def m_val_before(cls, values: dict[str, object]) -> dict[str, object]:
        reveal_type(cls)
# MYPY: note: Revealed type is "type[tests.mypy.modules.decorator_implicit_classmethod.Model]"
        return values

    @model_validator(mode='after')
    def m_val_after(self) -> 'Model':
        reveal_type(self)
# MYPY: note: Revealed type is "tests.mypy.modules.decorator_implicit_classmethod.Model"
        return self

    @model_serializer
    def m_ser(self) -> dict[str, object]:
        reveal_type(self)
# MYPY: note: Revealed type is "tests.mypy.modules.decorator_implicit_classmethod.Model"
        return self.model_dump()
