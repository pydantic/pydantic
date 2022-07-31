import re

import pytest

from pydantic_core import ValidationError

from .conftest import Err, PyAndJson


@pytest.mark.parametrize(
    'strict,input_value,expected',
    [
        (False, 123, 123),
        (False, '123', 123),
        (None, 123, 123),
        (None, '123', 123),
        (True, 123, 123),
        (True, '123', Err('Input should be a valid integer [kind=int_type')),
    ],
)
def test_int_strict_argument(py_and_json: PyAndJson, strict, input_value, expected):
    v = py_and_json({'type': 'int'})
    if isinstance(expected, Err):
        assert v.isinstance_test(input_value, strict) is False
        with pytest.raises(ValidationError, match=re.escape(expected.message)):
            v.validate_test(input_value, strict)
    else:
        assert v.isinstance_test(input_value, strict) is True
        assert v.validate_test(input_value, strict) == expected
