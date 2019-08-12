"""
This test is executed separately due to pytest's assertion-rewriting
"""
from pydantic import BaseModel, ValidationError, validator


def test_assert_raises_validation_error():
    test_name = test_assert_raises_validation_error.__name__

    class Model(BaseModel):
        a: str

        @validator('a')
        def check_a(cls, v):
            assert v == 'a', 'invalid a'
            return v

    Model(a='a')
    expected_errors = [{'loc': ('a',), 'msg': f'invalid a', 'type': 'assertion_error'}]

    try:
        Model(a='snap')
    except ValidationError as exc:
        actual_errors = exc.errors()
        if actual_errors != expected_errors:
            raise RuntimeError(f"{test_name}:\nActual errors: {actual_errors}\nExpected errors: {expected_errors}")
    else:
        raise RuntimeError(f"{test_name}: ValidationError was not raised")


if __name__ == '__main__':
    test_assert_raises_validation_error()
    print('Non-pytest assert tests passed')
