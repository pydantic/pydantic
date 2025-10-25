import math
import os
import re
import sys
from collections.abc import Mapping
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Union

import pytest
from dirty_equals import FunctionCheck, HasRepr, IsStr
from pydantic_core import CoreConfig, SchemaError, SchemaValidator, ValidationError, core_schema
from pydantic_core.core_schema import ExtraBehavior

from ..conftest import Err, PyAndJson


class Cls:
    def __init__(self, **attributes):
        for k, v in attributes.items():
            setattr(self, k, v)

    def __repr__(self):
        return 'Cls({})'.format(', '.join(f'{k}={v!r}' for k, v in self.__dict__.items()))


class Map(Mapping):
    def __init__(self, **kwargs):
        self._d = kwargs

    def __iter__(self):
        return iter(self._d)

    def __len__(self) -> int:
        return len(self._d)

    def __getitem__(self, k, /):
        return self._d[k]

    def __repr__(self):
        return 'Map({})'.format(', '.join(f'{k}={v!r}' for k, v in self._d.items()))


def test_simple():
    v = SchemaValidator(
        core_schema.model_fields_schema(
            fields={
                'field_a': core_schema.model_field(schema=core_schema.str_schema()),
                'field_b': core_schema.model_field(schema=core_schema.int_schema()),
            }
        )
    )

    assert v.validate_python({'field_a': b'abc', 'field_b': 1}) == (
        {'field_a': 'abc', 'field_b': 1},
        None,
        {'field_a', 'field_b'},
    )


def test_strict():
    v = SchemaValidator(
        {
            'type': 'model-fields',
            'fields': {
                'field_a': {'type': 'model-field', 'schema': {'type': 'str'}},
                'field_b': {'type': 'model-field', 'schema': {'type': 'int'}},
            },
        },
        CoreConfig(strict=True),
    )

    assert v.validate_python({'field_a': 'hello', 'field_b': 12}) == (
        {'field_a': 'hello', 'field_b': 12},
        None,
        {'field_a', 'field_b'},
    )

    with pytest.raises(ValidationError) as exc_info:
        assert v.validate_python({'field_a': 123, 'field_b': '123'})
    assert exc_info.value.errors(include_url=False) == [
        {'type': 'string_type', 'loc': ('field_a',), 'msg': 'Input should be a valid string', 'input': 123},
        {'type': 'int_type', 'loc': ('field_b',), 'msg': 'Input should be a valid integer', 'input': '123'},
    ]


def test_with_default():
    v = SchemaValidator(
        core_schema.model_fields_schema(
            fields={
                'field_a': core_schema.model_field(schema=core_schema.str_schema()),
                'field_b': core_schema.model_field(
                    schema=core_schema.with_default_schema(schema=core_schema.int_schema(), default=666)
                ),
            }
        )
    )

    assert v.validate_python({'field_a': b'abc'}) == ({'field_a': 'abc', 'field_b': 666}, None, {'field_a'})
    assert v.validate_python({'field_a': b'abc', 'field_b': 1}) == (
        {'field_a': 'abc', 'field_b': 1},
        None,
        {'field_b', 'field_a'},
    )


def test_missing_error(pydantic_version):
    v = SchemaValidator(
        core_schema.model_fields_schema(
            fields={
                'field_a': core_schema.model_field(schema=core_schema.str_schema()),
                'field_b': core_schema.model_field(schema=core_schema.int_schema()),
            }
        )
    )
    with pytest.raises(ValidationError) as exc_info:
        v.validate_python({'field_a': b'abc'})
    assert (
        str(exc_info.value)
        == """\
1 validation error for model-fields
field_b
  Field required [type=missing, input_value={'field_a': b'abc'}, input_type=dict]"""
        + (
            f'\n    For further information visit https://errors.pydantic.dev/{pydantic_version}/v/missing'
            if os.environ.get('PYDANTIC_ERRORS_INCLUDE_URL', '1') != 'false'
            else ''
        )
    )


@pytest.mark.parametrize(
    'config,input_value,expected',
    [
        ({}, {'a': '123'}, ({'a': 123, 'b': 4.2}, None, {'a'})),
        ({}, Map(a=123), ({'a': 123, 'b': 4.2}, None, {'a'})),
        ({}, {b'a': '123'}, Err('Field required [type=missing,')),
        ({}, {'a': '123', 'c': 4}, ({'a': 123, 'b': 4.2}, None, {'a'})),
        (CoreConfig(extra_fields_behavior='allow'), {'a': '123', 'c': 4}, ({'a': 123, 'b': 4.2}, {'c': 4}, {'a', 'c'})),
        (
            CoreConfig(extra_fields_behavior='allow'),
            {'a': '123', b'c': 4},
            Err('Keys should be strings [type=invalid_key,'),
        ),
        (
            CoreConfig(strict=True),
            Map(a=123),
            Err('Input should be a valid dictionary or instance of Model [type=model_type,'),
        ),
        ({}, {'a': '123', 'b': '4.7'}, ({'a': 123, 'b': 4.7}, None, {'a', 'b'})),
        ({}, {'a': '123', 'b': 'nan'}, ({'a': 123, 'b': FunctionCheck(math.isnan)}, None, {'a', 'b'})),
        (
            CoreConfig(allow_inf_nan=False),
            {'a': '123', 'b': 'nan'},
            Err('Input should be a finite number [type=finite_number,'),
        ),
    ],
    ids=repr,
)
def test_config(config: CoreConfig, input_value, expected):
    v = SchemaValidator(
        core_schema.model_fields_schema(
            fields={
                'a': core_schema.model_field(schema=core_schema.int_schema()),
                'b': core_schema.model_field(
                    schema=core_schema.with_default_schema(schema=core_schema.float_schema(), default=4.2)
                ),
            }
        ),
        config=config,
    )
    if isinstance(expected, Err):
        with pytest.raises(ValidationError, match=re.escape(expected.message)):
            val = v.validate_python(input_value)
            print(f'UNEXPECTED OUTPUT: {val!r}')
    else:
        result = v.validate_python(input_value)
        assert result == expected


def test_ignore_extra():
    v = SchemaValidator(
        core_schema.model_fields_schema(
            fields={
                'field_a': core_schema.model_field(schema=core_schema.str_schema()),
                'field_b': core_schema.model_field(schema=core_schema.int_schema()),
            }
        )
    )

    assert v.validate_python({'field_a': b'123', 'field_b': 1, 'field_c': 123}) == (
        {'field_a': '123', 'field_b': 1},
        None,
        {'field_b', 'field_a'},
    )


def test_forbid_extra():
    v = SchemaValidator(
        core_schema.model_fields_schema(
            fields={'field_a': core_schema.model_field(schema=core_schema.str_schema())}, extra_behavior='forbid'
        )
    )

    with pytest.raises(ValidationError) as exc_info:
        v.validate_python({'field_a': 'abc', 'field_b': 1})

    assert exc_info.value.errors(include_url=False) == [
        {'type': 'extra_forbidden', 'loc': ('field_b',), 'msg': 'Extra inputs are not permitted', 'input': 1}
    ]


def test_allow_extra_invalid():
    with pytest.raises(SchemaError, match='extras_schema can only be used if extra_behavior=allow'):
        SchemaValidator(
            schema=core_schema.model_fields_schema(
                fields={}, extras_schema=core_schema.int_schema(), extra_behavior='ignore'
            )
        )

    with pytest.raises(SchemaError, match='extras_keys_schema can only be used if extra_behavior=allow'):
        SchemaValidator(
            schema=core_schema.model_fields_schema(
                fields={}, extras_keys_schema=core_schema.int_schema(), extra_behavior='ignore'
            )
        )


def test_allow_extra_wrong():
    with pytest.raises(SchemaError, match='Invalid extra_behavior: `wrong`'):
        SchemaValidator(
            schema=core_schema.model_fields_schema(fields={}), config=CoreConfig(extra_fields_behavior='wrong')
        )


def test_allow_extra_fn_override_wrong():
    v = SchemaValidator(schema=core_schema.model_fields_schema(fields={}))
    with pytest.raises(ValueError, match='Invalid extra_behavior: `wrong`'):
        v.validate_python({}, extra='wrong')


def test_str_config():
    v = SchemaValidator(
        core_schema.model_fields_schema(fields={'field_a': core_schema.model_field(schema=core_schema.str_schema())}),
        config=CoreConfig(str_max_length=5),
    )
    assert v.validate_python({'field_a': 'test'}) == ({'field_a': 'test'}, None, {'field_a'})

    with pytest.raises(ValidationError, match='String should have at most 5 characters'):
        v.validate_python({'field_a': 'test long'})


def test_validate_assignment():
    v = SchemaValidator(
        core_schema.model_fields_schema(fields={'field_a': core_schema.model_field(schema=core_schema.str_schema())})
    )

    assert v.validate_python({'field_a': 'test'}) == ({'field_a': 'test'}, None, {'field_a'})

    data = {'field_a': 'test'}
    assert v.validate_assignment(data, 'field_a', b'abc') == ({'field_a': 'abc'}, None, {'field_a'})
    assert data == {'field_a': 'abc'}


def test_validate_assignment_strict_field():
    v = SchemaValidator(
        core_schema.model_fields_schema(
            fields={'field_a': core_schema.model_field(schema=core_schema.str_schema(strict=True))}
        )
    )

    assert v.validate_python({'field_a': 'test'}) == ({'field_a': 'test'}, None, {'field_a'})

    with pytest.raises(ValidationError) as exc_info:
        v.validate_assignment({'field_a': 'test'}, 'field_a', b'abc')
    assert exc_info.value.errors(include_url=False) == [
        {'input': b'abc', 'type': 'string_type', 'loc': ('field_a',), 'msg': 'Input should be a valid string'}
    ]


def test_validate_assignment_functions():
    calls: list[Any] = []

    def func_a(input_value, info):
        calls.append(('func_a', input_value))
        return input_value * 2

    def func_b(input_value, info):
        calls.append(('func_b', input_value))
        return input_value / 2

    v = SchemaValidator(
        core_schema.model_fields_schema(
            fields={
                'field_a': core_schema.model_field(
                    schema={
                        'type': 'function-after',
                        'function': {'type': 'with-info', 'function': func_a},
                        'schema': core_schema.str_schema(),
                    }
                ),
                'field_b': core_schema.model_field(
                    schema={
                        'type': 'function-after',
                        'function': {'type': 'with-info', 'function': func_b},
                        'schema': core_schema.int_schema(),
                    }
                ),
            }
        )
    )

    assert v.validate_python({'field_a': 'test', 'field_b': 12.0}) == (
        {'field_a': 'testtest', 'field_b': 6},
        None,
        {'field_a', 'field_b'},
    )

    assert calls == [('func_a', 'test'), ('func_b', 12)]
    calls.clear()

    assert v.validate_assignment({'field_a': 'testtest', 'field_b': 6}, 'field_a', 'new-val') == (
        {'field_a': 'new-valnew-val', 'field_b': 6},
        None,
        {'field_a'},
    )
    assert calls == [('func_a', 'new-val')]


def test_validate_assignment_ignore_extra():
    v = SchemaValidator(
        core_schema.model_fields_schema(fields={'field_a': core_schema.model_field(schema=core_schema.str_schema())})
    )

    assert v.validate_python({'field_a': 'test'}) == ({'field_a': 'test'}, None, {'field_a'})

    with pytest.raises(ValidationError) as exc_info:
        v.validate_assignment({'field_a': 'test'}, 'other_field', 456)

    # insert_assert(exc_info.value.errors(include_url=False))
    assert exc_info.value.errors(include_url=False) == [
        {
            'type': 'no_such_attribute',
            'loc': ('other_field',),
            'msg': "Object has no attribute 'other_field'",
            'input': 456,
            'ctx': {'attribute': 'other_field'},
        }
    ]


def test_validate_assignment_allow_extra():
    v = SchemaValidator(
        core_schema.model_fields_schema(
            fields={'field_a': core_schema.model_field(schema=core_schema.str_schema())}, extra_behavior='allow'
        )
    )

    assert v.validate_python({'field_a': 'test'}) == ({'field_a': 'test'}, {}, {'field_a'})

    assert v.validate_assignment({'field_a': 'test'}, 'other_field', 456) == (
        {'field_a': 'test'},
        {'other_field': 456},
        {'other_field'},
    )


def test_validate_assignment_allow_extra_validate():
    v = SchemaValidator(
        core_schema.model_fields_schema(
            fields={'field_a': core_schema.model_field(schema=core_schema.str_schema())},
            extras_schema=core_schema.int_schema(),
            extra_behavior='allow',
        )
    )

    assert v.validate_assignment({'field_a': 'test'}, 'other_field', '456') == (
        {'field_a': 'test'},
        {'other_field': 456},
        {'other_field'},
    )

    with pytest.raises(ValidationError) as exc_info:
        assert v.validate_assignment({'field_a': 'test'}, 'other_field', 'xyz')
    assert exc_info.value.errors(include_url=False) == [
        {
            'type': 'int_parsing',
            'loc': ('other_field',),
            'msg': 'Input should be a valid integer, unable to parse string as an integer',
            'input': 'xyz',
        }
    ]


def test_validate_assignment_with_strict():
    v = SchemaValidator(
        core_schema.model_fields_schema(
            fields={
                'x': core_schema.model_field(schema=core_schema.str_schema()),
                'y': core_schema.model_field(schema=core_schema.int_schema()),
            }
        )
    )

    r, model_extra, fields_set = v.validate_python({'x': 'a', 'y': '123'})
    assert r == {'x': 'a', 'y': 123}
    assert model_extra is None
    assert fields_set == {'x', 'y'}

    v.validate_assignment(r, 'y', '124')
    assert r == {'x': 'a', 'y': 124}

    with pytest.raises(ValidationError) as exc_info:
        v.validate_assignment(r, 'y', '124', strict=True)

    assert exc_info.value.errors(include_url=False) == [
        {'type': 'int_type', 'loc': ('y',), 'msg': 'Input should be a valid integer', 'input': '124'}
    ]


def test_json_error():
    v = SchemaValidator(
        core_schema.model_fields_schema(
            fields={
                'field_a': core_schema.model_field(
                    schema=core_schema.list_schema(items_schema=core_schema.int_schema())
                )
            }
        )
    )
    with pytest.raises(ValidationError) as exc_info:
        v.validate_json('{"field_a": [123, "wrong"]}')

    assert exc_info.value.errors(include_url=False) == [
        {
            'type': 'int_parsing',
            'loc': ('field_a', 1),
            'msg': 'Input should be a valid integer, unable to parse string as an integer',
            'input': 'wrong',
        }
    ]


def test_fields_required_by_default():
    """By default all fields should be required"""
    v = SchemaValidator(
        core_schema.model_fields_schema(
            fields={
                'x': core_schema.model_field(schema=core_schema.str_schema()),
                'y': core_schema.model_field(schema=core_schema.str_schema()),
            }
        )
    )

    assert v.validate_python({'x': 'pika', 'y': 'chu'}) == ({'x': 'pika', 'y': 'chu'}, None, {'x', 'y'})

    with pytest.raises(ValidationError) as exc_info:
        assert v.validate_python({'x': 'pika'})

    assert exc_info.value.errors(include_url=False) == [
        {'type': 'missing', 'loc': ('y',), 'msg': 'Field required', 'input': {'x': 'pika'}}
    ]


def test_fields_required_by_default_with_default():
    v = SchemaValidator(
        core_schema.model_fields_schema(
            fields={
                'x': core_schema.model_field(schema=core_schema.str_schema()),
                'y': core_schema.model_field(
                    schema=core_schema.with_default_schema(schema=core_schema.str_schema(), default='bulbi')
                ),
            }
        )
    )

    assert v.validate_python({'x': 'pika', 'y': 'chu'}) == ({'x': 'pika', 'y': 'chu'}, None, {'x', 'y'})
    assert v.validate_python({'x': 'pika'}) == ({'x': 'pika', 'y': 'bulbi'}, None, {'x'})


def test_alias(py_and_json: PyAndJson):
    v = py_and_json(
        {
            'type': 'model-fields',
            'fields': {'field_a': {'validation_alias': 'FieldA', 'type': 'model-field', 'schema': {'type': 'int'}}},
        }
    )
    assert v.validate_test({'FieldA': '123'}) == ({'field_a': 123}, None, {'field_a'})
    with pytest.raises(ValidationError, match=r'FieldA\n +Field required \[type=missing,'):
        assert v.validate_test({'foobar': '123'})
    with pytest.raises(ValidationError, match=r'FieldA\n +Field required \[type=missing,'):
        assert v.validate_test({'field_a': '123'})


def test_empty_string_field_name(py_and_json: PyAndJson):
    v = py_and_json({'type': 'model-fields', 'fields': {'': {'type': 'model-field', 'schema': {'type': 'int'}}}})
    assert v.validate_test({'': 123}) == ({'': 123}, None, {''})


def test_empty_string_aliases(py_and_json: PyAndJson):
    v = py_and_json(
        {
            'type': 'model-fields',
            'fields': {'field_a': {'validation_alias': '', 'type': 'model-field', 'schema': {'type': 'int'}}},
        }
    )
    assert v.validate_test({'': 123}) == ({'field_a': 123}, None, {'field_a'})

    v = py_and_json(
        {
            'type': 'model-fields',
            'fields': {'field_a': {'validation_alias': ['', ''], 'type': 'model-field', 'schema': {'type': 'int'}}},
        }
    )
    assert v.validate_test({'': {'': 123}}) == ({'field_a': 123}, None, {'field_a'})


def test_alias_allow_pop(py_and_json: PyAndJson):
    v = py_and_json(
        {
            'type': 'model-fields',
            'fields': {'field_a': {'validation_alias': 'FieldA', 'type': 'model-field', 'schema': {'type': 'int'}}},
        },
        config=CoreConfig(validate_by_name=True),
    )
    assert v.validate_test({'FieldA': '123'}) == ({'field_a': 123}, None, {'field_a'})
    assert v.validate_test({'field_a': '123'}) == ({'field_a': 123}, None, {'field_a'})
    assert v.validate_test({'FieldA': '1', 'field_a': '2'}) == ({'field_a': 1}, None, {'field_a'})
    with pytest.raises(ValidationError, match=r'FieldA\n +Field required \[type=missing,'):
        assert v.validate_test({'foobar': '123'})


def test_only_validate_by_name(py_and_json) -> None:
    v = py_and_json(
        {
            'type': 'model-fields',
            'fields': {'field_a': {'validation_alias': 'FieldA', 'type': 'model-field', 'schema': {'type': 'int'}}},
        },
        config=CoreConfig(validate_by_name=True, validate_by_alias=False),
    )
    assert v.validate_test({'field_a': '123'}) == ({'field_a': 123}, None, {'field_a'})
    with pytest.raises(ValidationError, match=r'field_a\n +Field required \[type=missing,'):
        assert v.validate_test({'FieldA': '123'})


def test_only_allow_alias(py_and_json) -> None:
    v = py_and_json(
        {
            'type': 'model-fields',
            'fields': {'field_a': {'validation_alias': 'FieldA', 'type': 'model-field', 'schema': {'type': 'int'}}},
        },
        config=CoreConfig(validate_by_name=False, validate_by_alias=True),
    )
    assert v.validate_test({'FieldA': '123'}) == ({'field_a': 123}, None, {'field_a'})
    with pytest.raises(ValidationError, match=r'FieldA\n +Field required \[type=missing,'):
        assert v.validate_test({'field_a': '123'})


@pytest.mark.parametrize(
    'input_value,expected',
    [
        ({'foo': {'bar': '123'}}, ({'field_a': 123}, None, {'field_a'})),
        ({'x': '123'}, Err(r'foo.bar\n +Field required \[type=missing,')),
        ({'foo': '123'}, Err(r'foo.bar\n +Field required \[type=missing,')),
        ({'foo': [1, 2, 3]}, Err(r'foo.bar\n +Field required \[type=missing,')),
        ({'foo': {'bat': '123'}}, Err(r'foo.bar\n +Field required \[type=missing,')),
    ],
    ids=repr,
)
def test_alias_path(py_and_json: PyAndJson, input_value, expected):
    v = py_and_json(
        {
            'type': 'model-fields',
            'fields': {
                'field_a': {'validation_alias': ['foo', 'bar'], 'type': 'model-field', 'schema': {'type': 'int'}}
            },
        }
    )
    if isinstance(expected, Err):
        with pytest.raises(ValidationError, match=expected.message):
            v.validate_test(input_value)
    else:
        output = v.validate_test(input_value)
        assert output == expected


@pytest.mark.parametrize(
    'input_value,expected',
    [
        ({'foo': {'bar': {'bat': '123'}}}, ({'field_a': 123}, None, {'field_a'})),
        ({'foo': [1, 2, 3, 4]}, ({'field_a': 4}, None, {'field_a'})),
        ({'foo': (1, 2, 3, 4)}, ({'field_a': 4}, None, {'field_a'})),
        ({'spam': 5}, ({'field_a': 5}, None, {'field_a'})),
        ({'spam': 1, 'foo': {'bar': {'bat': 2}}}, ({'field_a': 2}, None, {'field_a'})),
        ({'foo': {'x': 2}}, Err(r'field_a\n +Field required \[type=missing,')),
        ({'x': '123'}, Err(r'field_a\n +Field required \[type=missing,')),
        ({'x': {2: 33}}, Err(r'field_a\n +Field required \[type=missing,')),
        ({'foo': '01234'}, Err(r'field_a\n +Field required \[type=missing,')),
        ({'foo': [1]}, Err(r'field_a\n +Field required \[type=missing,')),
    ],
    ids=repr,
)
def test_aliases_path_multiple(py_and_json: PyAndJson, input_value, expected):
    v = py_and_json(
        {
            'type': 'model-fields',
            'fields': {
                'field_a': {
                    'validation_alias': [['foo', 'bar', 'bat'], ['foo', 3], ['spam']],
                    'type': 'model-field',
                    'schema': {'type': 'int'},
                }
            },
        },
        {'loc_by_alias': False},
    )
    if isinstance(expected, Err):
        with pytest.raises(ValidationError, match=expected.message):
            val = v.validate_test(input_value)
            print(f'UNEXPECTED OUTPUT: {val!r}')
    else:
        output = v.validate_test(input_value)
        assert output == expected


@pytest.mark.parametrize(
    'input_value,expected',
    [
        ({'foo': {-2: '123'}}, ({'field_a': 123}, None, {'field_a'})),
        # negatives indexes work fine
        ({'foo': [1, 42, 'xx']}, ({'field_a': 42}, None, {'field_a'})),
        ({'foo': [42, 'xxx', 42]}, Err(r'Input should be a valid integer,')),
        ({'foo': [42]}, Err(r'field_a\n +Field required \[type=missing,')),
        ({'foo': {'xx': '123'}}, Err(r'field_a\n +Field required \[type=missing,')),
        ({'foo': {'-2': '123'}}, Err(r'field_a\n +Field required \[type=missing,')),
        ({'foo': {2: '123'}}, Err(r'field_a\n +Field required \[type=missing,')),
        ({'foo': 'foobar'}, Err(r'field_a\n +Field required \[type=missing,')),
        ({'foo': {0, 1, 2}}, Err(r'field_a\n +Field required \[type=missing,')),
    ],
    ids=repr,
)
def test_aliases_path_negative(input_value, expected):
    v = SchemaValidator(
        core_schema.model_fields_schema(
            fields={'field_a': core_schema.model_field(validation_alias=['foo', -2], schema=core_schema.int_schema())}
        ),
        config=CoreConfig(loc_by_alias=False),
    )
    if isinstance(expected, Err):
        with pytest.raises(ValidationError, match=expected.message):
            val = v.validate_python(input_value)
            print(f'UNEXPECTED OUTPUT: {val!r}')
    else:
        output = v.validate_python(input_value)
        assert output == expected


@pytest.mark.parametrize(
    'input_value,expected',
    [
        ({'foo': [1, 42, 'xx']}, ({'field_a': 42}, None, {'field_a'})),
        ({'foo': [42, 'xxx', 42]}, Err(r'Input should be a valid integer,')),
        ({'foo': [42]}, Err(r'foo.-2\n +Field required \[type=missing,')),
    ],
    ids=repr,
)
def test_aliases_path_negative_json(py_and_json: PyAndJson, input_value, expected):
    v = py_and_json(
        {
            'type': 'model-fields',
            'fields': {'field_a': {'validation_alias': ['foo', -2], 'type': 'model-field', 'schema': {'type': 'int'}}},
        }
    )
    if isinstance(expected, Err):
        with pytest.raises(ValidationError, match=expected.message):
            val = v.validate_test(input_value)
            print(f'UNEXPECTED OUTPUT: {val!r}')
    else:
        output = v.validate_test(input_value)
        assert output == expected


def test_aliases_debug():
    v = SchemaValidator(
        core_schema.model_fields_schema(
            fields={
                'field_a': core_schema.model_field(
                    validation_alias=[['foo', 'bar', 'bat'], ['foo', 3]], schema=core_schema.int_schema()
                )
            }
        )
    )
    print(repr(v))
    assert repr(v).startswith('SchemaValidator(title="model-fields", validator=ModelFields(')
    assert 'PathChoices(' in repr(v)


def get_int_key():
    v = SchemaValidator(
        core_schema.model_fields_schema(
            fields={
                'field_a': core_schema.model_field(
                    validation_alias=[['foo', 3], ['spam']], schema=core_schema.int_schema()
                )
            }
        )
    )
    assert v.validate_python({'foo': {3: 33}}) == ({'field_a': 33}, {}, {'field_a'})


class GetItemThing:
    def __getitem__(self, v):
        assert v == 'foo'
        return 321


def get_custom_getitem():
    v = SchemaValidator(
        core_schema.model_fields_schema(
            fields={'field_a': core_schema.model_field(validation_alias=['foo'], schema=core_schema.int_schema())}
        )
    )
    assert v.validate_python(GetItemThing()) == ({'field_a': 321}, {}, {'field_a'})
    assert v.validate_python({'bar': GetItemThing()}) == ({'field_a': 321}, {}, {'field_a'})


@pytest.mark.parametrize('input_value', [{'foo': {'bar': 42}}, {'foo': 42}, {'field_a': 42}], ids=repr)
def test_paths_allow_by_name(py_and_json: PyAndJson, input_value):
    v = py_and_json(
        {
            'type': 'model-fields',
            'fields': {
                'field_a': {
                    'validation_alias': [['foo', 'bar'], ['foo']],
                    'type': 'model-field',
                    'schema': {'type': 'int'},
                }
            },
        },
        config=CoreConfig(validate_by_name=True),
    )
    assert v.validate_test(input_value) == ({'field_a': 42}, None, {'field_a'})


@pytest.mark.parametrize(
    'alias_schema,error',
    [
        ({'validation_alias': []}, 'Lookup paths should have at least one element'),
        ({'validation_alias': [[]]}, 'Each alias path should have at least one element'),
        ({'validation_alias': [123]}, "TypeError: 'int' object cannot be converted to 'PyList'"),
        ({'validation_alias': [[1, 'foo']]}, 'TypeError: The first item in an alias path should be a string'),
    ],
    ids=repr,
)
def test_alias_build_error(alias_schema, error):
    with pytest.raises(SchemaError, match=error):
        SchemaValidator(
            schema={
                'type': 'model-fields',
                'fields': {'field_a': {'type': 'model-field', 'schema': {'type': 'int'}, **alias_schema}},
            }
        )


def test_alias_error_loc_alias(py_and_json: PyAndJson):
    v = py_and_json(
        {
            'type': 'model-fields',
            'fields': {
                'field_a': {
                    'type': 'model-field',
                    'schema': {'type': 'int'},
                    'validation_alias': [['foo', 'x'], ['bar', 1, -1]],
                }
            },
        },
        {'loc_by_alias': True},  # this is the default
    )
    assert v.validate_test({'foo': {'x': 42}}) == ({'field_a': 42}, None, {'field_a'})
    assert v.validate_python({'bar': ['x', {-1: 42}]}) == ({'field_a': 42}, None, {'field_a'})
    assert v.validate_test({'bar': ['x', [1, 2, 42]]}) == ({'field_a': 42}, None, {'field_a'})
    with pytest.raises(ValidationError) as exc_info:
        v.validate_test({'foo': {'x': 'not_int'}})
    # insert_assert(exc_info.value.errors(include_url=False))
    assert exc_info.value.errors(include_url=False) == [
        {
            'type': 'int_parsing',
            'loc': ('foo', 'x'),
            'msg': 'Input should be a valid integer, unable to parse string as an integer',
            'input': 'not_int',
        }
    ]
    with pytest.raises(ValidationError) as exc_info:
        v.validate_test({'bar': ['x', [1, 2, 'not_int']]})
    # insert_assert(exc_info.value.errors(include_url=False))
    assert exc_info.value.errors(include_url=False) == [
        {
            'type': 'int_parsing',
            'loc': ('bar', 1, -1),
            'msg': 'Input should be a valid integer, unable to parse string as an integer',
            'input': 'not_int',
        }
    ]
    with pytest.raises(ValidationError) as exc_info:
        v.validate_test({})
    # insert_assert(exc_info.value.errors(include_url=False))
    assert exc_info.value.errors(include_url=False) == [
        {'type': 'missing', 'loc': ('foo', 'x'), 'msg': 'Field required', 'input': {}}
    ]


def test_alias_error_loc_field_names(py_and_json: PyAndJson):
    v = py_and_json(
        {
            'type': 'model-fields',
            'fields': {
                'field_a': {
                    'type': 'model-field',
                    'schema': {'type': 'int'},
                    'validation_alias': [['foo'], ['bar', 1, -1]],
                }
            },
        },
        {'loc_by_alias': False},
    )
    assert v.validate_test({'foo': 42}) == ({'field_a': 42}, None, {'field_a'})
    assert v.validate_test({'bar': ['x', [1, 2, 42]]}) == ({'field_a': 42}, None, {'field_a'})
    with pytest.raises(ValidationError) as exc_info:
        v.validate_test({'foo': 'not_int'})
    # insert_assert(exc_info.value.errors(include_url=False))
    assert exc_info.value.errors(include_url=False) == [
        {
            'type': 'int_parsing',
            'loc': ('field_a',),
            'msg': 'Input should be a valid integer, unable to parse string as an integer',
            'input': 'not_int',
        }
    ]
    with pytest.raises(ValidationError) as exc_info:
        v.validate_test({'bar': ['x', [1, 2, 'not_int']]})
    # insert_assert(exc_info.value.errors(include_url=False))
    assert exc_info.value.errors(include_url=False) == [
        {
            'type': 'int_parsing',
            'loc': ('field_a',),
            'msg': 'Input should be a valid integer, unable to parse string as an integer',
            'input': 'not_int',
        }
    ]
    with pytest.raises(ValidationError) as exc_info:
        v.validate_test({})
    # insert_assert(exc_info.value.errors(include_url=False))
    assert exc_info.value.errors(include_url=False) == [
        {'type': 'missing', 'loc': ('field_a',), 'msg': 'Field required', 'input': {}}
    ]


def test_empty_model():
    v = SchemaValidator(core_schema.model_fields_schema(fields={}))
    assert v.validate_python({}) == ({}, None, set())
    with pytest.raises(
        ValidationError, match=re.escape('Input should be a valid dictionary or instance of Model [type=model_type,')
    ):
        v.validate_python('x')


def test_model_fields_deep():
    v = SchemaValidator(
        core_schema.model_fields_schema(
            fields={
                'field_a': core_schema.model_field(schema=core_schema.str_schema()),
                'field_b': core_schema.model_field(
                    schema=core_schema.model_fields_schema(
                        fields={
                            'field_c': core_schema.model_field(schema=core_schema.str_schema()),
                            'field_d': core_schema.model_field(
                                schema=core_schema.model_fields_schema(
                                    fields={
                                        'field_e': core_schema.model_field(schema=core_schema.str_schema()),
                                        'field_f': core_schema.model_field(schema=core_schema.int_schema()),
                                    }
                                )
                            ),
                        }
                    )
                ),
            }
        )
    )
    model_dict, model_extra, fields_set = v.validate_python(
        {'field_a': '1', 'field_b': {'field_c': '2', 'field_d': {'field_e': '4', 'field_f': 4}}}
    )
    assert model_dict == {
        'field_a': '1',
        'field_b': (
            {'field_c': '2', 'field_d': ({'field_e': '4', 'field_f': 4}, None, {'field_f', 'field_e'})},
            None,
            {'field_d', 'field_c'},
        ),
    }
    assert model_extra is None
    assert fields_set == {'field_a', 'field_b'}
    with pytest.raises(ValidationError) as exc_info:
        v.validate_python({'field_a': '1', 'field_b': {'field_c': '2', 'field_d': {'field_e': '4', 'field_f': 'xx'}}})

    assert exc_info.value.errors(include_url=False) == [
        {
            'type': 'int_parsing',
            'loc': ('field_b', 'field_d', 'field_f'),
            'msg': 'Input should be a valid integer, unable to parse string as an integer',
            'input': 'xx',
        }
    ]


class ClassWithAttributes:
    def __init__(self):
        self.a = 1
        self.b = 2

    @property
    def c(self):
        return 'ham'


@dataclass
class MyDataclass:
    a: int = 1
    b: int = 2
    c: str = 'ham'


@pytest.mark.parametrize(
    'input_value,expected',
    [
        (ClassWithAttributes(), ({'a': 1, 'b': 2, 'c': 'ham'}, None, {'a', 'b', 'c'})),
        (MyDataclass(), ({'a': 1, 'b': 2, 'c': 'ham'}, None, {'a', 'b', 'c'})),
        (Cls(a=1, b=2, c='ham'), ({'a': 1, 'b': 2, 'c': 'ham'}, None, {'a', 'b', 'c'})),
        (dict(a=1, b=2, c='ham'), ({'a': 1, 'b': 2, 'c': 'ham'}, None, {'a', 'b', 'c'})),
        (Map(a=1, b=2, c='ham'), ({'a': 1, 'b': 2, 'c': 'ham'}, None, {'a', 'b', 'c'})),
        ((Cls(a=1, b=2), dict(c='ham')), ({'a': 1, 'b': 2, 'c': 'ham'}, None, {'a', 'b', 'c'})),
        ((Cls(a=1, b=2), dict(c='bacon')), ({'a': 1, 'b': 2, 'c': 'bacon'}, None, {'a', 'b', 'c'})),
        ((Cls(a=1, b=2, c='ham'), dict(c='bacon')), ({'a': 1, 'b': 2, 'c': 'bacon'}, None, {'a', 'b', 'c'})),
        ((Cls(a=1, b=2, c='ham'), dict(d='bacon')), ({'a': 1, 'b': 2, 'c': 'ham'}, None, {'a', 'b', 'c'})),
        # using type gives `__module__ == 'builtins'`
        (type('Testing', (), {}), Err('[type=model_attributes_type,')),
        (
            '123',
            Err('Input should be a valid dictionary or object to extract fields from [type=model_attributes_type,'),
        ),
        ([(1, 2)], Err('type=model_attributes_type,')),
        (((1, 2),), Err('type=model_attributes_type,')),
    ],
    ids=repr,
)
@pytest.mark.parametrize('from_attributes_mode', ['schema', 'validation'])
def test_from_attributes(input_value, expected, from_attributes_mode):
    v = SchemaValidator(
        core_schema.model_fields_schema(
            fields={
                'a': core_schema.model_field(schema=core_schema.int_schema()),
                'b': core_schema.model_field(schema=core_schema.int_schema()),
                'c': core_schema.model_field(schema=core_schema.str_schema()),
            },
            from_attributes=from_attributes_mode == 'schema',
        )
    )
    kwargs = {}
    if from_attributes_mode == 'validation':
        kwargs['from_attributes'] = True
    if isinstance(expected, Err):
        with pytest.raises(ValidationError, match=re.escape(expected.message)):
            val = v.validate_python(input_value, **kwargs)
            print(f'UNEXPECTED OUTPUT: {val!r}')
    else:
        output = v.validate_python(input_value, **kwargs)
        assert output == expected


def test_from_attributes_type_error():
    v = SchemaValidator(
        core_schema.model_fields_schema(
            fields={
                'a': core_schema.model_field(schema=core_schema.int_schema()),
                'b': core_schema.model_field(schema=core_schema.int_schema()),
                'c': core_schema.model_field(schema=core_schema.str_schema()),
            },
            from_attributes=True,
            model_name='MyModel',
        )
    )
    with pytest.raises(ValidationError) as exc_info:
        v.validate_python('123')

    assert exc_info.value.errors(include_url=False) == [
        {
            'type': 'model_attributes_type',
            'loc': (),
            'msg': 'Input should be a valid dictionary or object to extract fields from',
            'input': '123',
        }
    ]

    with pytest.raises(ValidationError) as exc_info:
        v.validate_json('123')
    # insert_assert(exc_info.value.errors())
    assert exc_info.value.errors(include_url=False) == [
        {
            'type': 'model_type',
            'loc': (),
            'msg': 'Input should be an object',
            'input': 123,
            'ctx': {'class_name': 'MyModel'},
        }
    ]


def test_from_attributes_by_name():
    v = SchemaValidator(
        core_schema.model_fields_schema(
            fields={'a': core_schema.model_field(schema=core_schema.int_schema(), validation_alias='a_alias')},
            from_attributes=True,
        ),
        config=CoreConfig(validate_by_name=True),
    )
    assert v.validate_python(Cls(a_alias=1)) == ({'a': 1}, None, {'a'})
    assert v.validate_python(Cls(a=1)) == ({'a': 1}, None, {'a'})


def test_from_attributes_override_true():
    v = SchemaValidator(
        core_schema.model_fields_schema(
            fields={'a': core_schema.model_field(schema=core_schema.int_schema())}, from_attributes=False
        )
    )
    with pytest.raises(ValidationError, match='Input should be a valid dictionary'):
        v.validate_python(Cls(a=1))
    assert v.validate_python(Cls(a=1), from_attributes=True) == ({'a': 1}, None, {'a'})

    assert v.isinstance_python(Cls(a=1), from_attributes=True) is True
    assert v.isinstance_python(Cls(a=1)) is False


def test_from_attributes_override_false():
    v = SchemaValidator(
        core_schema.model_fields_schema(
            fields={'a': core_schema.model_field(schema=core_schema.int_schema())}, from_attributes=True
        )
    )
    with pytest.raises(ValidationError, match='Input should be a valid dictionary'):
        v.validate_python(Cls(a=1), from_attributes=False)
    assert v.validate_python(Cls(a=1)) == ({'a': 1}, None, {'a'})

    assert v.isinstance_python(Cls(a=1)) is True
    assert v.isinstance_python(Cls(a=1), from_attributes=False) is False


def test_from_attributes_missing():
    class Foobar:
        def __init__(self):
            self.a = 1
            self.b = 2

    v = SchemaValidator(
        core_schema.model_fields_schema(
            fields={
                'a': core_schema.model_field(schema=core_schema.int_schema()),
                'b': core_schema.model_field(schema=core_schema.int_schema()),
                'c': core_schema.model_field(schema=core_schema.str_schema()),
            },
            from_attributes=True,
        )
    )

    with pytest.raises(ValidationError) as exc_info:
        v.validate_python(Foobar())

    assert exc_info.value.errors(include_url=False) == [
        {
            'type': 'missing',
            'loc': ('c',),
            'msg': 'Field required',
            'input': HasRepr(IsStr(regex='.+Foobar object at.+')),
        }
    ]


def test_from_attributes_error():
    class Foobar:
        def __init__(self):
            self.a = 1

        @property
        def b(self):
            raise RuntimeError('intentional error')

    v = SchemaValidator(
        core_schema.model_fields_schema(
            fields={
                'a': core_schema.model_field(schema=core_schema.int_schema()),
                'b': core_schema.model_field(schema=core_schema.int_schema()),
            },
            from_attributes=True,
        )
    )

    with pytest.raises(ValidationError) as exc_info:
        v.validate_python(Foobar())

    assert exc_info.value.errors(include_url=False) == [
        {
            'type': 'get_attribute_error',
            'loc': ('b',),
            'msg': 'Error extracting attribute: RuntimeError: intentional error',
            'input': HasRepr(IsStr(regex='.+Foobar object at.+')),
            'ctx': {'error': 'RuntimeError: intentional error'},
        }
    ]


def test_from_attributes_extra():
    def another_function(x):
        return x

    class Foobar:
        def __init__(self):
            self.a = 1
            self.b = 2
            self._private_attribute = 4

        @property
        def c(self):
            return 'ham'

        @property
        def _private_property(self):
            return 'wrong'

        @property
        def property_error(self):
            raise RuntimeError('xxx')

        def bound_method(self):
            return f'wrong {self.a}'

        @staticmethod
        def static_method():
            return 'wrong'

        # this is omitted along with the static method by the !PyFunction::is_type_of(attr) check in fields
        function_attribute = another_function

        @classmethod
        def class_method(cls):
            return 'wrong'

    @dataclass
    class MyDataclass:
        a: int = 1
        b: int = 2
        c: str = 'ham'
        _d: int = 4

    v = SchemaValidator(
        core_schema.model_fields_schema(
            fields={'a': core_schema.model_field(schema=core_schema.int_schema())},
            from_attributes=True,
            extra_behavior='allow',
        )
    )

    assert v.validate_python(Foobar()) == ({'a': 1}, {}, {'a'})
    assert v.validate_python(MyDataclass()) == ({'a': 1}, {}, {'a'})
    assert v.validate_python(Cls(a=1, b=2, c='ham')) == ({'a': 1}, {}, {'a'})
    assert v.validate_python(Cls(a=1, b=datetime(2000, 1, 1))) == ({'a': 1}, {}, {'a'})
    assert v.validate_python(Cls(a=1, b=datetime.now, c=lambda: 42)) == ({'a': 1}, {}, {'a'})


def test_from_attributes_extra_ignore_no_attributes_accessed() -> None:
    v = SchemaValidator(
        core_schema.model_fields_schema(
            fields={'a': core_schema.model_field(schema=core_schema.int_schema())},
            from_attributes=True,
            extra_behavior='ignore',
        )
    )

    accessed: list[str] = []

    class Source:
        a = 1
        b = 2

        def __getattribute__(self, name: str, /) -> Any:
            accessed.append(name)
            return super().__getattribute__(name)

    assert v.validate_python(Source()) == ({'a': 1}, None, {'a'})
    assert 'a' in accessed and 'b' not in accessed


def test_from_attributes_extra_forbid() -> None:
    class Source:
        a = 1
        b = 2

    v = SchemaValidator(
        core_schema.model_fields_schema(
            fields={'a': core_schema.model_field(schema=core_schema.int_schema())},
            from_attributes=True,
            extra_behavior='forbid',
        )
    )

    assert v.validate_python(Source()) == ({'a': 1}, None, {'a'})


def foobar():
    pass


@pytest.mark.parametrize(
    'input_value,expected',
    [
        (Cls(a=1), {'a': 1}),
        (Cls(a=datetime.now), {'a': datetime.now}),
        (Cls(a=lambda: 42), {'a': HasRepr(IsStr(regex='.+<lambda>.+'))}),
        (Cls(a=sys.path), {'a': sys.path}),
        (Cls(a=foobar), {'a': foobar}),
    ],
    ids=repr,
)
def test_from_attributes_function(input_value, expected):
    v = SchemaValidator(
        core_schema.model_fields_schema(
            fields={'a': core_schema.model_field(schema=core_schema.any_schema())}, from_attributes=True
        )
    )

    model_dict, model_extra, fields_set = v.validate_python(input_value)
    assert model_dict == expected
    assert model_extra is None
    assert fields_set == {'a'}


def test_from_attributes_error_error():
    class BadError(Exception):
        def __str__(self):
            raise RuntimeError('intentional error inside error')

    class Foobar:
        @property
        def x(self):
            raise BadError('intentional error')

    v = SchemaValidator(
        core_schema.model_fields_schema(
            fields={'x': core_schema.model_field(schema=core_schema.int_schema())}, from_attributes=True
        )
    )

    with pytest.raises(ValidationError) as exc_info:
        v.validate_python(Foobar())

    assert exc_info.value.errors(include_url=False) == [
        {
            'type': 'get_attribute_error',
            'loc': ('x',),
            'msg': IsStr(regex=r'Error extracting attribute: \S+\.<locals>\.BadError: <exception str\(\) failed>'),
            'input': HasRepr(IsStr(regex='.+Foobar object at.+')),
            'ctx': {'error': IsStr(regex=r'\S+\.<locals>\.BadError: <exception str\(\) failed>')},
        }
    ]

    class UnInitError:
        @property
        def x(self):
            raise RuntimeError

    with pytest.raises(ValidationError) as exc_info:
        v.validate_python(UnInitError())

    assert exc_info.value.errors(include_url=False) == [
        {
            'type': 'get_attribute_error',
            'loc': ('x',),
            'msg': 'Error extracting attribute: RuntimeError',
            'input': HasRepr(IsStr(regex='.+UnInitError object at.+')),
            'ctx': {'error': 'RuntimeError'},
        }
    ]


@pytest.mark.parametrize(
    'input_value,expected',
    [
        ({'foo': {'bar': {'bat': '123'}}}, {'my_field': 123}),
        (Cls(foo=Cls(bar=Cls(bat='123'))), {'my_field': 123}),
        (Cls(foo={'bar': {'bat': '123'}}), {'my_field': 123}),
        (Cls(foo=[1, 2, 3, 4]), {'my_field': 4}),
        (Cls(foo=(1, 2, 3, 4)), {'my_field': 4}),
        (Cls(spam=5), {'my_field': 5}),
        (Cls(spam=1, foo=Cls(bar=Cls(bat=2))), {'my_field': 2}),
        (Cls(x='123'), Err(r'my_field\n +Field required \[type=missing,')),
        (Cls(x={2: 33}), Err(r'my_field\n +Field required \[type=missing,')),
        (Cls(foo='01234'), Err(r'my_field\n +Field required \[type=missing,')),
        (Cls(foo=[1]), Err(r'my_field\n +Field required \[type=missing,')),
        (Cls, Err(r'Input should be a valid dictionary')),
    ],
    ids=repr,
)
def test_from_attributes_path(input_value, expected):
    v = SchemaValidator(
        core_schema.model_fields_schema(
            fields={
                'my_field': core_schema.model_field(
                    validation_alias=[['foo', 'bar', 'bat'], ['foo', 3], ['spam']], schema=core_schema.int_schema()
                )
            },
            from_attributes=True,
        ),
        config=CoreConfig(loc_by_alias=False),
    )
    if isinstance(expected, Err):
        with pytest.raises(ValidationError, match=expected.message):
            val = v.validate_python(input_value)
            print(f'UNEXPECTED OUTPUT: {val!r}')
    else:
        model_dict, model_extra, fields_set = v.validate_python(input_value)
        assert model_dict == expected
        assert model_extra is None
        assert fields_set == {'my_field'}


def test_from_attributes_path_error():
    class PropertyError:
        @property
        def foo(self):
            raise RuntimeError('intentional error')

    v = SchemaValidator(
        core_schema.model_fields_schema(
            fields={
                'my_field': core_schema.model_field(
                    validation_alias=[['foo', 'bar', 'bat'], ['foo', 3], ['spam']], schema=core_schema.int_schema()
                )
            },
            from_attributes=True,
        )
    )
    with pytest.raises(ValidationError) as exc_info:
        v.validate_python(PropertyError())

    assert exc_info.value.errors(include_url=False) == [
        {
            'type': 'get_attribute_error',
            'loc': ('my_field',),
            'msg': 'Error extracting attribute: RuntimeError: intentional error',
            'input': HasRepr(IsStr(regex='.+PropertyError object at.+')),
            'ctx': {'error': 'RuntimeError: intentional error'},
        }
    ]


def test_alias_extra(py_and_json: PyAndJson):
    v = py_and_json(
        {
            'type': 'model-fields',
            'extra_behavior': 'allow',
            'fields': {
                'field_a': {
                    'validation_alias': [['FieldA'], ['foo', 2]],
                    'type': 'model-field',
                    'schema': {'type': 'int'},
                }
            },
        },
        {'loc_by_alias': False},
    )
    assert v.validate_test({'FieldA': 1}) == ({'field_a': 1}, {}, {'field_a'})
    assert v.validate_test({'foo': [1, 2, 3]}) == ({'field_a': 3}, {}, {'field_a'})

    # used_keys should be populated either though validation fails so "FieldA" is skipped in extra
    with pytest.raises(ValidationError) as exc_info:
        assert v.validate_test({'FieldA': '...'}) == ({'field_a': 1}, {}, {'field_a'})

    assert exc_info.value.errors(include_url=False) == [
        {
            'type': 'int_parsing',
            'loc': ('field_a',),
            'msg': 'Input should be a valid integer, unable to parse string as an integer',
            'input': '...',
        }
    ]


def test_alias_extra_from_attributes():
    v = SchemaValidator(
        core_schema.model_fields_schema(
            extra_behavior='allow',
            from_attributes=True,
            fields={
                'field_a': core_schema.model_field(
                    validation_alias=[['FieldA'], ['foo', 2]], schema=core_schema.int_schema()
                )
            },
        )
    )
    assert v.validate_python({'FieldA': 1}) == ({'field_a': 1}, {}, {'field_a'})
    assert v.validate_python(Cls(FieldA=1)) == ({'field_a': 1}, {}, {'field_a'})
    assert v.validate_python(Cls(foo=[1, 2, 3])) == ({'field_a': 3}, {}, {'field_a'})
    assert v.validate_python({'foo': [1, 2, 3]}) == ({'field_a': 3}, {}, {'field_a'})


def test_alias_extra_by_name(py_and_json: PyAndJson):
    v = py_and_json(
        {
            'type': 'model-fields',
            'extra_behavior': 'allow',
            'from_attributes': True,
            'fields': {'field_a': {'validation_alias': 'FieldA', 'type': 'model-field', 'schema': {'type': 'int'}}},
        },
        config=CoreConfig(validate_by_name=True),
    )
    assert v.validate_test({'FieldA': 1}) == ({'field_a': 1}, {}, {'field_a'})
    assert v.validate_test({'field_a': 1}) == ({'field_a': 1}, {}, {'field_a'})
    assert v.validate_python(Cls(FieldA=1)) == ({'field_a': 1}, {}, {'field_a'})
    assert v.validate_python(Cls(field_a=1)) == ({'field_a': 1}, {}, {'field_a'})


def test_alias_extra_forbid(py_and_json: PyAndJson):
    v = py_and_json(
        {
            'type': 'model-fields',
            'extra_behavior': 'forbid',
            'fields': {'field_a': {'type': 'model-field', 'validation_alias': 'FieldA', 'schema': {'type': 'int'}}},
        }
    )
    assert v.validate_test({'FieldA': 1}) == ({'field_a': 1}, None, {'field_a'})


def test_with_default_factory():
    v = SchemaValidator(
        core_schema.model_fields_schema(
            fields={
                'x': core_schema.model_field(
                    schema=core_schema.with_default_schema(
                        schema=core_schema.str_schema(), default_factory=lambda: 'pikachu'
                    )
                )
            }
        )
    )

    assert v.validate_python({}) == ({'x': 'pikachu'}, None, set())
    assert v.validate_python({'x': 'bulbi'}) == ({'x': 'bulbi'}, None, {'x'})


@pytest.mark.parametrize(
    'default_factory,error_message',
    [
        (lambda: 1 + 'a', "unsupported operand type(s) for +: 'int' and 'str'"),
        (lambda x: 'a' + x, "<lambda>() missing 1 required positional argument: 'x'"),
    ],
)
def test_bad_default_factory(default_factory, error_message):
    v = SchemaValidator(
        core_schema.model_fields_schema(
            fields={
                'x': core_schema.model_field(
                    schema=core_schema.with_default_schema(
                        schema=core_schema.str_schema(), default_factory=default_factory
                    )
                )
            }
        )
    )
    with pytest.raises(TypeError, match=re.escape(error_message)):
        v.validate_python({})


class TestOnError:
    def test_on_error_bad_default(self):
        with pytest.raises(SchemaError, match="'on_error = default' requires a `default` or `default_factory`"):
            SchemaValidator(
                schema=core_schema.model_fields_schema(
                    fields={
                        'x': core_schema.model_field(
                            schema=core_schema.with_default_schema(schema=core_schema.str_schema(), on_error='default')
                        )
                    }
                )
            )

    def test_on_error_raise_by_default(self, py_and_json: PyAndJson):
        v = py_and_json({'type': 'model-fields', 'fields': {'x': {'type': 'model-field', 'schema': {'type': 'str'}}}})
        assert v.validate_test({'x': 'foo'}) == ({'x': 'foo'}, None, {'x'})
        with pytest.raises(ValidationError) as exc_info:
            v.validate_test({'x': ['foo']})
        assert exc_info.value.errors(include_url=False) == [
            {'input': ['foo'], 'type': 'string_type', 'loc': ('x',), 'msg': 'Input should be a valid string'}
        ]

    def test_on_error_raise_explicit(self, py_and_json: PyAndJson):
        v = py_and_json(
            {
                'type': 'model-fields',
                'fields': {
                    'x': {
                        'type': 'model-field',
                        'schema': {'type': 'default', 'schema': {'type': 'str'}, 'on_error': 'raise'},
                    }
                },
            }
        )
        assert v.validate_test({'x': 'foo'}) == ({'x': 'foo'}, None, {'x'})
        with pytest.raises(ValidationError) as exc_info:
            v.validate_test({'x': ['foo']})
        assert exc_info.value.errors(include_url=False) == [
            {'input': ['foo'], 'type': 'string_type', 'loc': ('x',), 'msg': 'Input should be a valid string'}
        ]

    def test_on_error_default(self, py_and_json: PyAndJson):
        v = py_and_json(
            {
                'type': 'model-fields',
                'fields': {
                    'x': {
                        'type': 'model-field',
                        'schema': {
                            'type': 'default',
                            'schema': {'type': 'str'},
                            'on_error': 'default',
                            'default': 'pika',
                        },
                    }
                },
            }
        )
        assert v.validate_test({'x': 'foo'}) == ({'x': 'foo'}, None, {'x'})
        assert v.validate_test({'x': ['foo']}) == ({'x': 'pika'}, None, {'x'})

    def test_on_error_default_factory(self, py_and_json: PyAndJson):
        v = py_and_json(
            {
                'type': 'model-fields',
                'fields': {
                    'x': {
                        'type': 'model-field',
                        'schema': {
                            'type': 'default',
                            'schema': {'type': 'str'},
                            'on_error': 'default',
                            'default_factory': lambda: 'pika',
                        },
                    }
                },
            }
        )
        assert v.validate_test({'x': 'foo'}) == ({'x': 'foo'}, None, {'x'})
        assert v.validate_test({'x': ['foo']}) == ({'x': 'pika'}, None, {'x'})

    def test_wrap_on_error(self, py_and_json: PyAndJson):
        def wrap_function(input_value, validator, info):
            try:
                return validator(input_value)
            except ValidationError:
                if isinstance(input_value, list):
                    return str(len(input_value))
                else:
                    return repr(input_value)

        v = py_and_json(
            {
                'type': 'model-fields',
                'fields': {
                    'x': {
                        'type': 'model-field',
                        'schema': {
                            'type': 'default',
                            'on_error': 'raise',
                            'schema': {
                                'type': 'function-wrap',
                                'function': {'type': 'with-info', 'function': wrap_function},
                                'schema': {'type': 'str'},
                            },
                        },
                    }
                },
            }
        )
        assert v.validate_test({'x': 'foo'}) == ({'x': 'foo'}, None, {'x'})
        assert v.validate_test({'x': ['foo']}) == ({'x': '1'}, None, {'x'})
        assert v.validate_test({'x': ['foo', 'bar']}) == ({'x': '2'}, None, {'x'})
        assert v.validate_test({'x': {'a': 'b'}}) == ({'x': "{'a': 'b'}"}, None, {'x'})


def test_frozen_field():
    v = SchemaValidator(
        core_schema.model_fields_schema(
            fields={
                'name': core_schema.model_field(schema=core_schema.str_schema()),
                'age': core_schema.model_field(schema=core_schema.int_schema()),
                'is_developer': core_schema.model_field(
                    schema=core_schema.with_default_schema(schema=core_schema.bool_schema(), default=True), frozen=True
                ),
            }
        )
    )
    r1, model_extra, fields_set = v.validate_python({'name': 'Samuel', 'age': '36'})
    assert r1 == {'name': 'Samuel', 'age': 36, 'is_developer': True}
    assert model_extra is None
    assert fields_set == {'name', 'age'}
    v.validate_assignment(r1, 'age', '35')
    assert r1 == {'name': 'Samuel', 'age': 35, 'is_developer': True}
    with pytest.raises(ValidationError) as exc_info:
        v.validate_assignment(r1, 'is_developer', False)
    assert exc_info.value.errors(include_url=False) == [
        {'type': 'frozen_field', 'loc': ('is_developer',), 'msg': 'Field is frozen', 'input': False}
    ]


@pytest.mark.parametrize(
    'config,schema_extra_behavior_kw',
    [
        (core_schema.CoreConfig(extra_fields_behavior='allow'), {}),
        (core_schema.CoreConfig(extra_fields_behavior='allow'), {'extra_behavior': None}),
        (core_schema.CoreConfig(), {'extra_behavior': 'allow'}),
        (None, {'extra_behavior': 'allow'}),
        (core_schema.CoreConfig(extra_fields_behavior='forbid'), {'extra_behavior': 'allow'}),
    ],
)
@pytest.mark.parametrize(
    'extras_schema_kw, expected_extra_value',
    [({}, '123'), ({'extras_schema': None}, '123'), ({'extras_schema': core_schema.int_schema()}, 123)],
    ids=['extras_schema=unset', 'extras_schema=None', 'extras_schema=int'],
)
def test_extra_behavior_allow(
    config: Union[core_schema.CoreConfig, None],
    schema_extra_behavior_kw: dict[str, Any],
    extras_schema_kw: dict[str, Any],
    expected_extra_value: Any,
):
    v = SchemaValidator(
        core_schema.model_fields_schema(
            {'f': core_schema.model_field(core_schema.str_schema())}, **schema_extra_behavior_kw, **extras_schema_kw
        ),
        config=config,
    )

    m, model_extra, fields_set = v.validate_python({'f': 'x', 'extra_field': '123'})
    assert m == {'f': 'x'}
    assert model_extra == {'extra_field': expected_extra_value}
    assert fields_set == {'f', 'extra_field'}

    v.validate_assignment(m, 'f', 'y')
    assert m == {'f': 'y'}

    new_m, new_model_extra, new_fields_set = v.validate_assignment({**m, **model_extra}, 'not_f', '123')
    assert new_m == {'f': 'y'}
    assert new_model_extra == {'extra_field': expected_extra_value, 'not_f': expected_extra_value}
    assert new_fields_set == {'not_f'}


# We can't test the extra parameter of the validate_* functions above, since the
# extras_schema parameter isn't valid unless the models are configured with extra='allow'.
# Test the validate_* extra parameter separately instead:
@pytest.mark.parametrize(
    'config,schema_extra_behavior_kw',
    [
        (core_schema.CoreConfig(extra_fields_behavior='forbid'), {}),
        (core_schema.CoreConfig(extra_fields_behavior='forbid'), {'extra_behavior': None}),
        (core_schema.CoreConfig(), {'extra_behavior': 'forbid'}),
        (None, {'extra_behavior': 'forbid'}),
        (core_schema.CoreConfig(extra_fields_behavior='ignore'), {'extra_behavior': 'forbid'}),
        (core_schema.CoreConfig(), {}),
        (core_schema.CoreConfig(), {'extra_behavior': None}),
        (None, {'extra_behavior': None}),
    ],
)
def test_extra_behavior_allow_with_validate_fn_override(
    config: Union[core_schema.CoreConfig, None],
    schema_extra_behavior_kw: dict[str, Any],
):
    v = SchemaValidator(
        core_schema.model_fields_schema(
            {'f': core_schema.model_field(core_schema.str_schema())}, **schema_extra_behavior_kw
        ),
        config=config,
    )

    m, model_extra, fields_set = v.validate_python({'f': 'x', 'extra_field': '123'}, extra='allow')
    assert m == {'f': 'x'}
    assert model_extra == {'extra_field': '123'}
    assert fields_set == {'f', 'extra_field'}

    v.validate_assignment(m, 'f', 'y', extra='allow')
    assert m == {'f': 'y'}

    new_m, new_model_extra, new_fields_set = v.validate_assignment({**m, **model_extra}, 'not_f', '123', extra='allow')
    assert new_m == {'f': 'y'}
    assert new_model_extra == {'extra_field': '123', 'not_f': '123'}
    assert new_fields_set == {'not_f'}


@pytest.mark.parametrize(
    'config,schema_extra_behavior_kw,validate_fn_extra_kw',
    [
        (core_schema.CoreConfig(extra_fields_behavior='forbid'), {}, None),
        (core_schema.CoreConfig(extra_fields_behavior='forbid'), {'extra_behavior': None}, None),
        (core_schema.CoreConfig(), {'extra_behavior': 'forbid'}, None),
        (None, {'extra_behavior': 'forbid'}, None),
        (core_schema.CoreConfig(extra_fields_behavior='allow'), {'extra_behavior': 'forbid'}, None),
        (core_schema.CoreConfig(extra_fields_behavior='ignore'), {}, 'forbid'),
        (core_schema.CoreConfig(extra_fields_behavior='ignore'), {'extra_behavior': None}, 'forbid'),
        (core_schema.CoreConfig(), {'extra_behavior': 'ignore'}, 'forbid'),
        (None, {'extra_behavior': 'ignore'}, 'forbid'),
        (core_schema.CoreConfig(extra_fields_behavior='allow'), {'extra_behavior': 'ignore'}, 'forbid'),
        (core_schema.CoreConfig(), {}, 'forbid'),
        (core_schema.CoreConfig(), {'extra_behavior': None}, 'forbid'),
        (None, {'extra_behavior': None}, 'forbid'),
    ],
)
def test_extra_behavior_forbid(
    config: Union[core_schema.CoreConfig, None],
    schema_extra_behavior_kw: dict[str, Any],
    validate_fn_extra_kw: Union[ExtraBehavior, None],
):
    v = SchemaValidator(
        core_schema.model_fields_schema(
            {'f': core_schema.model_field(core_schema.str_schema())}, **schema_extra_behavior_kw
        ),
        config=config,
    )

    m, model_extra, fields_set = v.validate_python({'f': 'x'}, extra=validate_fn_extra_kw)
    assert m == {'f': 'x'}
    assert fields_set == {'f'}

    with pytest.raises(ValidationError) as exc_info:
        v.validate_python({'f': 'x', 'extra_field': 123}, extra=validate_fn_extra_kw)
    assert exc_info.value.errors(include_url=False) == [
        {'type': 'extra_forbidden', 'loc': ('extra_field',), 'msg': 'Extra inputs are not permitted', 'input': 123}
    ]

    v.validate_assignment(m, 'f', 'y', extra=validate_fn_extra_kw)
    assert m['f'] == 'y'

    with pytest.raises(ValidationError) as exc_info:
        v.validate_assignment(m, 'not_f', 'xyz', extra=validate_fn_extra_kw)
    assert exc_info.value.errors(include_url=False) == [
        {
            'type': 'no_such_attribute',
            'loc': ('not_f',),
            'msg': "Object has no attribute 'not_f'",
            'input': 'xyz',
            'ctx': {'attribute': 'not_f'},
        }
    ]
    assert 'not_f' not in m


@pytest.mark.parametrize(
    'config,schema_extra_behavior_kw,validate_fn_extra_kw',
    [
        (core_schema.CoreConfig(extra_fields_behavior='ignore'), {}, None),
        (core_schema.CoreConfig(), {'extra_behavior': 'ignore'}, None),
        (None, {'extra_behavior': 'ignore'}, None),
        (core_schema.CoreConfig(extra_fields_behavior='forbid'), {'extra_behavior': 'ignore'}, None),
        (core_schema.CoreConfig(), {}, None),
        (core_schema.CoreConfig(), {'extra_behavior': None}, None),
        (None, {'extra_behavior': None}, None),
        (core_schema.CoreConfig(extra_fields_behavior='allow'), {}, 'ignore'),
        (core_schema.CoreConfig(), {'extra_behavior': 'allow'}, 'ignore'),
        (None, {'extra_behavior': 'allow'}, 'ignore'),
        (core_schema.CoreConfig(extra_fields_behavior='forbid'), {'extra_behavior': 'allow'}, 'ignore'),
    ],
)
def test_extra_behavior_ignore(
    config: Union[core_schema.CoreConfig, None],
    schema_extra_behavior_kw: dict[str, Any],
    validate_fn_extra_kw: Union[ExtraBehavior, None],
):
    v = SchemaValidator(
        core_schema.model_fields_schema(
            {'f': core_schema.model_field(core_schema.str_schema())}, **schema_extra_behavior_kw
        ),
        config=config,
    )

    m, model_extra, fields_set = v.validate_python({'f': 'x', 'extra_field': 123}, extra=validate_fn_extra_kw)
    assert m == {'f': 'x'}
    assert model_extra is None
    assert fields_set == {'f'}

    v.validate_assignment(m, 'f', 'y', extra=validate_fn_extra_kw)
    assert m['f'] == 'y'

    # even if we ignore extra attributes during initialization / validation
    # we never ignore them during assignment
    # instead if extra='ignore' was set (or nothing was set since that's the default)
    # we treat it as if it were extra='forbid'
    with pytest.raises(ValidationError) as exc_info:
        v.validate_assignment(m, 'not_f', 'xyz', extra=validate_fn_extra_kw)
    assert exc_info.value.errors(include_url=False) == [
        {
            'type': 'no_such_attribute',
            'loc': ('not_f',),
            'msg': "Object has no attribute 'not_f'",
            'input': 'xyz',
            'ctx': {'attribute': 'not_f'},
        }
    ]
    assert 'not_f' not in m


def test_extra_behavior_allow_keys_validation() -> None:
    v = SchemaValidator(
        core_schema.model_fields_schema(
            {}, extra_behavior='allow', extras_keys_schema=core_schema.str_schema(max_length=3)
        )
    )

    m, model_extra, fields_set = v.validate_python({'ext': 123})
    assert m == {}
    assert model_extra == {'ext': 123}
    assert fields_set == {'ext'}

    with pytest.raises(ValidationError) as exc_info:
        v.validate_python({'extra_too_long': 123})

    assert exc_info.value.errors()[0]['type'] == 'string_too_long'


@pytest.mark.parametrize('config_by_alias', [None, True, False])
@pytest.mark.parametrize('config_by_name', [None, True, False])
@pytest.mark.parametrize('runtime_by_alias', [None, True, False])
@pytest.mark.parametrize('runtime_by_name', [None, True, False])
def test_by_alias_and_name_config_interaction(
    config_by_alias: Union[bool, None],
    config_by_name: Union[bool, None],
    runtime_by_alias: Union[bool, None],
    runtime_by_name: Union[bool, None],
) -> None:
    """This test reflects the priority that applies for config vs runtime validation alias configuration.

    Runtime values take precedence over config values, when set.
    By default, by_alias is True and by_name is False.
    """

    if config_by_alias is False and config_by_name is False and runtime_by_alias is False and runtime_by_name is False:
        pytest.skip("Can't have both by_alias and by_name as effectively False")

    class Model:
        def __init__(self, my_field: int) -> None:
            self.my_field = my_field

    core_config = {
        **({'validate_by_alias': config_by_alias} if config_by_alias is not None else {}),
        **({'validate_by_name': config_by_name} if config_by_name is not None else {}),
    }

    schema = core_schema.model_schema(
        Model,
        core_schema.model_fields_schema(
            {
                'my_field': core_schema.model_field(core_schema.int_schema(), validation_alias='my_alias'),
            }
        ),
        config=core_schema.CoreConfig(**core_config),
    )
    s = SchemaValidator(schema)

    alias_allowed = next(x for x in (runtime_by_alias, config_by_alias, True) if x is not None)
    name_allowed = next(x for x in (runtime_by_name, config_by_name, False) if x is not None)

    if alias_allowed:
        assert s.validate_python({'my_alias': 1}, by_alias=runtime_by_alias, by_name=runtime_by_name).my_field == 1
    if name_allowed:
        assert s.validate_python({'my_field': 1}, by_alias=runtime_by_alias, by_name=runtime_by_name).my_field == 1
