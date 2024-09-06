import math
import platform
import re
import sys

import pytest

from pydantic_core import SchemaValidator, ValidationError

from ..conftest import Err

EXPECTED_PARSE_ERROR_MESSAGE = 'Input should be a valid complex string following the rules at https://docs.python.org/3/library/functions.html#complex'
EXPECTED_TYPE_ERROR_MESSAGE = 'Input should be a valid python complex object, a number, or a valid complex string following the rules at https://docs.python.org/3/library/functions.html#complex'
EXPECTED_TYPE_ERROR_PY_STRICT_MESSAGE = 'Input should be an instance of complex'


@pytest.mark.parametrize(
    'input_value,expected',
    [
        (complex(2, 4), complex(2, 4)),
        ('2', complex(2, 0)),
        ('2j', complex(0, 2)),
        ('+1.23e-4-5.67e+8J', complex(1.23e-4, -5.67e8)),
        ('1.5-j', complex(1.5, -1)),
        ('-j', complex(0, -1)),
        ('j', complex(0, 1)),
        (3, complex(3, 0)),
        (2.0, complex(2, 0)),
        ('1e-700j', complex(0, 0)),
        ('', Err(EXPECTED_TYPE_ERROR_MESSAGE)),
        ('\t( -1.23+4.5J   \n', Err(EXPECTED_TYPE_ERROR_MESSAGE)),
        ({'real': 2, 'imag': 4}, Err(EXPECTED_TYPE_ERROR_MESSAGE)),
        ({'real': 'test', 'imag': 1}, Err(EXPECTED_TYPE_ERROR_MESSAGE)),
        ({'real': True, 'imag': 1}, Err(EXPECTED_TYPE_ERROR_MESSAGE)),
        ('foobar', Err(EXPECTED_TYPE_ERROR_MESSAGE)),
        ([], Err(EXPECTED_TYPE_ERROR_MESSAGE)),
        ([('x', 'y')], Err(EXPECTED_TYPE_ERROR_MESSAGE)),
        ((), Err(EXPECTED_TYPE_ERROR_MESSAGE)),
        ((('x', 'y'),), Err(EXPECTED_TYPE_ERROR_MESSAGE)),
        (
            (type('Foobar', (), {'x': 1})()),
            Err(EXPECTED_TYPE_ERROR_MESSAGE),
        ),
    ],
    ids=repr,
)
def test_complex_cases(input_value, expected):
    v = SchemaValidator({'type': 'complex'})
    if isinstance(expected, Err):
        with pytest.raises(ValidationError, match=re.escape(expected.message)):
            v.validate_python(input_value)
    else:
        assert v.validate_python(input_value) == expected


@pytest.mark.parametrize(
    'input_value,expected',
    [
        (complex(2, 4), complex(2, 4)),
        ('2', Err(EXPECTED_TYPE_ERROR_PY_STRICT_MESSAGE)),
        ('2j', Err(EXPECTED_TYPE_ERROR_PY_STRICT_MESSAGE)),
        ('+1.23e-4-5.67e+8J', Err(EXPECTED_TYPE_ERROR_PY_STRICT_MESSAGE)),
        ('1.5-j', Err(EXPECTED_TYPE_ERROR_PY_STRICT_MESSAGE)),
        ('-j', Err(EXPECTED_TYPE_ERROR_PY_STRICT_MESSAGE)),
        ('j', Err(EXPECTED_TYPE_ERROR_PY_STRICT_MESSAGE)),
        (3, Err(EXPECTED_TYPE_ERROR_PY_STRICT_MESSAGE)),
        (2.0, Err(EXPECTED_TYPE_ERROR_PY_STRICT_MESSAGE)),
        ('1e-700j', Err(EXPECTED_TYPE_ERROR_PY_STRICT_MESSAGE)),
        ('', Err(EXPECTED_TYPE_ERROR_PY_STRICT_MESSAGE)),
        ('\t( -1.23+4.5J   \n', Err(EXPECTED_TYPE_ERROR_PY_STRICT_MESSAGE)),
        ({'real': 2, 'imag': 4}, Err(EXPECTED_TYPE_ERROR_PY_STRICT_MESSAGE)),
        ({'real': 'test', 'imag': 1}, Err(EXPECTED_TYPE_ERROR_PY_STRICT_MESSAGE)),
        ({'real': True, 'imag': 1}, Err(EXPECTED_TYPE_ERROR_PY_STRICT_MESSAGE)),
        ('foobar', Err(EXPECTED_TYPE_ERROR_PY_STRICT_MESSAGE)),
    ],
    ids=repr,
)
def test_complex_strict(input_value, expected):
    v = SchemaValidator({'type': 'complex', 'strict': True})
    if isinstance(expected, Err):
        with pytest.raises(ValidationError, match=re.escape(expected.message)):
            v.validate_python(input_value)
    else:
        assert v.validate_python(input_value) == expected


@pytest.mark.xfail(
    platform.python_implementation() == 'PyPy' and sys.pypy_version_info < (7, 3, 17),
    reason='PyPy cannot process this string due to a bug, even if this string is considered valid in python',
)
def test_valid_complex_string_with_space():
    v = SchemaValidator({'type': 'complex'})
    assert v.validate_python('\t( -1.23+4.5J )\n') == complex(-1.23, 4.5)


def test_nan_inf_complex():
    v = SchemaValidator({'type': 'complex'})
    c = v.validate_python('NaN+Infinityj')
    # c != complex(float('nan'), float('inf')) as nan != nan,
    # so we need to examine the values individually
    assert math.isnan(c.real)
    assert math.isinf(c.imag)


def test_overflow_complex():
    # Python simply converts too large float values to inf, so these strings
    # are still valid, even if the numbers are out of range
    v = SchemaValidator({'type': 'complex'})

    c = v.validate_python('5e600j')
    assert math.isinf(c.imag)

    c = v.validate_python('-5e600j')
    assert math.isinf(c.imag)


def test_json_complex():
    v = SchemaValidator({'type': 'complex'})
    assert v.validate_json('"-1.23e+4+5.67e-8J"') == complex(-1.23e4, 5.67e-8)
    assert v.validate_json('1') == complex(1, 0)
    assert v.validate_json('1.0') == complex(1, 0)
    # "1" is a valid complex string
    assert v.validate_json('"1"') == complex(1, 0)

    with pytest.raises(ValidationError) as exc_info:
        v.validate_json('{"real": 2, "imag": 4}')
    assert exc_info.value.errors(include_url=False) == [
        {
            'type': 'complex_type',
            'loc': (),
            'msg': EXPECTED_TYPE_ERROR_MESSAGE,
            'input': {'real': 2, 'imag': 4},
        }
    ]


def test_json_complex_strict():
    v = SchemaValidator({'type': 'complex', 'strict': True})
    assert v.validate_json('"-1.23e+4+5.67e-8J"') == complex(-1.23e4, 5.67e-8)
    # "1" is a valid complex string
    assert v.validate_json('"1"') == complex(1, 0)

    with pytest.raises(ValidationError, match=re.escape(EXPECTED_PARSE_ERROR_MESSAGE)):
        v.validate_json('1')
    with pytest.raises(ValidationError, match=re.escape(EXPECTED_PARSE_ERROR_MESSAGE)):
        v.validate_json('1.0')
    with pytest.raises(ValidationError, match=re.escape(EXPECTED_TYPE_ERROR_MESSAGE)):
        v.validate_json('{"real": 2, "imag": 4}')


def test_string_complex():
    v = SchemaValidator({'type': 'complex'})
    assert v.validate_strings('+1.23e-4-5.67e+8J') == complex(1.23e-4, -5.67e8)
    with pytest.raises(ValidationError, match=re.escape(EXPECTED_PARSE_ERROR_MESSAGE)):
        v.validate_strings("{'real': 1, 'imag': 0}")
