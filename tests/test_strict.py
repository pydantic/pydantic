import sys
from typing import Any, Type

if sys.version_info < (3, 9):
    from typing_extensions import Annotated
else:
    from typing import Annotated

import pytest

from pydantic import BaseModel, Field, ValidationError


@pytest.fixture(scope='session', name='ModelWithStrictField')
def model_with_strict_field():
    class ModelWithStrictField(BaseModel):
        a: Annotated[int, Field(strict=True)]

    return ModelWithStrictField


@pytest.mark.parametrize(
    'value',
    [
        '1',
        True,
        1.0,
    ],
)
def test_parse_strict_mode_on_field_invalid(value: Any, ModelWithStrictField: Type[BaseModel]) -> None:
    with pytest.raises(ValidationError):
        ModelWithStrictField(a=value)


def test_parse_strict_mode_on_field_valid(ModelWithStrictField: Type[BaseModel]) -> None:
    ModelWithStrictField(a=1)


@pytest.fixture(scope='session', name='ModelWithStrictConfig')
def model_with_strict_config_false():
    class ModelWithStrictConfig(BaseModel):
        a: int
        # strict=False overrides the Config
        b: Annotated[int, Field(strict=False)]
        # strict=None or not including it is equivalent
        # lets this field be overridden by the Config
        c: Annotated[int, Field(strict=None)]
        d: Annotated[int, Field()]

        class Config:
            strict = True

    return ModelWithStrictConfig


def test_parse_model_with_strict_config_enabled(ModelWithStrictConfig: Type[BaseModel]) -> None:
    with pytest.raises(ValidationError):
        ModelWithStrictConfig(a='1', b=2, c=3, d=4)
    with pytest.raises(ValidationError):
        ModelWithStrictConfig(a=1, b=2, c='3', d=4)
    with pytest.raises(ValidationError):
        ModelWithStrictConfig(a=1, b=2, c=3, d='4')
    ModelWithStrictConfig(a=1, b='2', c=3, d=4)
    ModelWithStrictConfig(a=1, b=2, c=3, d=4)


def test_parse_model_with_strict_config_disabled(ModelWithStrictConfig: Type[BaseModel]) -> None:
    class Model(ModelWithStrictConfig):
        class Config:
            strict = False

    Model(a='1', b=2, c=3, d=4)
    Model(a=1, b=2, c='3', d=4)
    Model(a=1, b=2, c=3, d='4')
    Model(a=1, b='2', c=3, d=4)
    Model(a=1, b=2, c=3, d=4)
