import gc
import math
import platform
import re
import weakref
from typing import Any, Dict, Mapping, Union

import pytest
from dirty_equals import FunctionCheck

from pydantic_core import CoreConfig, SchemaError, SchemaValidator, ValidationError, core_schema

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

    def __getitem__(self, __k):
        return self._d[__k]

    def __repr__(self):
        return 'Map({})'.format(', '.join(f'{k}={v!r}' for k, v in self._d.items()))


def test_simple():
    v = SchemaValidator(
        {
            'type': 'typed-dict',
            'fields': {
                'field_a': {'type': 'typed-dict-field', 'schema': {'type': 'str'}},
                'field_b': {'type': 'typed-dict-field', 'schema': {'type': 'int'}},
            },
        }
    )

    assert v.validate_python({'field_a': b'abc', 'field_b': 1}) == {'field_a': 'abc', 'field_b': 1}


def test_strict():
    v = SchemaValidator(
        {
            'type': 'typed-dict',
            'fields': {
                'field_a': {'type': 'typed-dict-field', 'schema': {'type': 'str'}},
                'field_b': {'type': 'typed-dict-field', 'schema': {'type': 'int'}},
            },
            'config': {'strict': True},
        }
    )

    assert v.validate_python({'field_a': 'hello', 'field_b': 12}) == {'field_a': 'hello', 'field_b': 12}

    with pytest.raises(ValidationError) as exc_info:
        assert v.validate_python({'field_a': 123, 'field_b': '123'})
    assert exc_info.value.errors(include_url=False) == [
        {'type': 'string_type', 'loc': ('field_a',), 'msg': 'Input should be a valid string', 'input': 123},
        {'type': 'int_type', 'loc': ('field_b',), 'msg': 'Input should be a valid integer', 'input': '123'},
    ]


def test_with_default():
    v = SchemaValidator(
        {
            'type': 'typed-dict',
            'fields': {
                'field_a': {'type': 'typed-dict-field', 'schema': {'type': 'str'}},
                'field_b': {
                    'type': 'typed-dict-field',
                    'schema': {'type': 'default', 'schema': {'type': 'int'}, 'default': 666},
                },
            },
        }
    )

    assert v.validate_python({'field_a': b'abc'}) == {'field_a': 'abc', 'field_b': 666}
    assert v.validate_python({'field_a': b'abc', 'field_b': 1}) == {'field_a': 'abc', 'field_b': 1}


def test_missing_error(pydantic_version):
    v = SchemaValidator(
        {
            'type': 'typed-dict',
            'fields': {
                'field_a': {'type': 'typed-dict-field', 'schema': {'type': 'str'}},
                'field_b': {'type': 'typed-dict-field', 'schema': {'type': 'int'}},
            },
        }
    )
    with pytest.raises(ValidationError) as exc_info:
        v.validate_python({'field_a': b'abc'})
    # insert_assert(str(exc_info.value))
    assert str(exc_info.value) == (
        "1 validation error for typed-dict\n"
        "field_b\n"
        "  Field required [type=missing, input_value={'field_a': b'abc'}, input_type=dict]\n"
        f"    For further information visit https://errors.pydantic.dev/{pydantic_version}/v/missing"
    )


@pytest.mark.parametrize(
    'config,input_value,expected',
    [
        ({}, {'a': '123'}, {'a': 123}),
        ({}, Map(a=123), {'a': 123}),
        ({}, {b'a': '123'}, Err('Field required [type=missing,')),
        ({}, {'a': '123', 'c': 4}, {'a': 123}),
        ({'extra_fields_behavior': 'allow'}, {'a': '123', 'c': 4}, {'a': 123, 'c': 4}),
        ({'extra_fields_behavior': 'allow'}, {'a': '123', b'c': 4}, Err('Keys should be strings [type=invalid_key,')),
        ({'strict': True}, Map(a=123), Err('Input should be a valid dictionary [type=dict_type,')),
        ({}, {'a': '123', 'b': '4.7'}, {'a': 123, 'b': 4.7}),
        ({}, {'a': '123', 'b': 'nan'}, {'a': 123, 'b': FunctionCheck(math.isnan)}),
        (
            {'allow_inf_nan': False},
            {'a': '123', 'b': 'nan'},
            Err('Input should be a finite number [type=finite_number,'),
        ),
    ],
    ids=repr,
)
def test_config(config: CoreConfig, input_value, expected):
    v = SchemaValidator(
        {
            'type': 'typed-dict',
            'fields': {
                'a': {'type': 'typed-dict-field', 'schema': {'type': 'int'}},
                'b': {'type': 'typed-dict-field', 'schema': {'type': 'float'}, 'required': False},
            },
            'config': config,
        }
    )
    if isinstance(expected, Err):
        with pytest.raises(ValidationError, match=re.escape(expected.message)):
            val = v.validate_python(input_value)
            print(f'UNEXPECTED OUTPUT: {val!r}')
    else:
        output_dict = v.validate_python(input_value)
        assert output_dict == expected


def test_ignore_extra():
    v = SchemaValidator(
        {
            'type': 'typed-dict',
            'fields': {
                'field_a': {'type': 'typed-dict-field', 'schema': {'type': 'str'}},
                'field_b': {'type': 'typed-dict-field', 'schema': {'type': 'int'}},
            },
        }
    )

    assert v.validate_python({'field_a': b'123', 'field_b': 1, 'field_c': 123}) == {'field_a': '123', 'field_b': 1}


def test_forbid_extra():
    v = SchemaValidator(
        {
            'type': 'typed-dict',
            'fields': {'field_a': {'type': 'typed-dict-field', 'schema': {'type': 'str'}}},
            'extra_behavior': 'forbid',
        }
    )

    with pytest.raises(ValidationError) as exc_info:
        v.validate_python({'field_a': 'abc', 'field_b': 1})

    assert exc_info.value.errors(include_url=False) == [
        {'type': 'extra_forbidden', 'loc': ('field_b',), 'msg': 'Extra inputs are not permitted', 'input': 1}
    ]


def test_allow_extra_invalid():
    with pytest.raises(SchemaError, match='extras_schema can only be used if extra_behavior=allow'):
        SchemaValidator(
            {'type': 'typed-dict', 'fields': {}, 'extras_schema': {'type': 'int'}, 'extra_behavior': 'ignore'}
        )


def test_allow_extra_wrong():
    with pytest.raises(SchemaError, match="Input should be 'allow', 'forbid' or 'ignore'"):
        SchemaValidator({'type': 'typed-dict', 'fields': {}, 'config': {'extra_fields_behavior': 'wrong'}})


def test_str_config():
    v = SchemaValidator(
        {
            'type': 'typed-dict',
            'fields': {'field_a': {'type': 'typed-dict-field', 'schema': {'type': 'str'}}},
            'config': {'str_max_length': 5},
        }
    )
    assert v.validate_python({'field_a': 'test'}) == {'field_a': 'test'}

    with pytest.raises(ValidationError, match='String should have at most 5 characters'):
        v.validate_python({'field_a': 'test long'})


def test_json_error():
    v = SchemaValidator(
        {
            'type': 'typed-dict',
            'fields': {
                'field_a': {'type': 'typed-dict-field', 'schema': {'type': 'list', 'items_schema': {'type': 'int'}}}
            },
        }
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


def test_missing_schema_key():
    with pytest.raises(SchemaError, match='typed-dict.fields.x.schema\n  Field required'):
        SchemaValidator({'type': 'typed-dict', 'fields': {'x': {'type': 'str'}}})


def test_fields_required_by_default():
    """By default all fields should be required"""
    v = SchemaValidator(
        {
            'type': 'typed-dict',
            'fields': {
                'x': {'type': 'typed-dict-field', 'schema': {'type': 'str'}},
                'y': {'type': 'typed-dict-field', 'schema': {'type': 'str'}},
            },
        }
    )

    assert v.validate_python({'x': 'pika', 'y': 'chu'}) == {'x': 'pika', 'y': 'chu'}

    with pytest.raises(ValidationError) as exc_info:
        assert v.validate_python({'x': 'pika'})

    assert exc_info.value.errors(include_url=False) == [
        {'type': 'missing', 'loc': ('y',), 'msg': 'Field required', 'input': {'x': 'pika'}}
    ]


def test_fields_required_by_default_with_optional():
    v = SchemaValidator(
        {
            'type': 'typed-dict',
            'fields': {
                'x': {'type': 'typed-dict-field', 'schema': {'type': 'str'}},
                'y': {'type': 'typed-dict-field', 'schema': {'type': 'str'}, 'required': False},
            },
        }
    )

    assert v.validate_python({'x': 'pika', 'y': 'chu'}) == {'x': 'pika', 'y': 'chu'}
    assert v.validate_python({'x': 'pika'}) == {'x': 'pika'}


def test_fields_required_by_default_with_default():
    v = SchemaValidator(
        {
            'type': 'typed-dict',
            'fields': {
                'x': {'type': 'typed-dict-field', 'schema': {'type': 'str'}},
                'y': {
                    'type': 'typed-dict-field',
                    'schema': {'type': 'default', 'schema': {'type': 'str'}, 'default': 'bulbi'},
                },
            },
        }
    )

    assert v.validate_python({'x': 'pika', 'y': 'chu'}) == {'x': 'pika', 'y': 'chu'}
    assert v.validate_python({'x': 'pika'}) == {'x': 'pika', 'y': 'bulbi'}


def test_all_optional_fields():
    """By default all fields should be optional if `total` is set to `False`"""
    v = SchemaValidator(
        {
            'type': 'typed-dict',
            'total': False,
            'fields': {
                'x': {'type': 'typed-dict-field', 'schema': {'type': 'str', 'strict': True}},
                'y': {'type': 'typed-dict-field', 'schema': {'type': 'str'}},
            },
        }
    )

    assert v.validate_python({'x': 'pika', 'y': 'chu'}) == {'x': 'pika', 'y': 'chu'}
    assert v.validate_python({'x': 'pika'}) == {'x': 'pika'}
    assert v.validate_python({'y': 'chu'}) == {'y': 'chu'}

    with pytest.raises(ValidationError) as exc_info:
        assert v.validate_python({'x': 123})

    assert exc_info.value.errors(include_url=False) == [
        {'type': 'string_type', 'loc': ('x',), 'msg': 'Input should be a valid string', 'input': 123}
    ]


def test_all_optional_fields_with_required_fields():
    v = SchemaValidator(
        {
            'type': 'typed-dict',
            'total': False,
            'fields': {
                'x': {'type': 'typed-dict-field', 'schema': {'type': 'str', 'strict': True}, 'required': True},
                'y': {'type': 'typed-dict-field', 'schema': {'type': 'str'}},
            },
        }
    )

    assert v.validate_python({'x': 'pika', 'y': 'chu'}) == {'x': 'pika', 'y': 'chu'}
    assert v.validate_python({'x': 'pika'}) == {'x': 'pika'}

    with pytest.raises(ValidationError) as exc_info:
        assert v.validate_python({'y': 'chu'}) == ({'y': 'chu'}, {'y'})

    assert exc_info.value.errors(include_url=False) == [
        {'type': 'missing', 'loc': ('x',), 'msg': 'Field required', 'input': {'y': 'chu'}}
    ]


def test_field_required_and_default():
    """A field cannot be required and have a default value"""
    with pytest.raises(SchemaError, match="Field 'x': a required field cannot have a default value"):
        SchemaValidator(
            {
                'type': 'typed-dict',
                'fields': {
                    'x': {
                        'type': 'typed-dict-field',
                        'schema': {'type': 'default', 'schema': {'type': 'str'}, 'default': 'pika'},
                        'required': True,
                    }
                },
            }
        )


def test_alias(py_and_json: PyAndJson):
    v = py_and_json(
        {
            'type': 'typed-dict',
            'fields': {
                'field_a': {'validation_alias': 'FieldA', 'type': 'typed-dict-field', 'schema': {'type': 'int'}}
            },
        }
    )
    assert v.validate_test({'FieldA': '123'}) == {'field_a': 123}
    with pytest.raises(ValidationError, match=r'FieldA\n +Field required \[type=missing,'):
        assert v.validate_test({'foobar': '123'})
    with pytest.raises(ValidationError, match=r'FieldA\n +Field required \[type=missing,'):
        assert v.validate_test({'field_a': '123'})


def test_empty_string_field_name(py_and_json: PyAndJson):
    v = py_and_json({'type': 'typed-dict', 'fields': {'': {'type': 'typed-dict-field', 'schema': {'type': 'int'}}}})
    assert v.validate_test({'': 123}) == {'': 123}


def test_empty_string_aliases(py_and_json: PyAndJson):
    v = py_and_json(
        {
            'type': 'typed-dict',
            'fields': {'field_a': {'validation_alias': '', 'type': 'typed-dict-field', 'schema': {'type': 'int'}}},
        }
    )
    assert v.validate_test({'': 123}) == {'field_a': 123}

    v = py_and_json(
        {
            'type': 'typed-dict',
            'fields': {
                'field_a': {'validation_alias': ['', ''], 'type': 'typed-dict-field', 'schema': {'type': 'int'}}
            },
        }
    )
    assert v.validate_test({'': {'': 123}}) == {'field_a': 123}


def test_alias_allow_pop(py_and_json: PyAndJson):
    v = py_and_json(
        {
            'type': 'typed-dict',
            'populate_by_name': True,
            'fields': {
                'field_a': {'validation_alias': 'FieldA', 'type': 'typed-dict-field', 'schema': {'type': 'int'}}
            },
        }
    )
    assert v.validate_test({'FieldA': '123'}) == {'field_a': 123}
    assert v.validate_test({'field_a': '123'}) == {'field_a': 123}
    assert v.validate_test({'FieldA': '1', 'field_a': '2'}) == {'field_a': 1}
    with pytest.raises(ValidationError, match=r'FieldA\n +Field required \[type=missing,'):
        assert v.validate_test({'foobar': '123'})


@pytest.mark.parametrize(
    'input_value,expected',
    [
        ({'foo': {'bar': '123'}}, {'field_a': 123}),
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
            'type': 'typed-dict',
            'fields': {
                'field_a': {'validation_alias': ['foo', 'bar'], 'type': 'typed-dict-field', 'schema': {'type': 'int'}}
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
        ({'foo': {'bar': {'bat': '123'}}}, {'field_a': 123}),
        ({'foo': [1, 2, 3, 4]}, {'field_a': 4}),
        ({'foo': (1, 2, 3, 4)}, {'field_a': 4}),
        ({'spam': 5}, {'field_a': 5}),
        ({'spam': 1, 'foo': {'bar': {'bat': 2}}}, {'field_a': 2}),
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
            'type': 'typed-dict',
            'fields': {
                'field_a': {
                    'validation_alias': [['foo', 'bar', 'bat'], ['foo', 3], ['spam']],
                    'type': 'typed-dict-field',
                    'schema': {'type': 'int'},
                }
            },
            'config': {'loc_by_alias': False},
        }
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
        ({'foo': {-2: '123'}}, {'field_a': 123}),
        # negatives indexes work fine
        ({'foo': [1, 42, 'xx']}, {'field_a': 42}),
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
        {
            'type': 'typed-dict',
            'fields': {
                'field_a': {'validation_alias': ['foo', -2], 'type': 'typed-dict-field', 'schema': {'type': 'int'}}
            },
            'config': {'loc_by_alias': False},
        }
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
        ({'foo': [1, 42, 'xx']}, {'field_a': 42}),
        ({'foo': [42, 'xxx', 42]}, Err(r'Input should be a valid integer,')),
        ({'foo': [42]}, Err(r'foo.-2\n +Field required \[type=missing,')),
    ],
    ids=repr,
)
def test_aliases_path_negative_json(py_and_json: PyAndJson, input_value, expected):
    v = py_and_json(
        {
            'type': 'typed-dict',
            'fields': {
                'field_a': {'validation_alias': ['foo', -2], 'type': 'typed-dict-field', 'schema': {'type': 'int'}}
            },
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
        {
            'type': 'typed-dict',
            'fields': {
                'field_a': {
                    'validation_alias': [['foo', 'bar', 'bat'], ['foo', 3]],
                    'type': 'typed-dict-field',
                    'schema': {'type': 'int'},
                }
            },
        }
    )
    print(repr(v))
    assert repr(v).startswith('SchemaValidator(title="typed-dict", validator=TypedDict(')
    assert 'PathChoices(' in repr(v)


def get_int_key():
    v = SchemaValidator(
        {
            'type': 'typed-dict',
            'fields': {
                'field_a': {
                    'validation_alias': [['foo', 3], ['spam']],
                    'type': 'typed-dict-field',
                    'schema': {'type': 'int'},
                }
            },
        }
    )
    assert v.validate_python({'foo': {3: 33}}) == ({'field_a': 33}, {'field_a'})


class GetItemThing:
    def __getitem__(self, v):
        assert v == 'foo'
        return 321


def get_custom_getitem():
    v = SchemaValidator(
        {
            'type': 'typed-dict',
            'fields': {'field_a': {'validation_alias': ['foo'], 'type': 'typed-dict-field', 'schema': {'type': 'int'}}},
        }
    )
    assert v.validate_python(GetItemThing()) == ({'field_a': 321}, {'field_a'})
    assert v.validate_python({'bar': GetItemThing()}) == ({'field_a': 321}, {'field_a'})


@pytest.mark.parametrize('input_value', [{'foo': {'bar': 42}}, {'foo': 42}, {'field_a': 42}], ids=repr)
def test_paths_allow_by_name(py_and_json: PyAndJson, input_value):
    v = py_and_json(
        {
            'type': 'typed-dict',
            'fields': {
                'field_a': {
                    'validation_alias': [['foo', 'bar'], ['foo']],
                    'type': 'typed-dict-field',
                    'schema': {'type': 'int'},
                }
            },
            'populate_by_name': True,
        }
    )
    assert v.validate_test(input_value) == {'field_a': 42}


@pytest.mark.parametrize(
    'alias_schema,error',
    [
        ({'validation_alias': ['foo', ['bar']]}, 'Input should be a valid string'),
        ({'validation_alias': []}, 'Lookup paths should have at least one element'),
        ({'validation_alias': [[]]}, 'Each alias path should have at least one element'),
        ({'validation_alias': [123]}, "TypeError: 'int' object cannot be converted to 'PyList'"),
        ({'validation_alias': [[[]]]}, 'Input should be a valid string'),
        ({'validation_alias': [[1, 'foo']]}, 'TypeError: The first item in an alias path should be a string'),
    ],
    ids=repr,
)
def test_alias_build_error(alias_schema, error):
    with pytest.raises(SchemaError, match=error):
        SchemaValidator(
            {
                'type': 'typed-dict',
                'fields': {'field_a': {'type': 'typed-dict-field', 'schema': {'type': 'int'}, **alias_schema}},
            }
        )


def test_alias_error_loc_alias(py_and_json: PyAndJson):
    v = py_and_json(
        {
            'type': 'typed-dict',
            'fields': {
                'field_a': {
                    'type': 'typed-dict-field',
                    'schema': {'type': 'int'},
                    'validation_alias': [['foo', 'x'], ['bar', 1, -1]],
                }
            },
        },
        {'loc_by_alias': True},  # this is the default
    )
    assert v.validate_test({'foo': {'x': 42}}) == {'field_a': 42}
    assert v.validate_python({'bar': ['x', {-1: 42}]}) == {'field_a': 42}
    assert v.validate_test({'bar': ['x', [1, 2, 42]]}) == {'field_a': 42}
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
            'type': 'typed-dict',
            'fields': {
                'field_a': {
                    'type': 'typed-dict-field',
                    'schema': {'type': 'int'},
                    'validation_alias': [['foo'], ['bar', 1, -1]],
                }
            },
            'config': {'loc_by_alias': False},
        }
    )
    assert v.validate_test({'foo': 42}) == {'field_a': 42}
    assert v.validate_test({'bar': ['x', [1, 2, 42]]}) == {'field_a': 42}
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
    v = SchemaValidator({'type': 'typed-dict', 'fields': {}})
    assert v.validate_python({}) == {}
    with pytest.raises(ValidationError, match=re.escape('Input should be a valid dictionary [type=dict_type,')):
        v.validate_python('x')


def test_model_deep():
    v = SchemaValidator(
        {
            'type': 'typed-dict',
            'fields': {
                'field_a': {'type': 'typed-dict-field', 'schema': {'type': 'str'}},
                'field_b': {
                    'type': 'typed-dict-field',
                    'schema': {
                        'type': 'typed-dict',
                        'fields': {
                            'field_c': {'type': 'typed-dict-field', 'schema': {'type': 'str'}},
                            'field_d': {
                                'type': 'typed-dict-field',
                                'schema': {
                                    'type': 'typed-dict',
                                    'fields': {
                                        'field_e': {'type': 'typed-dict-field', 'schema': {'type': 'str'}},
                                        'field_f': {'type': 'typed-dict-field', 'schema': {'type': 'int'}},
                                    },
                                },
                            },
                        },
                    },
                },
            },
        }
    )
    output = v.validate_python({'field_a': '1', 'field_b': {'field_c': '2', 'field_d': {'field_e': '4', 'field_f': 4}}})
    assert output == {'field_a': '1', 'field_b': ({'field_c': '2', 'field_d': {'field_e': '4', 'field_f': 4}})}
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


def test_alias_extra(py_and_json: PyAndJson):
    v = py_and_json(
        {
            'type': 'typed-dict',
            'extra_behavior': 'allow',
            'fields': {
                'field_a': {
                    'validation_alias': [['FieldA'], ['foo', 2]],
                    'type': 'typed-dict-field',
                    'schema': {'type': 'int'},
                }
            },
            'config': {'loc_by_alias': False},
        }
    )
    assert v.validate_test({'FieldA': 1}) == {'field_a': 1}
    assert v.validate_test({'foo': [1, 2, 3]}) == {'field_a': 3}

    # used_keys should be populated either though validation fails so "FieldA" is skipped in extra
    with pytest.raises(ValidationError) as exc_info:
        assert v.validate_test({'FieldA': '...'}) == {'field_a': 1}

    assert exc_info.value.errors(include_url=False) == [
        {
            'type': 'int_parsing',
            'loc': ('field_a',),
            'msg': 'Input should be a valid integer, unable to parse string as an integer',
            'input': '...',
        }
    ]


def test_alias_extra_by_name(py_and_json: PyAndJson):
    v = py_and_json(
        {
            'type': 'typed-dict',
            'extra_behavior': 'allow',
            'populate_by_name': True,
            'fields': {
                'field_a': {'validation_alias': 'FieldA', 'type': 'typed-dict-field', 'schema': {'type': 'int'}}
            },
        }
    )
    assert v.validate_test({'FieldA': 1}) == {'field_a': 1}
    assert v.validate_test({'field_a': 1}) == {'field_a': 1}


def test_alias_extra_forbid(py_and_json: PyAndJson):
    v = py_and_json(
        {
            'type': 'typed-dict',
            'extra_behavior': 'forbid',
            'fields': {
                'field_a': {'type': 'typed-dict-field', 'validation_alias': 'FieldA', 'schema': {'type': 'int'}}
            },
        }
    )
    assert v.validate_test({'FieldA': 1}) == {'field_a': 1}


def test_with_default_factory():
    v = SchemaValidator(
        {
            'type': 'typed-dict',
            'fields': {
                'x': {
                    'type': 'typed-dict-field',
                    'schema': {'type': 'default', 'schema': {'type': 'str'}, 'default_factory': lambda: 'pikachu'},
                }
            },
        }
    )

    assert v.validate_python({}) == {'x': 'pikachu'}
    assert v.validate_python({'x': 'bulbi'}) == {'x': 'bulbi'}


def test_field_required_and_default_factory():
    """A field cannot be required and have a default factory"""
    with pytest.raises(SchemaError, match="Field 'x': a required field cannot have a default value"):
        SchemaValidator(
            {
                'type': 'typed-dict',
                'fields': {
                    'x': {
                        'type': 'typed-dict-field',
                        'schema': {'type': 'default', 'schema': {'type': 'str'}, 'default_factory': lambda: 'pika'},
                        'required': True,
                    }
                },
            }
        )


@pytest.mark.parametrize(
    'default_factory,error_message',
    [
        (lambda: 1 + 'a', "unsupported operand type(s) for +: 'int' and 'str'"),
        (lambda x: 'a' + x, "<lambda>() missing 1 required positional argument: 'x'"),
    ],
)
def test_bad_default_factory(default_factory, error_message):
    v = SchemaValidator(
        {
            'type': 'typed-dict',
            'fields': {
                'x': {
                    'type': 'typed-dict-field',
                    'schema': {'type': 'default', 'schema': {'type': 'str'}, 'default_factory': default_factory},
                }
            },
        }
    )
    with pytest.raises(TypeError, match=re.escape(error_message)):
        v.validate_python({})


class TestOnError:
    def test_on_error_bad_name(self):
        with pytest.raises(SchemaError, match="Input should be 'raise', 'omit' or 'default'"):
            SchemaValidator(
                {
                    'type': 'typed-dict',
                    'fields': {
                        'x': {
                            'type': 'typed-dict-field',
                            'schema': {'type': 'default', 'schema': {'type': 'str'}, 'on_error': 'rais'},
                        }
                    },
                }
            )

    def test_on_error_bad_omit(self):
        with pytest.raises(SchemaError, match="Field 'x': 'on_error = omit' cannot be set for required fields"):
            SchemaValidator(
                {
                    'type': 'typed-dict',
                    'fields': {
                        'x': {
                            'type': 'typed-dict-field',
                            'schema': {'type': 'default', 'schema': {'type': 'str'}, 'on_error': 'omit'},
                        }
                    },
                }
            )

    def test_on_error_bad_default(self):
        with pytest.raises(SchemaError, match="'on_error = default' requires a `default` or `default_factory`"):
            SchemaValidator(
                {
                    'type': 'typed-dict',
                    'fields': {
                        'x': {
                            'type': 'typed-dict-field',
                            'schema': {'type': 'default', 'schema': {'type': 'str'}, 'on_error': 'default'},
                        }
                    },
                }
            )

    def test_on_error_raise_by_default(self, py_and_json: PyAndJson):
        v = py_and_json(
            {'type': 'typed-dict', 'fields': {'x': {'type': 'typed-dict-field', 'schema': {'type': 'str'}}}}
        )
        assert v.validate_test({'x': 'foo'}) == {'x': 'foo'}
        with pytest.raises(ValidationError) as exc_info:
            v.validate_test({'x': ['foo']})
        assert exc_info.value.errors(include_url=False) == [
            {'input': ['foo'], 'type': 'string_type', 'loc': ('x',), 'msg': 'Input should be a valid string'}
        ]

    def test_on_error_raise_explicit(self, py_and_json: PyAndJson):
        v = py_and_json(
            {
                'type': 'typed-dict',
                'fields': {
                    'x': {
                        'type': 'typed-dict-field',
                        'schema': {'type': 'default', 'schema': {'type': 'str'}, 'on_error': 'raise'},
                    }
                },
            }
        )
        assert v.validate_test({'x': 'foo'}) == {'x': 'foo'}
        with pytest.raises(ValidationError) as exc_info:
            v.validate_test({'x': ['foo']})
        assert exc_info.value.errors(include_url=False) == [
            {'input': ['foo'], 'type': 'string_type', 'loc': ('x',), 'msg': 'Input should be a valid string'}
        ]

    def test_on_error_omit(self, py_and_json: PyAndJson):
        v = py_and_json(
            {
                'type': 'typed-dict',
                'fields': {
                    'x': {
                        'type': 'typed-dict-field',
                        'schema': {'type': 'default', 'schema': {'type': 'str'}, 'on_error': 'omit'},
                        'required': False,
                    }
                },
            }
        )
        assert v.validate_test({'x': 'foo'}) == {'x': 'foo'}
        assert v.validate_test({}) == {}
        assert v.validate_test({'x': ['foo']}) == {}

    def test_on_error_omit_with_default(self, py_and_json: PyAndJson):
        v = py_and_json(
            {
                'type': 'typed-dict',
                'fields': {
                    'x': {
                        'type': 'typed-dict-field',
                        'schema': {'type': 'default', 'schema': {'type': 'str'}, 'on_error': 'omit', 'default': 'pika'},
                        'required': False,
                    }
                },
            }
        )
        assert v.validate_test({'x': 'foo'}) == {'x': 'foo'}
        assert v.validate_test({}) == {'x': 'pika'}
        assert v.validate_test({'x': ['foo']}) == {}

    def test_on_error_default(self, py_and_json: PyAndJson):
        v = py_and_json(
            {
                'type': 'typed-dict',
                'fields': {
                    'x': {
                        'type': 'typed-dict-field',
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
        assert v.validate_test({'x': 'foo'}) == {'x': 'foo'}
        assert v.validate_test({'x': ['foo']}) == {'x': 'pika'}

    def test_on_error_default_factory(self, py_and_json: PyAndJson):
        v = py_and_json(
            {
                'type': 'typed-dict',
                'fields': {
                    'x': {
                        'type': 'typed-dict-field',
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
        assert v.validate_test({'x': 'foo'}) == {'x': 'foo'}
        assert v.validate_test({'x': ['foo']}) == {'x': 'pika'}

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
                'type': 'typed-dict',
                'fields': {
                    'x': {
                        'type': 'typed-dict-field',
                        'schema': {
                            'type': 'default',
                            'on_error': 'raise',
                            'schema': {
                                'type': 'function-wrap',
                                'function': {'type': 'general', 'function': wrap_function},
                                'schema': {'type': 'str'},
                            },
                        },
                    }
                },
            }
        )
        assert v.validate_test({'x': 'foo'}) == {'x': 'foo'}
        assert v.validate_test({'x': ['foo']}) == {'x': '1'}
        assert v.validate_test({'x': ['foo', 'bar']}) == {'x': '2'}
        assert v.validate_test({'x': {'a': 'b'}}) == {'x': "{'a': 'b'}"}


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
    schema_extra_behavior_kw: Dict[str, Any],
    extras_schema_kw: Dict[str, Any],
    expected_extra_value: Any,
):
    v = SchemaValidator(
        core_schema.typed_dict_schema(
            {'f': core_schema.typed_dict_field(core_schema.str_schema())},
            **schema_extra_behavior_kw,
            **extras_schema_kw,
            config=config,
        )
    )

    m: Dict[str, Any] = v.validate_python({'f': 'x', 'extra_field': '123'})
    assert m == {'f': 'x', 'extra_field': expected_extra_value}


@pytest.mark.parametrize(
    'config,schema_extra_behavior_kw',
    [
        (core_schema.CoreConfig(extra_fields_behavior='forbid'), {}),
        (core_schema.CoreConfig(extra_fields_behavior='forbid'), {'extra_behavior': None}),
        (core_schema.CoreConfig(), {'extra_behavior': 'forbid'}),
        (None, {'extra_behavior': 'forbid'}),
        (core_schema.CoreConfig(extra_fields_behavior='allow'), {'extra_behavior': 'forbid'}),
    ],
)
def test_extra_behavior_forbid(config: Union[core_schema.CoreConfig, None], schema_extra_behavior_kw: Dict[str, Any]):
    v = SchemaValidator(
        core_schema.typed_dict_schema(
            {'f': core_schema.typed_dict_field(core_schema.str_schema())}, **schema_extra_behavior_kw, config=config
        )
    )

    m: Dict[str, Any] = v.validate_python({'f': 'x'})
    assert m == {'f': 'x'}

    with pytest.raises(ValidationError) as exc_info:
        v.validate_python({'f': 'x', 'extra_field': 123})
    assert exc_info.value.errors(include_url=False) == [
        {'type': 'extra_forbidden', 'loc': ('extra_field',), 'msg': 'Extra inputs are not permitted', 'input': 123}
    ]


@pytest.mark.parametrize(
    'config,schema_extra_behavior_kw',
    [
        (core_schema.CoreConfig(extra_fields_behavior='ignore'), {}),
        (core_schema.CoreConfig(), {'extra_behavior': 'ignore'}),
        (None, {'extra_behavior': 'ignore'}),
        (core_schema.CoreConfig(extra_fields_behavior='forbid'), {'extra_behavior': 'ignore'}),
        (core_schema.CoreConfig(), {}),
        (core_schema.CoreConfig(), {'extra_behavior': None}),
        (None, {'extra_behavior': None}),
    ],
)
def test_extra_behavior_ignore(config: Union[core_schema.CoreConfig, None], schema_extra_behavior_kw: Dict[str, Any]):
    v = SchemaValidator(
        core_schema.typed_dict_schema(
            {'f': core_schema.typed_dict_field(core_schema.str_schema())}, **schema_extra_behavior_kw
        ),
        config=config,
    )

    m: Dict[str, Any] = v.validate_python({'f': 'x', 'extra_field': 123})
    assert m == {'f': 'x'}


@pytest.mark.xfail(
    condition=platform.python_implementation() == 'PyPy', reason='https://foss.heptapod.net/pypy/pypy/-/issues/3899'
)
def test_leak_typed_dict():
    def fn():
        def validate(v, info):
            return v

        schema = core_schema.general_plain_validator_function(validate)
        schema = core_schema.typed_dict_schema(
            {'f': core_schema.typed_dict_field(schema)}, extra_behavior='allow', extras_schema=schema
        )

        # If any of the Rust validators don't implement traversal properly,
        # there will be an undetectable cycle created by this assignment
        # which will keep Defaulted alive
        validate.__pydantic_validator__ = SchemaValidator(schema)

        return validate

    cycle = fn()
    ref = weakref.ref(cycle)
    assert ref() is not None

    del cycle
    gc.collect(0)
    gc.collect(1)
    gc.collect(2)
    gc.collect()

    assert ref() is None
