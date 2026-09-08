import json
from collections import deque

import pytest

from pydantic_core import SchemaSerializer, core_schema


def test_deque_any() -> None:
    v = SchemaSerializer(core_schema.deque_schema(core_schema.any_schema()))
    d = deque(['a', 'b', 'c'])
    output = v.to_python(d)

    assert output == d
    assert type(output) is deque
    assert output is not d
    assert v.to_python(d, mode='json') == ['a', 'b', 'c']
    assert v.to_json(d) == b'["a","b","c"]'
    assert v.to_json(d, indent=2) == b'[\n  "a",\n  "b",\n  "c"\n]'


def test_deque_maxlen_preserved() -> None:
    v = SchemaSerializer(core_schema.deque_schema(core_schema.int_schema()))
    d = deque([1, 2, 3], maxlen=5)

    output = v.to_python(d)
    assert output == d
    assert output.maxlen == 5
    assert v.to_python(deque([1, 2, 3])).maxlen is None
    assert v.to_python(d, mode='json') == [1, 2, 3]


def test_deque_int() -> None:
    v = SchemaSerializer(core_schema.deque_schema(core_schema.int_schema()))

    assert v.to_python(deque([1, 2, 3])) == deque([1, 2, 3])
    assert v.to_python(deque([1, 2, 3]), mode='json') == [1, 2, 3]
    assert v.to_json(deque([1, 2, 3])) == b'[1,2,3]'


@pytest.mark.parametrize(
    ['input_value', 'json_output', 'expected_type'],
    [
        ('apple', 'apple', r'deque\[int\]'),
        ([1, 2, 3], [1, 2, 3], r'deque\[int\]'),
        ((1, 2, 3), [1, 2, 3], r'deque\[int\]'),
        (deque([1, 2, 'a']), [1, 2, 'a'], 'int'),
    ],
)
def test_deque_fallback(input_value, json_output, expected_type):
    v = SchemaSerializer(core_schema.deque_schema(core_schema.int_schema()))
    assert v.to_python(deque([1, 2, 3])) == deque([1, 2, 3])

    with pytest.warns(UserWarning, match=f'Expected `{expected_type}` - serialized value may not be as expected'):
        assert v.to_python(input_value) == input_value

    with pytest.warns(UserWarning, match=f'Expected `{expected_type}` - serialized value may not be as expected'):
        assert v.to_python(input_value, mode='json') == json_output

    with pytest.warns(UserWarning, match=f'Expected `{expected_type}` - serialized value may not be as expected'):
        assert json.loads(v.to_json(input_value)) == json_output


def test_deque_include_exclude() -> None:
    v = SchemaSerializer(core_schema.deque_schema(core_schema.int_schema()))
    d = deque([0, 1, 2, 3], maxlen=6)

    assert v.to_python(d, include={0, 2}) == deque([0, 2], maxlen=6)
    assert v.to_python(d, exclude={0, 2}) == deque([1, 3], maxlen=6)
    assert v.to_python(d, include={0, 2}, mode='json') == [0, 2]
    assert v.to_json(d, include={-1}) == b'[3]'
    assert v.to_json(d, exclude={-1}) == b'[0,1,2]'


def test_deque_filter_schema() -> None:
    v = SchemaSerializer(
        core_schema.deque_schema(core_schema.int_schema(), serialization=core_schema.filter_seq_schema(exclude={1}))
    )
    assert v.to_python(deque([0, 1, 2])) == deque([0, 2])
    assert v.to_json(deque([0, 1, 2])) == b'[0,2]'


def test_deque_nested() -> None:
    v = SchemaSerializer(
        core_schema.dict_schema(core_schema.str_schema(), core_schema.deque_schema(core_schema.int_schema()))
    )
    assert v.to_python({'a': deque([1, 2])}) == {'a': deque([1, 2])}
    assert v.to_json({'a': deque([1, 2])}) == b'{"a":[1,2]}'


def test_deque_subclass() -> None:
    class MyDeque(deque):
        pass

    v = SchemaSerializer(core_schema.deque_schema(core_schema.int_schema()))
    output = v.to_python(MyDeque([1, 2]))
    assert output == deque([1, 2])
    assert type(output) is deque
    assert v.to_json(MyDeque([1, 2])) == b'[1,2]'
