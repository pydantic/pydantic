"""
This test is executed separately due to pytest's assertion-rewriting
"""
import sys
from typing import List

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
            description = [f'Actual errors: {actual_errors}', f'Expected errors: {expected_errors}']
            fail_test(test_name, description)
    else:
        fail_test(test_name, ['ValidationError was not raised'])


def fail_test(test_name: str, description: List[str]):
    print(f'{__file__}: failure in {test_name}')
    print('\n'.join(['    ' + line for line in description]))
    sys.exit(1)


if __name__ == '__main__':
    test_assert_raises_validation_error()
    print('Non-pytest assert tests passed')
