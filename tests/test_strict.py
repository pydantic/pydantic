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
