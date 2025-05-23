from __future__ import annotations

import re
from typing import Any, cast

import pytest

from pydantic import BaseModel, ValidationInfo, ValidatorFunctionWrapHandler, model_validator
from pydantic.errors import PydanticUserError
from pydantic.warnings import PydanticDeprecatedSince211


def test_model_validator_wrap() -> None:
    class Model(BaseModel):
        x: int
        y: int

        @model_validator(mode='wrap')
        @classmethod
        def val_model(cls, values: dict[str, Any] | Model, handler: ValidatorFunctionWrapHandler) -> Model:
            if isinstance(values, dict):
                assert values == {'x': 1, 'y': 2}
                model = handler({'x': 2, 'y': 3})
            else:
                assert values.x == 1
                assert values.y == 2
                model = handler(Model.model_construct(x=2, y=3))
            assert model.x == 2
            assert model.y == 3
            model.x = 20
            model.y = 30
            return model

    assert Model(x=1, y=2).model_dump() == {'x': 20, 'y': 30}
    assert Model.model_validate(Model.model_construct(x=1, y=2)).model_dump() == {'x': 20, 'y': 30}


def test_model_validator_before() -> None:
    class Model(BaseModel):
        x: int
        y: int

        @model_validator(mode='before')
        @classmethod
        def val_model(cls, values: Any, info: ValidationInfo) -> dict[str, Any] | Model:
            assert not info.context
            if isinstance(values, dict):
                values = cast(dict[str, Any], values)
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


def test_model_validator_before_revalidate_always() -> None:
    class Model(BaseModel, revalidate_instances='always'):
        x: int
        y: int

        @model_validator(mode='before')
        @classmethod
        def val_model(cls, values: Any, info: ValidationInfo) -> dict[str, Any] | Model:
            assert not info.context
            if isinstance(values, dict):
                values = cast(dict[str, Any], values)
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
        inner: Model | None

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


def test_model_validator_before_on_not_decorated_classmethod() -> None:
    warning_message = "`@model_validator(mode='before')` should be applied to a classmethod, not an instance method"
    with pytest.warns(PydanticDeprecatedSince211, match=re.escape(warning_message)):

        class M(BaseModel):
            x: int

            @model_validator(mode='before')
            def validator(cls, data: Any) -> Any:
                return data


def test_model_validator_wrap_on_not_decorated_classmethod() -> None:
    warning_message = "`@model_validator(mode='wrap')` should be applied to a classmethod, not an instance method"
    with pytest.warns(PydanticDeprecatedSince211, match=re.escape(warning_message)):

        class M(BaseModel):
            x: int

            @model_validator(mode='wrap')
            def validator(cls, data: Any, handler: ValidatorFunctionWrapHandler) -> Any:
                return handler(data)


def test_model_validator_after_on_invalid_signature() -> None:
    warning_message = 'Unrecognized model_validator function signature'
    with pytest.raises(PydanticUserError, match=re.escape(warning_message)):

        class M(BaseModel):
            x: int

            @model_validator(mode='after')
            def validator(cls, model, info) -> Any:
                return model
