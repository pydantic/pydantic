import re

import pytest

from pydantic_core import SchemaValidator, ValidationError, core_schema

from ..conftest import Err, PyAndJson, plain_repr


@pytest.mark.parametrize(
    'input_value,expected',
    [
        ('{"a": 1}', {'a': 1}),
        ('"a"', 'a'),
        ('1', 1),
        ('[1, 2, 3, "4"]', [1, 2, 3, '4']),
        (
            '{1: 2}',
            Err(
                'Invalid JSON: key must be a string at line 1 column 2 [type=json_invalid,',
                [
                    {
                        'type': 'json_invalid',
                        'loc': (),
                        'msg': 'Invalid JSON: key must be a string at line 1 column 2',
                        'input': '{1: 2}',
                        'ctx': {'error': 'key must be a string at line 1 column 2'},
                    }
                ],
            ),
        ),
        (44, Err('JSON input should be string, bytes or bytearray [type=json_type, input_value=44, input_type=int')),
    ],
)
def test_any(py_and_json: PyAndJson, input_value, expected):
    v = py_and_json(core_schema.json_schema())
    if isinstance(expected, Err):
        with pytest.raises(ValidationError, match=re.escape(expected.message)) as exc_info:
            v.validate_test(input_value)

        if expected.errors is not None:
            # debug(exc_info.value.errors(include_url=False))
            assert exc_info.value.errors(include_url=False) == expected.errors
    else:
        assert v.validate_test(input_value) == expected


@pytest.mark.parametrize(
    'input_value,expected',
    [
        ('{"a": 1}', {'a': 1}),
        (b'{"a": 1}', {'a': 1}),
        (bytearray(b'{"a": 1}'), {'a': 1}),
        (
            'xx',
            Err(
                'Invalid JSON: expected value at line 1 column 1 '
                "[type=json_invalid, input_value='xx', input_type=str"
            ),
        ),
        (
            b'xx',
            Err(
                'Invalid JSON: expected value at line 1 column 1 '
                "[type=json_invalid, input_value=b'xx', input_type=bytes"
            ),
        ),
        (
            bytearray(b'xx'),
            Err(
                'Invalid JSON: expected value at line 1 column 1 '
                "[type=json_invalid, input_value=bytearray(b'xx'), input_type=bytearray"
            ),
        ),
    ],
)
def test_any_python(input_value, expected):
    v = SchemaValidator(core_schema.json_schema())
    if isinstance(expected, Err):
        with pytest.raises(ValidationError, match=re.escape(expected.message)):
            v.validate_python(input_value)
    else:
        assert v.validate_python(input_value) == expected


@pytest.mark.parametrize(
    'input_value,expected',
    [
        ('[1]', [1]),
        ('[1, 2, 3, "4"]', [1, 2, 3, 4]),
        ('44', Err(r'Input should be a valid (list|array) \[type=list_type, input_value=44, input_type=int')),
        ('"x"', Err(r"Input should be a valid (list|array) \[type=list_type, input_value='x', input_type=str")),
        (
            '[1, 2, 3, "err"]',
            Err(
                r'Input should be a valid integer, unable to parse string as an integer \[type=int_parsing,',
                [
                    {
                        'type': 'int_parsing',
                        'loc': (3,),
                        'msg': 'Input should be a valid integer, unable to parse string as an integer',
                        'input': 'err',
                    }
                ],
            ),
        ),
    ],
)
def test_list_int(py_and_json: PyAndJson, input_value, expected):
    v = py_and_json(core_schema.json_schema(core_schema.list_schema(core_schema.int_schema())))
    if isinstance(expected, Err):
        with pytest.raises(ValidationError, match=expected.message) as exc_info:
            v.validate_test(input_value)

        if expected.errors is not None:
            # debug(exc_info.value.errors(include_url=False))
            assert exc_info.value.errors(include_url=False) == expected.errors
    else:
        assert v.validate_test(input_value) == expected


def test_dict_key(py_and_json: PyAndJson):
    v = py_and_json(
        core_schema.dict_schema(
            core_schema.json_schema(core_schema.tuple_positional_schema([core_schema.int_schema()])),
            core_schema.int_schema(),
        )
    )
    assert v.validate_test({'[1]': 4}) == {(1,): 4}
    with pytest.raises(ValidationError) as exc_info:
        v.validate_test({'x': 4})
    # insert_assert(exc_info.value.errors(include_url=False))
    assert exc_info.value.errors(include_url=False) == [
        {
            'type': 'json_invalid',
            'loc': ('x', '[key]'),
            'msg': 'Invalid JSON: expected value at line 1 column 1',
            'input': 'x',
            'ctx': {'error': 'expected value at line 1 column 1'},
        }
    ]


def test_any_schema_no_schema():
    v = SchemaValidator(core_schema.json_schema())
    assert 'validator:None' in plain_repr(v)
    v = SchemaValidator(core_schema.json_schema(core_schema.any_schema()))
    assert 'validator:None' in plain_repr(v)
    v = SchemaValidator(core_schema.json_schema(core_schema.int_schema()))
    assert 'validator:Some(' in plain_repr(v)
