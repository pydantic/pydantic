import pytest

from pydantic import BaseModel


class Model(BaseModel):
    a: float
    b: int = 10


def test_simple_construct():
    m = Model.construct(a=40, b=10)
    assert m.a == 40
    assert m.b == 10


def test_construct_missing():
    m = Model.construct(a='not a float')
    assert m.a == 'not a float'
    with pytest.raises(AttributeError) as exc_info:
        print(m.b)

    assert "'Model' object has no attribute 'b'" in str(exc_info)
