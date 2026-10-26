import re
from collections import Counter
from collections.abc import Mapping

import pytest

from pydantic_core import SchemaValidator, ValidationError
from pydantic_core import core_schema as cs

from ..conftest import Err, PyAndJson


def test_counter(py_and_json: PyAndJson) -> None:
    v = py_and_json({'type': 'counter', 'keys_schema': {'type': 'int'}, 'values_schema': {'type': 'int'}})
    output = v.validate_test({'1': 2, '3': 4})
    assert output == Counter({1: 2, 3: 4})
    if v.validator_type == 'python':
        assert type(output) is Counter
    assert v.validate_test({}) == Counter()
    with pytest.raises(ValidationError, match=re.escape('[type=counter_type, input_value=[], input_type=list]')):
        v.validate_test([])


def test_counter_json_object() -> None:
    # a JSON object is the only way to create a Counter from JSON, so it is allowed in strict mode:
    v = SchemaValidator(cs.counter_schema(cs.str_schema(), cs.int_schema(), strict=True))
    output = v.validate_json('{"a": 1, "b": 2}')
    assert output == Counter({'a': 1, 'b': 2})
    assert type(output) is Counter


@pytest.mark.parametrize(
    ['input_value', 'expected'],
    [
        ({'1': b'1', '2': b'2'}, Counter({'1': '1', '2': '2'})),
        (Counter(a=b'1', b='2'), Counter({'a': '1', 'b': '2'})),
        ({}, Counter()),
        (
            'foobar',
            Err("Input should be a valid Counter [type=counter_type, input_value='foobar', input_type=str]"),
        ),
        ([], Err('Input should be a valid Counter [type=counter_type,')),
        ([('x', 'y')], Err('Input should be a valid Counter [type=counter_type,')),
        ((), Err('Input should be a valid Counter [type=counter_type,')),
        ((type('Foobar', (), {'x': 1})()), Err('Input should be a valid Counter [type=counter_type,')),
    ],
    ids=repr,
)
def test_counter_cases(input_value, expected) -> None:
    v = SchemaValidator(cs.counter_schema(keys_schema=cs.str_schema(), values_schema=cs.str_schema()))
    if isinstance(expected, Err):
        with pytest.raises(ValidationError, match=re.escape(expected.message)):
            v.validate_python(input_value)
    else:
        output = v.validate_python(input_value)
        assert output == expected
        assert type(output) is Counter


def test_counter_input() -> None:
    v = SchemaValidator(cs.counter_schema(keys_schema=cs.str_schema(), values_schema=cs.int_schema()))
    input_value = Counter({'a': '1'})
    output = v.validate_python(input_value)
    assert output == Counter({'a': 1})
    assert type(output) is Counter
    # we don't make any promises about preserving instances, at the moment we always copy them:
    assert output is not input_value


def test_counter_values_preserved() -> None:
    # `Counter.__init__()` must not alter validated values (e.g. by summing counts):
    v = SchemaValidator(cs.counter_schema(keys_schema=cs.str_schema(), values_schema=cs.int_schema()))
    output = v.validate_python({'a': 3, 'b': 0, 'c': -2})
    assert output == Counter({'a': 3, 'b': 0, 'c': -2})
    assert dict(output) == {'a': 3, 'b': 0, 'c': -2}
    assert list(output) == ['a', 'b', 'c']


def test_counter_strict() -> None:
    v = SchemaValidator(cs.counter_schema(keys_schema=cs.str_schema(), values_schema=cs.int_schema(), strict=True))
    output = v.validate_python(Counter({'a': 1}))
    assert output == Counter({'a': 1})
    assert type(output) is Counter

    class DictSubclass(dict):
        pass

    for wrong in ({'a': 1}, DictSubclass(a=1), [('a', 1)]):
        with pytest.raises(ValidationError, match='Input should be a valid Counter'):
            v.validate_python(wrong)


def test_counter_subclass() -> None:
    class CounterSubclass(Counter):
        pass

    v = SchemaValidator(cs.counter_schema(strict=True))
    output = v.validate_python(CounterSubclass({'a': 1}))
    assert output == Counter({'a': 1})
    assert type(output) is Counter


def test_counter_any_mapping() -> None:
    class MyMapping(Mapping):
        def __init__(self, d):
            self._d = d

        def __getitem__(self, key):
            return self._d[key]

        def __iter__(self):
            return iter(self._d)

        def __len__(self):
            return len(self._d)

    v = SchemaValidator(cs.counter_schema(cs.str_schema(), cs.int_schema()))
    output = v.validate_python(MyMapping({'a': '1', 'b': '2'}))
    assert output == Counter({'a': 1, 'b': 2})
    assert type(output) is Counter


def test_counter_key_value_errors(py_and_json: PyAndJson) -> None:
    v = py_and_json({'type': 'counter', 'keys_schema': {'type': 'int'}, 'values_schema': {'type': 'int'}})
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


def test_counter_length_constraints() -> None:
    v = SchemaValidator(cs.counter_schema(min_length=2, max_length=3))
    assert v.validate_python({'a': 1, 'b': 2}) == Counter({'a': 1, 'b': 2})
    with pytest.raises(ValidationError) as exc_info:
        v.validate_python({'a': 1})
    assert exc_info.value.errors(include_url=False) == [
        {
            'type': 'too_short',
            'loc': (),
            'msg': 'Counter should have at least 2 items after validation, not 1',
            'input': {'a': 1},
            'ctx': {'field_type': 'Counter', 'min_length': 2, 'actual_length': 1},
        }
    ]
    with pytest.raises(ValidationError) as exc_info:
        v.validate_python({'a': 1, 'b': 2, 'c': 3, 'd': 4})
    assert exc_info.value.errors(include_url=False)[0]['type'] == 'too_long'


def test_counter_fail_fast() -> None:
    v = SchemaValidator(cs.counter_schema(cs.str_schema(), cs.int_schema(), fail_fast=True))
    with pytest.raises(ValidationError) as exc_info:
        v.validate_python({'a': 'x', 'b': 'y'})
    assert len(exc_info.value.errors(include_url=False)) == 1


def test_counter_smart_union() -> None:
    v = SchemaValidator(cs.union_schema([cs.counter_schema(), cs.dict_schema()]))
    assert type(v.validate_python({'a': 1})) is dict
    assert type(v.validate_python(Counter({'a': 1}))) is Counter


def test_counter_validate_strings() -> None:
    v = SchemaValidator(cs.counter_schema(cs.int_schema(), cs.int_schema()))
    output = v.validate_strings({'1': '2'})
    assert output == Counter({1: 2})
    assert type(output) is Counter


def test_counter_nested() -> None:
    v = SchemaValidator(cs.counter_schema(cs.str_schema(), cs.counter_schema(cs.str_schema(), cs.int_schema())))
    output = v.validate_python({'a': {'b': '1'}})
    assert output == Counter({'a': Counter({'b': 1})})
    assert type(output['a']) is Counter
