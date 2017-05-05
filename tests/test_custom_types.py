import pytest

from pydantic import BaseModel, ValidationError, constr


class ConStringModel(BaseModel):
    v: constr(max_length=10) = 'foobar'


def test_constrained_str_good():
    m = ConStringModel(v='short')
    assert m.v == 'short'


def test_constrained_str_default():
    m = ConStringModel()
    assert m.v == 'foobar'


def test_constrained_str_too_long():
    with pytest.raises(ValidationError) as exc_info:
        ConStringModel(v='this is too long')
    assert exc_info.value.args[0] == ('1 errors validating input: {"v": {'
                                      '"msg": "length greater than maximum allowed: 10", '
                                      '"type": "ValueError", '
                                      '"validator": "ConstrainedStr.validate"}}')
