from __future__ import annotations

from pprint import pprint
from typing import Any, Dict, cast

import pytest

from pydantic import BaseModel, ValidationInfo, model_validator


def test_model_validator_wrap() -> None:
    class Model(BaseModel):
        x: int
        y: int

        @model_validator(mode='wrap')
        @classmethod
        def val_model(cls, values, handler, info) -> Model:
            return handler(values)

    pprint(Model.__pydantic_core_schema__)
    # Model(x=1, y=2).model_dump()
    # assert Model.model_validate(Model(x=1, y=2)).model_dump() == {'x': 3, 'y': 4}


@pytest.mark.parametrize('classmethod_decorator', [classmethod, lambda x: x])
def test_model_validator_before(classmethod_decorator: Any) -> None:
    class Model(BaseModel):
        x: int
        y: int

        @model_validator(mode='before')
        @classmethod_decorator
        def val_model(cls, values: Any, info: ValidationInfo) -> dict[str, Any] | Model:
            assert not info.context
            if isinstance(values, dict):
                values = cast(Dict[str, Any], values)
                values['x'] += 1
                values['y'] += 1
            else:
                assert isinstance(values, Model)
                values.x += 1
                values.y += 1
            return values

    assert Model(x=1, y=2).model_dump() == {'x': 2, 'y': 3}
    assert Model.model_validate(Model(x=1, y=2)).model_dump() == {'x': 3, 'y': 4}


def test_model_validator_after() -> None:
    class Model(BaseModel):
        x: int
        y: int

        @model_validator(mode='after')
        def val_model(self, info: ValidationInfo) -> Model:
            assert not info.context
            self.x += 1
            self.y += 1
            return self

    assert Model(x=1, y=2).model_dump() == {'x': 2, 'y': 3}
    assert Model.model_validate(Model(x=1, y=2)).model_dump() == {'x': 3, 'y': 4}


def test_subclass() -> None:
    class Human(BaseModel):
        @model_validator(mode='before')
        @classmethod
        def run_model_validator(cls, values: dict[str, Any]) -> dict[str, Any]:
            values['age'] *= 2
            return values

    class Person(Human):
        age: int

    assert Person(age=28).age == 56
