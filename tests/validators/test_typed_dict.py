import re
import sys
from dataclasses import dataclass
from datetime import datetime
from typing import Mapping

import pytest
from dirty_equals import HasRepr, IsStr

from pydantic_core import Config, SchemaError, SchemaValidator, ValidationError

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
            'fields': {'field_a': {'schema': {'type': 'str'}}, 'field_b': {'schema': {'type': 'int'}}},
        }
    )

    assert v.validate_python({'field_a': b'abc', 'field_b': 1}) == {'field_a': 'abc', 'field_b': 1}


def test_strict():
    v = SchemaValidator(
        {
            'type': 'typed-dict',
            'fields': {'field_a': {'schema': {'type': 'str'}}, 'field_b': {'schema': {'type': 'int'}}},
        },
        {'strict': True},
    )

    assert v.validate_python({'field_a': 'hello', 'field_b': 12}) == {'field_a': 'hello', 'field_b': 12}

    with pytest.raises(ValidationError) as exc_info:
        assert v.validate_python({'field_a': 123, 'field_b': '123'})
    assert exc_info.value.errors() == [
        {'kind': 'str_type', 'loc': ['field_a'], 'message': 'Input should be a valid string', 'input_value': 123},
        {'kind': 'int_type', 'loc': ['field_b'], 'message': 'Input should be a valid integer', 'input_value': '123'},
    ]


def test_with_default():
    v = SchemaValidator(
        {
            'type': 'typed-dict',
            'return_fields_set': True,
            'fields': {'field_a': {'schema': {'type': 'str'}}, 'field_b': {'schema': {'type': 'int'}, 'default': 666}},
        }
    )

    assert v.validate_python({'field_a': b'abc'}) == ({'field_a': 'abc', 'field_b': 666}, {'field_a'})
    assert v.validate_python({'field_a': b'abc', 'field_b': 1}) == (
        {'field_a': 'abc', 'field_b': 1},
        {'field_b', 'field_a'},
    )


def test_missing_error():
    v = SchemaValidator(
        {
            'type': 'typed-dict',
            'fields': {'field_a': {'schema': {'type': 'str'}}, 'field_b': {'schema': {'type': 'int'}}},
        }
    )
    with pytest.raises(ValidationError) as exc_info:
        v.validate_python({'field_a': b'abc'})
    assert (
        str(exc_info.value)
        == """\
1 validation error for typed-dict
field_b
  Field required [kind=missing, input_value={'field_a': b'abc'}, input_type=dict]"""
    )


@pytest.mark.parametrize(
    'config,input_value,expected',
    [
        ({}, {'a': '123'}, {'a': 123}),
        ({}, Map(a=123), {'a': 123}),
        ({}, {b'a': '123'}, Err('Field required [kind=missing,')),
        ({}, {'a': '123', 'c': 4}, {'a': 123}),
        ({'typed_dict_extra_behavior': 'allow'}, {'a': '123', 'c': 4}, {'a': 123, 'c': 4}),
        (
            {'typed_dict_extra_behavior': 'allow'},
            {'a': '123', b'c': 4},
            Err('Keys should be strings [kind=invalid_key,'),
        ),
        ({'strict': True}, Map(a=123), Err('Input should be a valid dictionary [kind=dict_type,')),
    ],
    ids=repr,
)
def test_config(config: Config, input_value, expected):
    v = SchemaValidator(
        {'type': 'typed-dict', 'fields': {'a': {'schema': 'int'}, 'b': {'schema': 'int', 'required': False}}}, config
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
            'return_fields_set': True,
            'fields': {'field_a': {'schema': {'type': 'str'}}, 'field_b': {'schema': {'type': 'int'}}},
        }
    )

    assert v.validate_python({'field_a': b'123', 'field_b': 1, 'field_c': 123}) == (
        {'field_a': '123', 'field_b': 1},
        {'field_b', 'field_a'},
    )


def test_forbid_extra():
    v = SchemaValidator(
        {
            'type': 'typed-dict',
            'return_fields_set': True,
            'fields': {'field_a': {'schema': {'type': 'str'}}},
            'extra_behavior': 'forbid',
        }
    )

    with pytest.raises(ValidationError) as exc_info:
        v.validate_python({'field_a': 'abc', 'field_b': 1})

    assert exc_info.value.errors() == [
        {'kind': 'extra_forbidden', 'loc': ['field_b'], 'message': 'Extra inputs are not permitted', 'input_value': 1}
    ]


def test_allow_extra():
    v = SchemaValidator(
        {
            'type': 'typed-dict',
            'return_fields_set': True,
            'fields': {'field_a': {'schema': {'type': 'str'}}},
            'extra_behavior': 'allow',
        }
    )

    assert v.validate_python({'field_a': b'abc', 'field_b': (1, 2)}) == (
        {'field_a': 'abc', 'field_b': (1, 2)},
        {'field_a', 'field_b'},
    )


def test_allow_extra_validate():
    v = SchemaValidator(
        {
            'type': 'typed-dict',
            'return_fields_set': True,
            'fields': {'field_a': {'schema': {'type': 'str'}}},
            'extra_validator': {'type': 'int'},
            'extra_behavior': 'allow',
        }
    )

    assert v.validate_python({'field_a': 'test', 'other_value': '123'}) == (
        {'field_a': 'test', 'other_value': 123},
        {'field_a', 'other_value'},
    )

    with pytest.raises(ValidationError) as exc_info:
        v.validate_python({'field_a': 'test', 'other_value': 12.5})
    assert exc_info.value.errors() == [
        {
            'kind': 'int_from_float',
            'loc': ['other_value'],
            'message': 'Input should be a valid integer, got a number with a fractional part',
            'input_value': 12.5,
        }
    ]


def test_allow_extra_invalid():
    with pytest.raises(SchemaError, match='extra_validator can only be used if extra_behavior=allow'):
        SchemaValidator(
            {'type': 'typed-dict', 'fields': {}, 'extra_validator': {'type': 'int'}, 'extra_behavior': 'ignore'}
        )


def test_allow_extra_wrong():
    with pytest.raises(SchemaError, match='Invalid extra_behavior: "wrong"'):
        SchemaValidator({'type': 'typed-dict', 'fields': {}}, {'typed_dict_extra_behavior': 'wrong'})


def test_str_config():
    v = SchemaValidator(
        {'type': 'typed-dict', 'fields': {'field_a': {'schema': {'type': 'str'}}}}, {'str_max_length': 5}
    )
    assert v.validate_python({'field_a': 'test'}) == {'field_a': 'test'}

    with pytest.raises(ValidationError, match='String should have at most 5 characters'):
        v.validate_python({'field_a': 'test long'})


def test_validate_assignment():
    v = SchemaValidator(
        {'type': 'typed-dict', 'return_fields_set': True, 'fields': {'field_a': {'schema': {'type': 'str'}}}}
    )

    assert v.validate_python({'field_a': 'test'}) == ({'field_a': 'test'}, {'field_a'})

    assert v.validate_assignment('field_a', b'abc', {'field_a': 'test'}) == ({'field_a': 'abc'}, {'field_a'})


def test_validate_assignment_functions():
    calls = []

    def func_a(input_value, **kwargs):
        calls.append('func_a')
        return input_value * 2

    def func_b(input_value, **kwargs):
        calls.append('func_b')
        return input_value / 2

    v = SchemaValidator(
        {
            'type': 'typed-dict',
            'return_fields_set': True,
            'fields': {
                'field_a': {
                    'schema': {'type': 'function', 'mode': 'after', 'function': func_a, 'schema': {'type': 'str'}}
                },
                'field_b': {
                    'schema': {'type': 'function', 'mode': 'after', 'function': func_b, 'schema': {'type': 'int'}}
                },
            },
        }
    )

    assert v.validate_python({'field_a': 'test', 'field_b': 12.0}) == (
        {'field_a': 'testtest', 'field_b': 6},
        {'field_a', 'field_b'},
    )

    assert calls == ['func_a', 'func_b']
    calls.clear()

    assert v.validate_assignment('field_a', 'new-val', {'field_a': 'testtest', 'field_b': 6}) == (
        {'field_a': 'new-valnew-val', 'field_b': 6},
        {'field_a'},
    )
    assert calls == ['func_a']


def test_validate_assignment_ignore_extra():
    v = SchemaValidator(
        {'type': 'typed-dict', 'return_fields_set': True, 'fields': {'field_a': {'schema': {'type': 'str'}}}}
    )

    assert v.validate_python({'field_a': 'test'}) == ({'field_a': 'test'}, {'field_a'})

    with pytest.raises(ValidationError) as exc_info:
        v.validate_assignment('other_field', 456, {'field_a': 'test'})

    assert exc_info.value.errors() == [
        {
            'kind': 'extra_forbidden',
            'loc': ['other_field'],
            'message': 'Extra inputs are not permitted',
            'input_value': 456,
        }
    ]


def test_validate_assignment_allow_extra():
    v = SchemaValidator(
        {'type': 'typed-dict', 'fields': {'field_a': {'schema': {'type': 'str'}}}, 'extra_behavior': 'allow'}
    )

    assert v.validate_python({'field_a': 'test'}) == {'field_a': 'test'}

    assert v.validate_assignment('other_field', 456, {'field_a': 'test'}) == {'field_a': 'test', 'other_field': 456}


def test_validate_assignment_allow_extra_validate():
    v = SchemaValidator(
        {
            'type': 'typed-dict',
            'fields': {'field_a': {'schema': {'type': 'str'}}},
            'extra_validator': {'type': 'int'},
            'extra_behavior': 'allow',
        }
    )

    assert v.validate_assignment('other_field', '456', {'field_a': 'test'}) == {'field_a': 'test', 'other_field': 456}

    with pytest.raises(ValidationError) as exc_info:
        assert v.validate_assignment('other_field', 'xyz', {'field_a': 'test'})
    assert exc_info.value.errors() == [
        {
            'kind': 'int_parsing',
            'loc': ['other_field'],
            'message': 'Input should be a valid integer, unable to parse string as an integer',
            'input_value': 'xyz',
        }
    ]


def test_json_error():
    v = SchemaValidator(
        {'type': 'typed-dict', 'fields': {'field_a': {'schema': {'type': 'list', 'items_schema': 'int'}}}}
    )
    with pytest.raises(ValidationError) as exc_info:
        v.validate_json('{"field_a": [123, "wrong"]}')

    assert exc_info.value.errors() == [
        {
            'kind': 'int_parsing',
            'loc': ['field_a', 1],
            'message': 'Input should be a valid integer, unable to parse string as an integer',
            'input_value': 'wrong',
        }
    ]


def test_missing_schema_key():
    with pytest.raises(SchemaError, match='typed-dict -> fields -> x -> schema\n  Field required'):
        SchemaValidator({'type': 'typed-dict', 'fields': {'x': {'type': 'str'}}})


def test_fields_required_by_default():
    """By default all fields should be required"""
    v = SchemaValidator(
        {'type': 'typed-dict', 'fields': {'x': {'schema': {'type': 'str'}}, 'y': {'schema': {'type': 'str'}}}}
    )

    assert v.validate_python({'x': 'pika', 'y': 'chu'}) == {'x': 'pika', 'y': 'chu'}

    with pytest.raises(ValidationError) as exc_info:
        assert v.validate_python({'x': 'pika'})

    assert exc_info.value.errors() == [
        {'kind': 'missing', 'loc': ['y'], 'message': 'Field required', 'input_value': {'x': 'pika'}}
    ]


def test_fields_required_by_default_with_optional():
    v = SchemaValidator(
        {
            'type': 'typed-dict',
            'return_fields_set': True,
            'fields': {'x': {'schema': {'type': 'str'}}, 'y': {'schema': {'type': 'str'}, 'required': False}},
        }
    )

    assert v.validate_python({'x': 'pika', 'y': 'chu'}) == ({'x': 'pika', 'y': 'chu'}, {'x', 'y'})
    assert v.validate_python({'x': 'pika'}) == ({'x': 'pika'}, {'x'})


def test_fields_required_by_default_with_default():
    v = SchemaValidator(
        {
            'type': 'typed-dict',
            'return_fields_set': True,
            'fields': {'x': {'schema': {'type': 'str'}}, 'y': {'schema': {'type': 'str'}, 'default': 'bulbi'}},
        }
    )

    assert v.validate_python({'x': 'pika', 'y': 'chu'}) == ({'x': 'pika', 'y': 'chu'}, {'x', 'y'})
    assert v.validate_python({'x': 'pika'}) == ({'x': 'pika', 'y': 'bulbi'}, {'x'})


def test_all_optional_fields():
    """By default all fields should be optional if `full` is set to `False`"""
    v = SchemaValidator(
        {
            'type': 'typed-dict',
            'full': False,
            'return_fields_set': True,
            'fields': {'x': {'schema': {'type': 'str', 'strict': True}}, 'y': {'schema': {'type': 'str'}}},
        }
    )

    assert v.validate_python({'x': 'pika', 'y': 'chu'}) == ({'x': 'pika', 'y': 'chu'}, {'x', 'y'})
    assert v.validate_python({'x': 'pika'}) == ({'x': 'pika'}, {'x'})
    assert v.validate_python({'y': 'chu'}) == ({'y': 'chu'}, {'y'})

    with pytest.raises(ValidationError) as exc_info:
        assert v.validate_python({'x': 123})

    assert exc_info.value.errors() == [
        {'kind': 'str_type', 'loc': ['x'], 'message': 'Input should be a valid string', 'input_value': 123}
    ]


def test_all_optional_fields_with_required_fields():
    v = SchemaValidator(
        {
            'type': 'typed-dict',
            'full': False,
            'return_fields_set': True,
            'fields': {
                'x': {'schema': {'type': 'str', 'strict': True}, 'required': True},
                'y': {'schema': {'type': 'str'}},
            },
        }
    )

    assert v.validate_python({'x': 'pika', 'y': 'chu'}) == ({'x': 'pika', 'y': 'chu'}, {'x', 'y'})
    assert v.validate_python({'x': 'pika'}) == ({'x': 'pika'}, {'x'})

    with pytest.raises(ValidationError) as exc_info:
        assert v.validate_python({'y': 'chu'}) == ({'y': 'chu'}, {'y'})

    assert exc_info.value.errors() == [
        {'kind': 'missing', 'loc': ['x'], 'message': 'Field required', 'input_value': {'y': 'chu'}}
    ]


def test_field_required_and_default():
    """A field cannot be required and have a default value"""
    with pytest.raises(SchemaError, match="Field 'x': a required field cannot have a default value"):
        SchemaValidator(
            {'type': 'typed-dict', 'fields': {'x': {'schema': {'type': 'str'}, 'required': True, 'default': 'pika'}}}
        )


def test_alias(py_and_json: PyAndJson):
    v = py_and_json({'type': 'typed-dict', 'fields': {'field_a': {'alias': 'FieldA', 'schema': 'int'}}})
    assert v.validate_test({'FieldA': '123'}) == {'field_a': 123}
    with pytest.raises(ValidationError, match=r'field_a\n +Field required \[kind=missing,'):
        assert v.validate_test({'foobar': '123'})
    with pytest.raises(ValidationError, match=r'field_a\n +Field required \[kind=missing,'):
        assert v.validate_test({'field_a': '123'})


def test_empty_string_field_name(py_and_json: PyAndJson):
    v = py_and_json({'type': 'typed-dict', 'fields': {'': {'schema': {'type': 'int'}}}})
    assert v.validate_test({'': 123}) == {'': 123}


def test_empty_string_aliases(py_and_json: PyAndJson):
    v = py_and_json({'type': 'typed-dict', 'fields': {'field_a': {'alias': '', 'schema': {'type': 'int'}}}})
    assert v.validate_test({'': 123}) == {'field_a': 123}

    v = py_and_json({'type': 'typed-dict', 'fields': {'field_a': {'alias': ['', ''], 'schema': {'type': 'int'}}}})
    assert v.validate_test({'': {'': 123}}) == {'field_a': 123}


def test_alias_allow_pop(py_and_json: PyAndJson):
    v = py_and_json(
        {
            'type': 'typed-dict',
            'return_fields_set': True,
            'populate_by_name': True,
            'fields': {'field_a': {'alias': 'FieldA', 'schema': 'int'}},
        }
    )
    assert v.validate_test({'FieldA': '123'}) == ({'field_a': 123}, {'field_a'})
    assert v.validate_test({'field_a': '123'}) == ({'field_a': 123}, {'field_a'})
    assert v.validate_test({'FieldA': '1', 'field_a': '2'}) == ({'field_a': 1}, {'field_a'})
    with pytest.raises(ValidationError, match=r'field_a\n +Field required \[kind=missing,'):
        assert v.validate_test({'foobar': '123'})


@pytest.mark.parametrize(
    'input_value,expected',
    [
        ({'foo': {'bar': '123'}}, {'field_a': 123}),
        ({'x': '123'}, Err(r'field_a\n +Field required \[kind=missing,')),
        ({'foo': '123'}, Err(r'field_a\n +Field required \[kind=missing,')),
        ({'foo': [1, 2, 3]}, Err(r'field_a\n +Field required \[kind=missing,')),
        ({'foo': {'bat': '123'}}, Err(r'field_a\n +Field required \[kind=missing,')),
    ],
    ids=repr,
)
def test_alias_path(py_and_json: PyAndJson, input_value, expected):
    v = py_and_json({'type': 'typed-dict', 'fields': {'field_a': {'alias': ['foo', 'bar'], 'schema': 'int'}}})
    if isinstance(expected, Err):
        with pytest.raises(ValidationError, match=expected.message):
            v.validate_test(input_value)
    else:
        output = v.validate_test(input_value)
        assert output == expected


@pytest.mark.parametrize(
    'input_value,expected',
    [
        ({'foo': {'bar': {'bat': '123'}}}, ({'field_a': 123}, {'field_a'})),
        ({'foo': [1, 2, 3, 4]}, ({'field_a': 4}, {'field_a'})),
        ({'foo': (1, 2, 3, 4)}, ({'field_a': 4}, {'field_a'})),
        ({'spam': 5}, ({'field_a': 5}, {'field_a'})),
        ({'spam': 1, 'foo': {'bar': {'bat': 2}}}, ({'field_a': 2}, {'field_a'})),
        ({'foo': {'x': 2}}, Err(r'field_a\n +Field required \[kind=missing,')),
        ({'x': '123'}, Err(r'field_a\n +Field required \[kind=missing,')),
        ({'x': {2: 33}}, Err(r'field_a\n +Field required \[kind=missing,')),
        ({'foo': '01234'}, Err(r'field_a\n +Field required \[kind=missing,')),
        ({'foo': [1]}, Err(r'field_a\n +Field required \[kind=missing,')),
    ],
    ids=repr,
)
def test_aliases_path_multiple(py_and_json: PyAndJson, input_value, expected):
    v = py_and_json(
        {
            'type': 'typed-dict',
            'return_fields_set': True,
            'fields': {'field_a': {'alias': [['foo', 'bar', 'bat'], ['foo', 3], ['spam']], 'schema': 'int'}},
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
        {'type': 'typed-dict', 'fields': {'field_a': {'alias': [['foo', 'bar', 'bat'], ['foo', 3]], 'schema': 'int'}}}
    )
    assert repr(v).startswith('SchemaValidator(name="typed-dict", validator=TypedDict(')
    assert 'PathChoices(' in repr(v)


def get_int_key():
    v = SchemaValidator(
        {'type': 'typed-dict', 'fields': {'field_a': {'alias': [['foo', 3], ['spam']], 'schema': 'int'}}}
    )
    assert v.validate_python({'foo': {3: 33}}) == ({'field_a': 33}, {'field_a'})


class GetItemThing:
    def __getitem__(self, v):
        assert v == 'foo'
        return 321


def get_custom_getitem():
    v = SchemaValidator({'type': 'typed-dict', 'fields': {'field_a': {'alias': ['foo'], 'schema': 'int'}}})
    assert v.validate_python(GetItemThing()) == ({'field_a': 321}, {'field_a'})
    assert v.validate_python({'bar': GetItemThing()}) == ({'field_a': 321}, {'field_a'})


@pytest.mark.parametrize('input_value', [{'foo': {'bar': 42}}, {'foo': 42}, {'field_a': 42}], ids=repr)
def test_paths_allow_by_name(py_and_json: PyAndJson, input_value):
    v = py_and_json(
        {
            'type': 'typed-dict',
            'fields': {'field_a': {'alias': [['foo', 'bar'], ['foo']], 'schema': 'int'}},
            'populate_by_name': True,
        }
    )
    assert v.validate_test(input_value) == {'field_a': 42}


@pytest.mark.parametrize(
    'alias_schema,error',
    [
        ({'alias': ['foo', ['bar']]}, 'Input should be a valid string'),
        ({'alias': []}, 'Lookup paths should have at least one element'),
        ({'alias': [[]]}, 'Each alias path should have at least one element'),
        ({'alias': [123]}, "TypeError: 'int' object cannot be converted to 'PyList'"),
        ({'alias': [[[]]]}, 'Input should be a valid string'),
        ({'alias': [[1, 'foo']]}, 'TypeError: The first item in an alias path should be a string'),
    ],
    ids=repr,
)
def test_alias_build_error(alias_schema, error):
    with pytest.raises(SchemaError, match=error):
        SchemaValidator({'type': 'typed-dict', 'fields': {'field_a': {'schema': 'int', **alias_schema}}})


def test_empty_model():
    v = SchemaValidator({'type': 'typed-dict', 'fields': {}, 'return_fields_set': True})
    assert v.validate_python({}) == ({}, set())
    with pytest.raises(ValidationError, match=re.escape('Input should be a valid dictionary [kind=dict_type,')):
        v.validate_python('x')


def test_model_deep():
    v = SchemaValidator(
        {
            'type': 'typed-dict',
            'return_fields_set': True,
            'fields': {
                'field_a': {'schema': 'str'},
                'field_b': {
                    'schema': {
                        'type': 'typed-dict',
                        'return_fields_set': True,
                        'fields': {
                            'field_c': {'schema': 'str'},
                            'field_d': {
                                'schema': {
                                    'type': 'typed-dict',
                                    'return_fields_set': True,
                                    'fields': {'field_e': {'schema': 'str'}, 'field_f': {'schema': 'int'}},
                                }
                            },
                        },
                    }
                },
            },
        }
    )
    output, fields_set = v.validate_python(
        {'field_a': '1', 'field_b': {'field_c': '2', 'field_d': {'field_e': '4', 'field_f': 4}}}
    )
    assert output == {
        'field_a': '1',
        'field_b': (
            {'field_c': '2', 'field_d': ({'field_e': '4', 'field_f': 4}, {'field_f', 'field_e'})},
            {'field_d', 'field_c'},
        ),
    }
    assert fields_set == {'field_a', 'field_b'}
    with pytest.raises(ValidationError) as exc_info:
        v.validate_python({'field_a': '1', 'field_b': {'field_c': '2', 'field_d': {'field_e': '4', 'field_f': 'xx'}}})

    assert exc_info.value.errors() == [
        {
            'kind': 'int_parsing',
            'loc': ['field_b', 'field_d', 'field_f'],
            'message': 'Input should be a valid integer, unable to parse string as an integer',
            'input_value': 'xx',
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
        (ClassWithAttributes(), ({'a': 1, 'b': 2, 'c': 'ham'}, {'a', 'b', 'c'})),
        (MyDataclass(), ({'a': 1, 'b': 2, 'c': 'ham'}, {'a', 'b', 'c'})),
        (Cls(a=1, b=2, c='ham'), ({'a': 1, 'b': 2, 'c': 'ham'}, {'a', 'b', 'c'})),
        (dict(a=1, b=2, c='ham'), ({'a': 1, 'b': 2, 'c': 'ham'}, {'a', 'b', 'c'})),
        (Map(a=1, b=2, c='ham'), ({'a': 1, 'b': 2, 'c': 'ham'}, {'a', 'b', 'c'})),
        # using type gives `__module__ == 'builtins'`
        (type('Testing', (), {}), Err('[kind=dict_attributes_type,')),
        (
            '123',
            Err('Input should be a valid dictionary or instance to extract fields from [kind=dict_attributes_type,'),
        ),
        ([(1, 2)], Err('kind=dict_attributes_type,')),
        (((1, 2),), Err('kind=dict_attributes_type,')),
    ],
    ids=repr,
)
def test_from_attributes(input_value, expected):
    v = SchemaValidator(
        {
            'type': 'typed-dict',
            'return_fields_set': True,
            'fields': {'a': {'schema': 'int'}, 'b': {'schema': 'int'}, 'c': {'schema': 'str'}},
            'from_attributes': True,
        }
    )
    if isinstance(expected, Err):
        with pytest.raises(ValidationError, match=re.escape(expected.message)):
            val = v.validate_python(input_value)
            print(f'UNEXPECTED OUTPUT: {val!r}')
    else:
        output = v.validate_python(input_value)
        assert output == expected


def test_from_attributes_type_error():
    v = SchemaValidator(
        {
            'type': 'typed-dict',
            'fields': {'a': {'schema': 'int'}, 'b': {'schema': 'int'}, 'c': {'schema': 'str'}},
            'from_attributes': True,
        }
    )
    with pytest.raises(ValidationError) as exc_info:
        v.validate_python('123')

    assert exc_info.value.errors() == [
        {
            'kind': 'dict_attributes_type',
            'loc': [],
            'message': 'Input should be a valid dictionary or instance to extract fields from',
            'input_value': '123',
        }
    ]


def test_from_attributes_by_name():
    v = SchemaValidator(
        {
            'type': 'typed-dict',
            'return_fields_set': True,
            'fields': {'a': {'schema': 'int', 'alias': 'a_alias'}},
            'from_attributes': True,
            'populate_by_name': True,
        }
    )
    assert v.validate_python(Cls(a_alias=1)) == ({'a': 1}, {'a'})
    assert v.validate_python(Cls(a=1)) == ({'a': 1}, {'a'})


def test_from_attributes_missing():
    class Foobar:
        def __init__(self):
            self.a = 1
            self.b = 2

    v = SchemaValidator(
        {
            'type': 'typed-dict',
            'fields': {'a': {'schema': 'int'}, 'b': {'schema': 'int'}, 'c': {'schema': 'str'}},
            'from_attributes': True,
        }
    )

    with pytest.raises(ValidationError) as exc_info:
        v.validate_python(Foobar())

    assert exc_info.value.errors() == [
        {
            'kind': 'missing',
            'loc': ['c'],
            'message': 'Field required',
            'input_value': HasRepr(IsStr(regex='.+Foobar object at.+')),
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
        {'type': 'typed-dict', 'fields': {'a': {'schema': 'int'}, 'b': {'schema': 'int'}}, 'from_attributes': True}
    )

    with pytest.raises(ValidationError) as exc_info:
        v.validate_python(Foobar())

    assert exc_info.value.errors() == [
        {
            'kind': 'get_attribute_error',
            'loc': ['b'],
            'message': 'Error extracting attribute: RuntimeError: intentional error',
            'input_value': HasRepr(IsStr(regex='.+Foobar object at.+')),
            'context': {'error': 'RuntimeError: intentional error'},
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

        # this is omitted along with the static method by the !PyFunction::is_type_of(attr) check in typed_dict.rs
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
        {
            'type': 'typed-dict',
            'return_fields_set': True,
            'fields': {'a': {'schema': 'int'}},
            'from_attributes': True,
            'extra_behavior': 'allow',
        }
    )

    assert v.validate_python(Foobar()) == ({'a': 1, 'b': 2, 'c': 'ham'}, {'a', 'b', 'c'})
    assert v.validate_python(MyDataclass()) == ({'a': 1, 'b': 2, 'c': 'ham'}, {'a', 'b', 'c'})
    assert v.validate_python(Cls(a=1, b=2, c='ham')) == ({'a': 1, 'b': 2, 'c': 'ham'}, {'a', 'b', 'c'})
    assert v.validate_python(Cls(a=1, b=datetime(2000, 1, 1))) == ({'a': 1, 'b': datetime(2000, 1, 1)}, {'a', 'b'})
    assert v.validate_python(Cls(a=1, b=datetime.now, c=lambda: 42)) == ({'a': 1}, {'a'})


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
    v = SchemaValidator({'type': 'typed-dict', 'fields': {'a': {'schema': 'any'}}, 'from_attributes': True})

    assert v.validate_python(input_value) == expected


def test_from_attributes_error_error():
    class BadError(Exception):
        def __str__(self):
            raise RuntimeError('intentional error inside error')

    class Foobar:
        @property
        def x(self):
            raise BadError('intentional error')

    v = SchemaValidator({'type': 'typed-dict', 'fields': {'x': {'schema': 'int'}}, 'from_attributes': True})

    with pytest.raises(ValidationError) as exc_info:
        v.validate_python(Foobar())

    assert exc_info.value.errors() == [
        {
            'kind': 'get_attribute_error',
            'loc': ['x'],
            'message': IsStr(regex=r'Error extracting attribute: \S+\.<locals>\.BadError: <exception str\(\) failed>'),
            'input_value': HasRepr(IsStr(regex='.+Foobar object at.+')),
            'context': {'error': IsStr(regex=r'\S+\.<locals>\.BadError: <exception str\(\) failed>')},
        }
    ]

    class UnInitError:
        @property
        def x(self):
            raise RuntimeError

    with pytest.raises(ValidationError) as exc_info:
        v.validate_python(UnInitError())

    assert exc_info.value.errors() == [
        {
            'kind': 'get_attribute_error',
            'loc': ['x'],
            'message': 'Error extracting attribute: RuntimeError',
            'input_value': HasRepr(IsStr(regex='.+UnInitError object at.+')),
            'context': {'error': 'RuntimeError'},
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
        (Cls(x='123'), Err(r'my_field\n +Field required \[kind=missing,')),
        (Cls(x={2: 33}), Err(r'my_field\n +Field required \[kind=missing,')),
        (Cls(foo='01234'), Err(r'my_field\n +Field required \[kind=missing,')),
        (Cls(foo=[1]), Err(r'my_field\n +Field required \[kind=missing,')),
        (Cls, Err(r'Input should be a valid dictionary')),
    ],
    ids=repr,
)
def test_from_attributes_path(input_value, expected):
    v = SchemaValidator(
        {
            'type': 'typed-dict',
            'fields': {'my_field': {'alias': [['foo', 'bar', 'bat'], ['foo', 3], ['spam']], 'schema': 'int'}},
            'from_attributes': True,
        }
    )
    if isinstance(expected, Err):
        with pytest.raises(ValidationError, match=expected.message):
            val = v.validate_python(input_value)
            print(f'UNEXPECTED OUTPUT: {val!r}')
    else:
        output = v.validate_python(input_value)
        assert output == expected


def test_from_attributes_path_error():
    class PropertyError:
        @property
        def foo(self):
            raise RuntimeError('intentional error')

    v = SchemaValidator(
        {
            'type': 'typed-dict',
            'fields': {'my_field': {'alias': [['foo', 'bar', 'bat'], ['foo', 3], ['spam']], 'schema': 'int'}},
            'from_attributes': True,
        }
    )
    with pytest.raises(ValidationError) as exc_info:
        v.validate_python(PropertyError())

    assert exc_info.value.errors() == [
        {
            'kind': 'get_attribute_error',
            'loc': ['my_field'],
            'message': 'Error extracting attribute: RuntimeError: intentional error',
            'input_value': HasRepr(IsStr(regex='.+PropertyError object at.+')),
            'context': {'error': 'RuntimeError: intentional error'},
        }
    ]


def test_alias_extra(py_and_json: PyAndJson):
    v = py_and_json(
        {
            'type': 'typed-dict',
            'extra_behavior': 'allow',
            'fields': {'field_a': {'alias': [['FieldA'], ['foo', 2]], 'schema': 'int'}},
        }
    )
    assert v.validate_test({'FieldA': 1}) == {'field_a': 1}
    assert v.validate_test({'foo': [1, 2, 3]}) == {'field_a': 3}

    # used_keys should be populated either though validation fails so "FieldA" is skipped in extra
    with pytest.raises(ValidationError) as exc_info:
        assert v.validate_test({'FieldA': '...'}) == {'field_a': 1}

    assert exc_info.value.errors() == [
        {
            'kind': 'int_parsing',
            'loc': ['field_a'],
            'message': 'Input should be a valid integer, unable to parse string as an integer',
            'input_value': '...',
        }
    ]


def test_alias_extra_from_attributes():
    v = SchemaValidator(
        {
            'type': 'typed-dict',
            'extra_behavior': 'allow',
            'from_attributes': True,
            'fields': {'field_a': {'alias': [['FieldA'], ['foo', 2]], 'schema': 'int'}},
        }
    )
    assert v.validate_python({'FieldA': 1}) == {'field_a': 1}
    assert v.validate_python(Cls(FieldA=1)) == {'field_a': 1}
    assert v.validate_python(Cls(foo=[1, 2, 3])) == {'field_a': 3}
    assert v.validate_python({'foo': [1, 2, 3]}) == {'field_a': 3}


def test_alias_extra_by_name(py_and_json: PyAndJson):
    v = py_and_json(
        {
            'type': 'typed-dict',
            'extra_behavior': 'allow',
            'from_attributes': True,
            'populate_by_name': True,
            'fields': {'field_a': {'alias': 'FieldA', 'schema': 'int'}},
        }
    )
    assert v.validate_test({'FieldA': 1}) == {'field_a': 1}
    assert v.validate_test({'field_a': 1}) == {'field_a': 1}
    assert v.validate_python(Cls(FieldA=1)) == {'field_a': 1}
    assert v.validate_python(Cls(field_a=1)) == {'field_a': 1}


def test_alias_extra_forbid(py_and_json: PyAndJson):
    v = py_and_json(
        {'type': 'typed-dict', 'extra_behavior': 'forbid', 'fields': {'field_a': {'alias': 'FieldA', 'schema': 'int'}}}
    )
    assert v.validate_test({'FieldA': 1}) == {'field_a': 1}


def test_with_default_factory():
    v = SchemaValidator(
        {'type': 'typed-dict', 'fields': {'x': {'schema': {'type': 'str'}, 'default_factory': lambda: 'pikachu'}}}
    )

    assert v.validate_python({}) == {'x': 'pikachu'}
    assert v.validate_python({'x': 'bulbi'}) == {'x': 'bulbi'}


def test_default_and_default_factory():
    """`default` and `default_factory` should not be set together"""
    with pytest.raises(SchemaError, match="'default' and 'default_factory' cannot be used together"):
        SchemaValidator(
            {
                'type': 'typed-dict',
                'fields': {
                    'x': {'schema': {'type': 'str'}, 'default': 'pikachu', 'default_factory': lambda: 'pikachu'}
                },
            }
        )


def test_field_required_and_default_factory():
    """A field cannot be required and have a default factory"""
    with pytest.raises(SchemaError, match="Field 'x': a required field cannot have a default value"):
        SchemaValidator(
            {
                'type': 'typed-dict',
                'fields': {'x': {'schema': {'type': 'str'}, 'required': True, 'default_factory': lambda: 'pika'}},
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
        {'type': 'typed-dict', 'fields': {'x': {'schema': {'type': 'str'}, 'default_factory': default_factory}}}
    )
    with pytest.raises(TypeError, match=re.escape(error_message)):
        v.validate_python({})


class TestOnError:
    def test_on_error_bad_name(self):
        with pytest.raises(SchemaError, match="Input should be one of: 'raise', 'omit', 'fallback_on_default'"):
            SchemaValidator({'type': 'typed-dict', 'fields': {'x': {'schema': {'type': 'str'}, 'on_error': 'rais'}}})

    def test_on_error_bad_omit(self):
        with pytest.raises(SchemaError, match="Field 'x': 'on_error = omit' cannot be set for required fields"):
            SchemaValidator({'type': 'typed-dict', 'fields': {'x': {'schema': {'type': 'str'}, 'on_error': 'omit'}}})

    def test_on_error_bad_fallback_on_default(self):
        with pytest.raises(
            SchemaError, match="Field 'x': 'on_error = fallback_on_default' requires a `default` or `default_factory`"
        ):
            SchemaValidator(
                {'type': 'typed-dict', 'fields': {'x': {'schema': {'type': 'str'}, 'on_error': 'fallback_on_default'}}}
            )

    def test_on_error_raise_by_default(self, py_and_json: PyAndJson):
        v = py_and_json({'type': 'typed-dict', 'fields': {'x': {'schema': {'type': 'str'}}}})
        assert v.validate_test({'x': 'foo'}) == {'x': 'foo'}
        with pytest.raises(ValidationError) as exc_info:
            v.validate_test({'x': ['foo']})
        assert exc_info.value.errors() == [
            {'input_value': ['foo'], 'kind': 'str_type', 'loc': ['x'], 'message': 'Input should be a valid string'}
        ]

    def test_on_error_raise_explicit(self, py_and_json: PyAndJson):
        v = py_and_json({'type': 'typed-dict', 'fields': {'x': {'schema': {'type': 'str'}, 'on_error': 'raise'}}})
        assert v.validate_test({'x': 'foo'}) == {'x': 'foo'}
        with pytest.raises(ValidationError) as exc_info:
            v.validate_test({'x': ['foo']})
        assert exc_info.value.errors() == [
            {'input_value': ['foo'], 'kind': 'str_type', 'loc': ['x'], 'message': 'Input should be a valid string'}
        ]

    def test_on_error_omit(self, py_and_json: PyAndJson):
        v = py_and_json(
            {'type': 'typed-dict', 'fields': {'x': {'schema': {'type': 'str'}, 'on_error': 'omit', 'required': False}}}
        )
        assert v.validate_test({'x': 'foo'}) == {'x': 'foo'}
        assert v.validate_test({}) == {}
        assert v.validate_test({'x': ['foo']}) == {}

    def test_on_error_omit_with_default(self, py_and_json: PyAndJson):
        v = py_and_json(
            {
                'type': 'typed-dict',
                'fields': {'x': {'schema': {'type': 'str'}, 'on_error': 'omit', 'default': 'pika', 'required': False}},
            }
        )
        assert v.validate_test({'x': 'foo'}) == {'x': 'foo'}
        assert v.validate_test({}) == {'x': 'pika'}
        assert v.validate_test({'x': ['foo']}) == {}

    def test_on_error_fallback_on_default(self, py_and_json: PyAndJson):
        v = py_and_json(
            {
                'type': 'typed-dict',
                'fields': {'x': {'schema': {'type': 'str'}, 'on_error': 'fallback_on_default', 'default': 'pika'}},
            }
        )
        assert v.validate_test({'x': 'foo'}) == {'x': 'foo'}
        assert v.validate_test({'x': ['foo']}) == {'x': 'pika'}

    def test_on_error_fallback_on_default_factory(self, py_and_json: PyAndJson):
        v = py_and_json(
            {
                'type': 'typed-dict',
                'fields': {
                    'x': {
                        'schema': {'type': 'str'},
                        'on_error': 'fallback_on_default',
                        'default_factory': lambda: 'pika',
                    }
                },
            }
        )
        assert v.validate_test({'x': 'foo'}) == {'x': 'foo'}
        assert v.validate_test({'x': ['foo']}) == {'x': 'pika'}

    def test_wrap_on_error(self, py_and_json: PyAndJson):
        def wrap_function(input_value, *, validator, **kwargs):
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
                        'schema': {
                            'type': 'function',
                            'mode': 'wrap',
                            'function': wrap_function,
                            'schema': {'type': 'str'},
                        },
                        'on_error': 'raise',
                    }
                },
            }
        )
        assert v.validate_test({'x': 'foo'}) == {'x': 'foo'}
        assert v.validate_test({'x': ['foo']}) == {'x': '1'}
        assert v.validate_test({'x': ['foo', 'bar']}) == {'x': '2'}
        assert v.validate_test({'x': {'a': 'b'}}) == {'x': "{'a': 'b'}"}
