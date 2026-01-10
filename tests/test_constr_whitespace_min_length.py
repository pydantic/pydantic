import pytest
from pydantic import BaseModel, constr, ValidationError


def test_whitespace_only_string_fails_when_min_length_set():
    class Model(BaseModel):
        name: constr(min_length=1)

    with pytest.raises(ValidationError):
        Model(name="   ")


def test_string_with_non_whitespace_passes():
    class Model(BaseModel):
        name: constr(min_length=1)

    m = Model(name=" a ")
    assert m.name == " a "
