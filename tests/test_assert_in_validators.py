"""
PYTEST_DONT_REWRITE
"""
import pytest

from pydantic import BaseModel, ValidationError, field_validator


def test_assert_raises_validation_error():
    class Model(BaseModel):
        a: str

        @field_validator('a')
        @classmethod
        def check_a(cls, v):
            assert v == 'a', 'invalid a'
            return v

    assert Model(a='a').a == 'a'

    with pytest.raises(ValidationError) as exc_info:
        Model(a='snap')

    expected_errors = [
        {
            'type': 'assertion_error',
            'loc': ('a',),
            'msg': 'Assertion failed, invalid a',
            'input': 'snap',
            'ctx': {'error': 'invalid a'},
        }
    ]
    actual_errors = exc_info.value.errors(include_url=False)
    if expected_errors != actual_errors:
        pytest.fail(f'Actual errors: {actual_errors}\nExpected errors: {expected_errors}')
