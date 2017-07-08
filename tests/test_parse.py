import pytest

from pydantic import BaseModel, ValidationError


class Model(BaseModel):
    a: float = ...
    b: int = 10


def test_parse_obj():
    m = Model.parse_obj(dict(a=10.2))
    assert str(m) == 'Model a=10.2 b=10'


def test_parse_fails():
    with pytest.raises(ValidationError) as exc_info:
        Model.parse_obj([1, 2, 3])
    assert """\
1 error validating input
Model expected dict not list (error_type=TypeError)""" == str(exc_info.value)


def test_parse_str():
    m = Model.parse_raw('{"a": 12, "b": 8}')
    assert str(m) == 'Model a=12.0 b=8'
