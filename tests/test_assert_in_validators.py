"""PYTEST_DONT_REWRITE"""
from pydantic import BaseModel, ValidationError, validator


def test_assert_raises_validation_error():
    class Model(BaseModel):
        a: str

        @validator('a')
        def check_a(cls, v):
            assert v == 'a', 'invalid a'
            return v

    Model(a='a')
    expected_errors = [{'loc': ('a',), 'msg': 'invalid a', 'type': 'assertion_error'}]

    try:
        Model(a='snap')
    except ValidationError as exc:
        actual_errors = exc.errors()
        if actual_errors != expected_errors:
            raise RuntimeError(f'Actual errors: {actual_errors}\nExpected errors: {expected_errors}')
    else:
        raise RuntimeError(f'ValidationError was not raised')
