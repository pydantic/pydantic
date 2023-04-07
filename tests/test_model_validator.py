from __future__ import annotations

from typing import Any, Dict, cast

from pydantic import BaseModel, ValidationInfo
from pydantic.decorators import ModelWrapValidatorHandler, model_validator


def test_model_validator_wrap() -> None:
    class Model(BaseModel):
        x: int
        y: int

        @model_validator(mode='wrap')
        @classmethod
        def val_model(cls, values: Any, handler: ModelWrapValidatorHandler[Model], info: ValidationInfo) -> Model:
            assert not info.context
            if isinstance(values, dict):
                assert values['x'] != values['y']
            else:
                assert isinstance(values, Model)
                assert values.x != values.y
            self = handler(values)
            self.x += 1
            self.y += 1
            return self

    assert Model(x=1, y=2).model_dump() == {'x': 2, 'y': 3}
    assert Model.model_validate(Model(x=1, y=2)).model_dump() == {'x': 3, 'y': 4}


def test_model_validator_before() -> None:
    class Model(BaseModel):
        x: int
        y: int

        @model_validator(mode='before')
        @classmethod
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
