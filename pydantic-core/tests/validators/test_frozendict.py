import re
import sys
from collections import OrderedDict
from collections.abc import Mapping

import pytest

from pydantic_core import SchemaValidator, ValidationError
from pydantic_core import core_schema as cs

from ..conftest import Err, PyAndJson

if sys.version_info < (3, 15):
    pytest.skip(reason='The `frozendict` builtin type is only available in Python 3.15+', allow_module_level=True)
else:
    from builtins import frozendict


def test_frozendict(py_and_json: PyAndJson):
    v = py_and_json({'type': 'frozendict', 'keys_schema': {'type': 'int'}, 'values_schema': {'type': 'int'}})
    output = v.validate_test({'1': 2, '3': 4})
    assert output == frozendict({1: 2, 3: 4})
    if v.validator_type == 'python':
        assert isinstance(output, frozendict)
    assert v.validate_test({}) == frozendict()
    with pytest.raises(ValidationError, match=re.escape('[type=frozen_dict_type, input_value=[], input_type=list]')):
        v.validate_test([])


def test_frozendict_json_object():
    # a JSON object is the only way to create a frozendict from JSON, so it is allowed in strict mode:
    v = SchemaValidator(cs.frozendict_schema(cs.str_schema(), cs.int_schema(), strict=True))
    output = v.validate_json('{"a": 1}')
    assert output == frozendict({'a': 1})
    assert isinstance(output, frozendict)


@pytest.mark.parametrize(
    'input_value,expected',
    [
        ({'1': b'1', '2': b'2'}, frozendict({'1': '1', '2': '2'})),
        (OrderedDict(a=b'1', b='2'), frozendict({'a': '1', 'b': '2'})),
        ({}, frozendict()),
        (
            'foobar',
            Err("Input should be a valid frozendict [type=frozen_dict_type, input_value='foobar', input_type=str]"),
        ),
        ([], Err('Input should be a valid frozendict [type=frozen_dict_type,')),
        ([('x', 'y')], Err('Input should be a valid frozendict [type=frozen_dict_type,')),
        ((), Err('Input should be a valid frozendict [type=frozen_dict_type,')),
        ((type('Foobar', (), {'x': 1})()), Err('Input should be a valid frozendict [type=frozen_dict_type,')),
    ],
    ids=repr,
)
def test_frozendict_cases(input_value, expected):
    v = SchemaValidator(cs.frozendict_schema(keys_schema=cs.str_schema(), values_schema=cs.str_schema()))
    if isinstance(expected, Err):
        with pytest.raises(ValidationError, match=re.escape(expected.message)):
            v.validate_python(input_value)
    else:
        output = v.validate_python(input_value)
        assert output == expected
        assert isinstance(output, frozendict)


def test_frozendict_input():
    v = SchemaValidator(cs.frozendict_schema(keys_schema=cs.str_schema(), values_schema=cs.int_schema()))
    output = v.validate_python(frozendict({'a': '1'}))
    assert output == frozendict({'a': 1})
    assert isinstance(output, frozendict)


def test_frozendict_strict():
    v = SchemaValidator(cs.frozendict_schema(keys_schema=cs.str_schema(), values_schema=cs.int_schema(), strict=True))
    output = v.validate_python(frozendict({'a': 1}))
    assert output == frozendict({'a': 1})
    for wrong in ({'a': 1}, OrderedDict(a=1), [('a', 1)]):
        with pytest.raises(ValidationError, match='Input should be a valid frozendict'):
            v.validate_python(wrong)


def test_frozendict_subclass():
    class FrozenDictSubclass(frozendict):
        pass

    v = SchemaValidator(cs.frozendict_schema(strict=True))
    assert v.validate_python(FrozenDictSubclass({'a': 1})) == frozendict({'a': 1})


def test_frozendict_any_mapping():
    class MyMapping(Mapping):
        def __init__(self, d):
            self._d = d

        def __getitem__(self, key):
            return self._d[key]

        def __iter__(self):
            return iter(self._d)

        def __len__(self):
            return len(self._d)

    v = SchemaValidator(cs.frozendict_schema(cs.str_schema(), cs.int_schema()))
    output = v.validate_python(MyMapping({'a': '1'}))
    assert output == frozendict({'a': 1})
    assert isinstance(output, frozendict)


def test_frozendict_key_value_errors(py_and_json: PyAndJson):
    v = py_and_json({'type': 'frozendict', 'keys_schema': {'type': 'int'}, 'values_schema': {'type': 'int'}})
    with pytest.raises(ValidationError) as exc_info:
        v.validate_test({'wrong': 1, '2': 'also wrong'})
    assert exc_info.value.errors(include_url=False) == [
        {
            'type': 'int_parsing',
            'loc': ('wrong', '[key]'),
            'msg': 'Input should be a valid integer, unable to parse string as an integer',
            'input': 'wrong',
        },
        {
            'type': 'int_parsing',
            'loc': ('2',),
            'msg': 'Input should be a valid integer, unable to parse string as an integer',
            'input': 'also wrong',
        },
    ]


def test_frozendict_length_constraints():
    v = SchemaValidator(cs.frozendict_schema(min_length=2, max_length=3))
    assert v.validate_python({'a': 1, 'b': 2}) == frozendict({'a': 1, 'b': 2})
    with pytest.raises(ValidationError) as exc_info:
        v.validate_python({'a': 1})
    assert exc_info.value.errors(include_url=False)[0]['type'] == 'too_short'
    with pytest.raises(ValidationError) as exc_info:
        v.validate_python({'a': 1, 'b': 2, 'c': 3, 'd': 4})
    assert exc_info.value.errors(include_url=False)[0]['type'] == 'too_long'


def test_frozendict_fail_fast():
    v = SchemaValidator(cs.frozendict_schema(cs.str_schema(), cs.int_schema(), fail_fast=True))
    with pytest.raises(ValidationError) as exc_info:
        v.validate_python({'a': 'x', 'b': 'y'})
    assert len(exc_info.value.errors(include_url=False)) == 1


def test_frozendict_hashable_output():
    v = SchemaValidator(cs.frozendict_schema())
    output = v.validate_python({'a': 1})
    assert hash(output) == hash(frozendict({'a': 1}))


def test_frozendict_smart_union():
    v = SchemaValidator(cs.union_schema([cs.frozendict_schema(), cs.dict_schema()]))
    assert type(v.validate_python({'a': 1})) is dict
    assert type(v.validate_python(frozendict({'a': 1}))) is frozendict


def test_frozendict_validate_strings():
    v = SchemaValidator(cs.frozendict_schema(cs.int_schema(), cs.int_schema()))
    output = v.validate_strings({'1': '2'})
    assert output == frozendict({1: 2})
    assert isinstance(output, frozendict)
