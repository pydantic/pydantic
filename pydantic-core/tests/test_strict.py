from __future__ import annotations

import re
from typing import Any

import pytest

from pydantic_core import ValidationError

from .conftest import Err, PyAndJson


@pytest.mark.parametrize(
    'strict_to_validator,strict_in_schema,input_value,expected',
    [
        pytest.param(False, False, 123, 123, id='False-False-123_int-123_int'),
        pytest.param(False, False, '123', 123, id='False-False-123_str-123_int'),
        pytest.param(None, False, 123, 123, id='None-False-123_int-123_int'),
        pytest.param(None, False, '123', 123, id='None-False-123_str-123_int'),
        (True, False, 123, 123),
        (True, False, '123', Err('Input should be a valid integer [type=int_type')),
        pytest.param(False, True, 123, 123, id='False-True-123_int-123_int'),
        pytest.param(False, True, '123', 123, id='False-True-123_str-123_int'),
        (None, True, 123, 123),
        (None, True, '123', Err('Input should be a valid integer [type=int_type')),
        (True, True, 123, 123),
        (True, True, '123', Err('Input should be a valid integer [type=int_type')),
        pytest.param(False, None, 123, 123, id='False-None-123_int-123_int'),
        pytest.param(False, None, '123', 123, id='False-None-123_str-123_int'),
        pytest.param(None, None, 123, 123, id='None-None-123_int-123_int'),
        pytest.param(None, None, '123', 123, id='None-None-123_str-123_int'),
        (True, None, 123, 123),
        (True, None, '123', Err('Input should be a valid integer [type=int_type')),
    ],
)
def test_int_strict_argument(
    py_and_json: PyAndJson, strict_to_validator: bool | None, strict_in_schema: bool | None, input_value, expected
):
    schema: dict[str, Any] = {'type': 'int'}
    if strict_in_schema is not None:
        schema['strict'] = strict_in_schema
    v = py_and_json(schema)
    if isinstance(expected, Err):
        assert v.isinstance_test(input_value, strict_to_validator) is False
        with pytest.raises(ValidationError, match=re.escape(expected.message)):
            v.validate_test(input_value, strict_to_validator)
    else:
        assert v.isinstance_test(input_value, strict_to_validator) is True
        assert v.validate_test(input_value, strict_to_validator) == expected
