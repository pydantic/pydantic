import json

import pytest
from dirty_equals import IsList

from pydantic_core import SchemaSerializer, core_schema


def test_set_any():
    v = SchemaSerializer(core_schema.set_schema(core_schema.any_schema()))
    assert v.to_python({'a', 'b', 'c'}) == {'a', 'b', 'c'}
    assert v.to_python({'a', 'b', 'c'}, mode='json') == IsList('a', 'b', 'c', check_order=False)
    assert json.loads(v.to_json({'a', 'b', 'c'})) == IsList('a', 'b', 'c', check_order=False)


def test_frozenset_any():
    v = SchemaSerializer(core_schema.frozenset_schema(core_schema.any_schema()))
    fs = frozenset(['a', 'b', 'c'])
    output = v.to_python(fs)
    assert output == {'a', 'b', 'c'}
    assert type(output) == frozenset
    assert v.to_python(fs, mode='json') == IsList('a', 'b', 'c', check_order=False)
    assert json.loads(v.to_json(fs)) == IsList('a', 'b', 'c', check_order=False)


@pytest.mark.parametrize(
    'input_value,json_output,warning_type',
    [
        ('apple', 'apple', r'`set\[int\]` but got `str`'),
        ([1, 2, 3], [1, 2, 3], r'`set\[int\]` but got `list`'),
        ((1, 2, 3), [1, 2, 3], r'`set\[int\]` but got `tuple`'),
        (frozenset([1, 2, 3]), IsList(1, 2, 3, check_order=False), r'`set\[int\]` but got `frozenset`'),
        ({1, 2, 'a'}, IsList(1, 2, 'a', check_order=False), '`int` but got `str`'),
    ],
)
def test_set_fallback(input_value, json_output, warning_type):
    v = SchemaSerializer(core_schema.set_schema(core_schema.int_schema()))
    assert v.to_python({1, 2, 3}) == {1, 2, 3}

    with pytest.warns(UserWarning, match=f'Expected {warning_type} - serialized value may not be as expected'):
        assert v.to_python(input_value) == input_value

    with pytest.warns(UserWarning, match=f'Expected {warning_type} - serialized value may not be as expected'):
        assert v.to_python(input_value, mode='json') == json_output

    with pytest.warns(UserWarning, match=f'Expected {warning_type} - serialized value may not be as expected'):
        assert json.loads(v.to_json(input_value)) == json_output
