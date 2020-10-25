"""
PYTEST_DONT_REWRITE
"""
import pytest

from pydantic import BaseModel, ValidationError, validator


def test_assert_raises_validation_error():
    class Model(BaseModel):
        a: str

        @validator('a')
        def check_a(cls, v):
            assert v == 'a', 'invalid a'
            return v

    assert Model(a='a').a == 'a'

    with pytest.raises(ValidationError) as exc_info:
        Model(a='snap')

    assert exc_info.value.errors() == [{'loc': ('a',), 'msg': 'invalid a', 'type': 'assertion_error'}]
