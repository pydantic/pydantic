import pytest


@pytest.fixture(name='Foobar')
def fix_model(create_module):
    module = create_module(
        # language=Python
        """
from __future__ import annotations
from pydantic import BaseModel

class Foobar(BaseModel):
    x: int
    y: Foobar | None = None
"""
    )
    return module.Foobar


def test_recursive_model(Foobar):
    f = Foobar(x=1, y={'x': 2})
    assert f.dict() == {'x': 1, 'y': {'x': 2, 'y': None}}
    assert f.__fields_set__ == {'x', 'y'}
    assert f.y.__fields_set__ == {'x'}
