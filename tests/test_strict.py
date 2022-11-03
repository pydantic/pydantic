import sys
from typing import Any

if sys.version_info < (3, 9):
    from typing_extensions import Annotated
else:
    from typing import Annotated

import pytest

from pydantic import BaseModel, Field, ValidationError


class ModelWithStrictField(BaseModel):
    a: Annotated[int, Field(strict=True)]


@pytest.mark.parametrize(
    'value',
    [
        '1',
        True,
        1.0,
    ],
)
def test_parse_strict_mode_on_field_invalid(value: Any) -> None:
    with pytest.raises(ValidationError):
        ModelWithStrictField(a=value)


def test_parse_strict_mode_on_field_valid() -> None:
    ModelWithStrictField(a=1)
