from typing import Callable

import pytest

from pydantic import BaseModel, ValidationError


def test_callable():
    class Model(BaseModel):
        callback: Callable[[int], int]

    m = Model(callback=lambda x: x)
    assert callable(m.callback)


def test_non_callable():
    class Model(BaseModel):
        callback: Callable[[int], int]

    with pytest.raises(ValidationError):
        Model(callback=1)
