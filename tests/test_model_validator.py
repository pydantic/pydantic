from __future__ import annotations

from pprint import pprint
from typing import Any, Dict, Union, cast

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

    m = Model(x=1, y=2)
    assert m.model_dump() == {'x': 2, 'y': 3}
    # model not changed because we don't revalidate m
    assert Model.model_validate(m).model_dump() == {'x': 2, 'y': 3}


@pytest.mark.parametrize('classmethod_decorator', [classmethod, lambda x: x])
def test_model_validator_before_revalidate_always(classmethod_decorator: Any) -> None:
    class Model(BaseModel, revalidate_instances='always'):
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


def test_nested_models() -> None:
    calls: list[str] = []

    class Model(BaseModel):
        inner: Union[Model, None]  # noqa

        @model_validator(mode='before')
        @classmethod
        def validate_model_before(cls, values: dict[str, Any]) -> dict[str, Any]:
            calls.append('before')
            return values

        @model_validator(mode='after')
        def validate_model_after(self) -> Model:
            calls.append('after')
            return self

    Model.model_validate({'inner': None})
    assert calls == ['before', 'after']
    calls.clear()

    Model.model_validate({'inner': {'inner': {'inner': None}}})
    assert calls == ['before'] * 3 + ['after'] * 3
    calls.clear()
