import pytest
from dataclasses import dataclass

import pydantic
from pydantic import ValidationError


@dataclass
class ModelDataclass:
    i: int
    f: float


@pydantic.dataclasses.dataclass
class ModelPydanticDataclass:
    i: int
    f: float


def test_dataclasses():
    instance_dataclass = ModelDataclass(1, 2)
    instance_pydantic_dataclass = ModelPydanticDataclass(1, 2)
    assert instance_dataclass.i == 1
    assert instance_pydantic_dataclass.i == 1
    instance_pydantic_dataclass.i = 0
    assert instance_pydantic_dataclass.i == 0

    with pytest.raises(ValidationError):
        ModelPydanticDataclass(1, '')

    with pytest.raises(ValidationError):
        instance_pydantic_dataclass.f = ''
