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
            # debug(exc_info.value.errors())
            assert exc_info.value.errors() == expected.errors
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
        ('44', Err('Input should be a valid list/array [type=list_type, input_value=44, input_type=int')),
        ('"x"', Err("Input should be a valid list/array [type=list_type, input_value='x', input_type=str")),
        (
            '[1, 2, 3, "err"]',
            Err(
                'Input should be a valid integer, unable to parse string as an integer [type=int_parsing,',
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
        with pytest.raises(ValidationError, match=re.escape(expected.message)) as exc_info:
            v.validate_test(input_value)

        if expected.errors is not None:
            # debug(exc_info.value.errors())
            assert exc_info.value.errors() == expected.errors
    else:
        assert v.validate_test(input_value) == expected


def test_dict_key(py_and_json: PyAndJson):
    v = py_and_json(
        core_schema.dict_schema(
            core_schema.json_schema(core_schema.tuple_positional_schema(core_schema.int_schema())),
            core_schema.int_schema(),
        )
    )
    assert v.validate_test({'[1]': 4}) == {(1,): 4}
    with pytest.raises(ValidationError) as exc_info:
        v.validate_test({'x': 4})
    # insert_assert(exc_info.value.errors())
    assert exc_info.value.errors() == [
        {
            'type': 'json_invalid',
            'loc': ('x', '[key]'),
            'msg': 'Invalid JSON: expected value at line 1 column 1',
            'input': 'x',
            'ctx': {'error': 'expected value at line 1 column 1'},
        }
    ]


def test_ask():
    class MyModel:
        # this is not required, but it avoids `__fields_set__` being included in `__dict__`
        __slots__ = '__dict__', '__fields_set__'
        field_a: str
        field_b: int

    v = SchemaValidator(
        {
            'type': 'model',
            'cls': MyModel,
            'schema': {
                'type': 'json',
                'schema': {
                    'type': 'typed-dict',
                    'return_fields_set': True,
                    'extra_behavior': 'forbid',
                    'fields': {'field_a': {'schema': {'type': 'str'}}, 'field_b': {'schema': {'type': 'int'}}},
                },
            },
        }
    )
    assert 'expect_fields_set:true' in plain_repr(v)
    m = v.validate_python('{"field_a": "test", "field_b": 12}')
    assert isinstance(m, MyModel)
    assert m.field_a == 'test'
    assert m.field_b == 12
    assert m.__fields_set__ == {'field_a', 'field_b'}
    with pytest.raises(ValidationError) as exc_info:
        v.validate_python('{"field_c": "wrong"}')
    # insert_assert(exc_info.value.errors())
    assert exc_info.value.errors() == [
        {'type': 'missing', 'loc': ('field_a',), 'msg': 'Field required', 'input': {'field_c': 'wrong'}},
        {'type': 'missing', 'loc': ('field_b',), 'msg': 'Field required', 'input': {'field_c': 'wrong'}},
        {'type': 'extra_forbidden', 'loc': ('field_c',), 'msg': 'Extra inputs are not permitted', 'input': 'wrong'},
    ]


def test_any_schema_no_schema():
    v = SchemaValidator(core_schema.json_schema())
    assert 'validator:None' in plain_repr(v)
    v = SchemaValidator(core_schema.json_schema(core_schema.any_schema()))
    assert 'validator:None' in plain_repr(v)
    v = SchemaValidator(core_schema.json_schema(core_schema.int_schema()))
    assert 'validator:Some(' in plain_repr(v)
