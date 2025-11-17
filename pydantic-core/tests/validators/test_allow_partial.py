from collections.abc import Mapping

import pytest
from dirty_equals import IsStrictDict
from inline_snapshot import snapshot

from pydantic_core import SchemaValidator, ValidationError, core_schema


def test_list():
    v = SchemaValidator(
        core_schema.list_schema(
            core_schema.tuple_positional_schema([core_schema.int_schema(), core_schema.int_schema()]),
        )
    )
    assert v.validate_python([[1, 2], [3, 4]]) == [(1, 2), (3, 4)]
    assert v.validate_python([[1, 2], [3, 4]], allow_partial=True) == [(1, 2), (3, 4)]
    with pytest.raises(ValidationError) as exc_info:
        v.validate_python([[1, 2], 'wrong'])
    assert exc_info.value.errors(include_url=False) == snapshot(
        [
            {
                'type': 'tuple_type',
                'loc': (1,),
                'msg': 'Input should be a valid tuple',
                'input': 'wrong',
            }
        ]
    )
    assert v.validate_python([[1, 2], 'wrong'], allow_partial=True) == [(1, 2)]
    assert v.validate_python([[1, 2], []], allow_partial=True) == [(1, 2)]
    assert v.validate_python([[1, 2], [3]], allow_partial=True) == [(1, 2)]
    assert v.validate_python([[1, 2], [3, 'x']], allow_partial=True) == [(1, 2)]
    with pytest.raises(ValidationError, match='Input should be a valid tuple'):
        v.validate_python([[1, 2], 'wrong', [3, 4]])
    with pytest.raises(ValidationError, match='Input should be a valid tuple'):
        v.validate_python([[1, 2], 'wrong', 'wrong'])
    assert v.validate_json(b'[[1, 2], [3, 4]]', allow_partial=True) == [(1, 2), (3, 4)]
    assert v.validate_json(b'[[1, 2], [3,', allow_partial=True) == [(1, 2)]


@pytest.mark.parametrize('collection_type', [core_schema.set_schema, core_schema.frozenset_schema])
def test_set_frozenset(collection_type):
    v = SchemaValidator(
        collection_type(
            core_schema.tuple_positional_schema([core_schema.int_schema(), core_schema.int_schema()]),
        )
    )
    assert v.validate_python([[1, 2], [3, 4]]) == snapshot({(1, 2), (3, 4)})
    assert v.validate_python([[1, 2], [3, 4]], allow_partial=True) == snapshot({(1, 2), (3, 4)})
    with pytest.raises(ValidationError) as exc_info:
        v.validate_python([[1, 2], 'wrong'])
    assert exc_info.value.errors(include_url=False) == snapshot(
        [
            {
                'type': 'tuple_type',
                'loc': (1,),
                'msg': 'Input should be a valid tuple',
                'input': 'wrong',
            }
        ]
    )
    assert v.validate_python([[1, 2], 'wrong'], allow_partial=True) == snapshot({(1, 2)})
    assert v.validate_python([[1, 2], [3, 4], 'wrong'], allow_partial=True) == snapshot({(1, 2), (3, 4)})
    assert v.validate_python([[1, 2], []], allow_partial=True) == snapshot({(1, 2)})
    assert v.validate_python([[1, 2], [3]], allow_partial=True) == snapshot({(1, 2)})
    assert v.validate_python([[1, 2], [3, 'x']], allow_partial=True) == snapshot({(1, 2)})
    with pytest.raises(ValidationError, match='Input should be a valid tuple'):
        v.validate_python([[1, 2], 'wrong', [3, 4]])
    with pytest.raises(ValidationError, match='Input should be a valid tuple'):
        v.validate_python([[1, 2], 'wrong', 'wrong'])


class MyMapping(Mapping):
    def __init__(self, d):
        self._d = d

    def __getitem__(self, key):
        return self._d[key]

    def __iter__(self):
        return iter(self._d)

    def __len__(self):
        return len(self._d)


def test_dict():
    v = SchemaValidator(core_schema.dict_schema(core_schema.int_schema(), core_schema.int_schema()))
    assert v.validate_python({'1': 2, 3: '4'}) == snapshot({1: 2, 3: 4})
    assert v.validate_python({'1': 2, 3: '4'}, allow_partial=True) == snapshot({1: 2, 3: 4})
    assert v.validate_python(MyMapping({'1': 2, 3: '4'}), allow_partial=True) == snapshot({1: 2, 3: 4})
    with pytest.raises(ValidationError) as exc_info:
        v.validate_python({'1': 2, 3: 'wrong'})
    assert exc_info.value.errors(include_url=False) == snapshot(
        [
            {
                'type': 'int_parsing',
                'loc': (3,),
                'msg': 'Input should be a valid integer, unable to parse string as an integer',
                'input': 'wrong',
            }
        ]
    )
    assert v.validate_python({'1': 2, 3: 'x'}, allow_partial=True) == snapshot({1: 2})
    assert v.validate_python(MyMapping({'1': 2, 3: 'x'}), allow_partial=True) == snapshot({1: 2})
    assert v.validate_python({'1': 2, 3: 4, 5: '6', 7: 'x'}, allow_partial=True) == snapshot({1: 2, 3: 4, 5: 6})
    with pytest.raises(ValidationError, match='Input should be a valid integer'):
        v.validate_python({'1': 2, 3: 4, 5: 'x', 7: '8'})
    with pytest.raises(ValidationError, match='Input should be a valid integer'):
        v.validate_python({'1': 2, 3: 4, 5: 'x', 7: 'x'})
    with pytest.raises(ValidationError, match='Input should be a valid integer'):
        v.validate_python({'1': 2, 3: 4, 'x': 6})


def test_dict_list():
    v = SchemaValidator(
        core_schema.dict_schema(core_schema.int_schema(), core_schema.list_schema(core_schema.int_schema(ge=10)))
    )
    assert v.validate_python({'1': [20, 30], 3: [40, '50']}, allow_partial=True) == snapshot({1: [20, 30], 3: [40, 50]})
    assert v.validate_python({'1': [20, 30], 3: [40, 5]}, allow_partial=True) == snapshot({1: [20, 30], 3: [40]})

    with pytest.raises(ValidationError, match=r'1\.1\s+Input should be greater than or equal to 10'):
        v.validate_python({'1': [20, 3], 3: [40, 50]}, allow_partial=True)


def test_partial_typed_dict():
    v = SchemaValidator(
        core_schema.typed_dict_schema(
            {
                'a': core_schema.typed_dict_field(core_schema.int_schema(gt=10)),
                'b': core_schema.typed_dict_field(core_schema.int_schema(gt=10)),
                'c': core_schema.typed_dict_field(core_schema.int_schema(gt=10)),
            },
            total=False,
        )
    )

    assert v.validate_python({'a': 11, 'b': '12', 'c': 13}) == snapshot(IsStrictDict(a=11, b=12, c=13))
    assert v.validate_python({'a': 11, 'c': 13, 'b': '12'}) == snapshot(IsStrictDict(a=11, b=12, c=13))
    assert v.validate_python(MyMapping({'a': 11, 'c': 13, 'b': '12'})) == snapshot(IsStrictDict(a=11, b=12, c=13))

    assert v.validate_python({'a': 11, 'b': '12', 'c': 13}, allow_partial=True) == snapshot({'a': 11, 'b': 12, 'c': 13})
    with pytest.raises(ValidationError) as exc_info:
        v.validate_python({'a': 11, 'b': '12', 'c': 1})
    assert exc_info.value.errors(include_url=False) == snapshot(
        [
            {
                'type': 'greater_than',
                'loc': ('c',),
                'msg': 'Input should be greater than 10',
                'input': 1,
                'ctx': {'gt': 10},
            }
        ]
    )
    assert v.validate_python({'a': 11, 'b': '12', 'c': 1}, allow_partial=True) == snapshot(IsStrictDict(a=11, b=12))
    assert v.validate_python(MyMapping({'a': 11, 'b': '12', 'c': 1}), allow_partial=True) == snapshot(
        IsStrictDict(a=11, b=12)
    )
    assert v.validate_python({'a': 11, 'c': 13, 'b': 1}, allow_partial=True) == snapshot(IsStrictDict(a=11, c=13))
    with pytest.raises(ValidationError) as exc_info:
        v.validate_python({'a': 11, 'c': 1, 'b': 12}, allow_partial=True)
    assert exc_info.value.errors(include_url=False) == snapshot(
        [
            {
                'type': 'greater_than',
                'loc': ('c',),
                'msg': 'Input should be greater than 10',
                'input': 1,
                'ctx': {'gt': 10},
            }
        ]
    )
    with pytest.raises(ValidationError, match=r'c\s+Input should be greater than 10'):
        v.validate_python(MyMapping({'a': 11, 'c': 1, 'b': 12}), allow_partial=True)

    # validate strings
    assert v.validate_strings({'a': '11', 'b': '22'}) == snapshot({'a': 11, 'b': 22})
    with pytest.raises(ValidationError, match='Input should be greater than 10'):
        v.validate_strings({'a': '11', 'b': '2'})
    assert v.validate_strings({'a': '11', 'b': '2'}, allow_partial=True) == snapshot({'a': 11})

    assert v.validate_json(b'{"b": "12", "a": 11, "c": 13}', allow_partial=True) == IsStrictDict(a=11, b=12, c=13)
    assert v.validate_json(b'{"b": "12", "a": 11, "c": 13', allow_partial=True) == IsStrictDict(a=11, b=12, c=13)
    assert v.validate_json(b'{"a": 11, "b": "12", "c": 1', allow_partial=True) == IsStrictDict(a=11, b=12)
    assert v.validate_json(b'{"a": 11, "b": "12", "c":', allow_partial=True) == IsStrictDict(a=11, b=12)
    assert v.validate_json(b'{"a": 11, "b": "12", "c"', allow_partial=True) == IsStrictDict(a=11, b=12)
    assert v.validate_json(b'{"a": 11, "b": "12", "c', allow_partial=True) == IsStrictDict(a=11, b=12)
    assert v.validate_json(b'{"a": 11, "b": "12", "', allow_partial=True) == IsStrictDict(a=11, b=12)
    assert v.validate_json(b'{"a": 11, "b": "12", ', allow_partial=True) == IsStrictDict(a=11, b=12)
    assert v.validate_json(b'{"a": 11, "b": "12",', allow_partial=True) == IsStrictDict(a=11, b=12)
    assert v.validate_json(b'{"a": 11, "b": "12"', allow_partial=True) == IsStrictDict(a=11, b=12)


def test_non_partial_typed_dict():
    v = SchemaValidator(
        core_schema.typed_dict_schema(
            {
                'a': core_schema.typed_dict_field(core_schema.int_schema(gt=10)),
                'b': core_schema.typed_dict_field(core_schema.int_schema(gt=10), required=True),
                'c': core_schema.typed_dict_field(core_schema.int_schema(gt=10)),
            },
            total=False,
        )
    )

    assert v.validate_python({'a': 11, 'b': '12', 'c': 13}) == snapshot({'a': 11, 'b': 12, 'c': 13})
    with pytest.raises(ValidationError, match='Input should be greater than 10'):
        v.validate_python({'a': 11, 'b': '12', 'c': 1})
    assert v.validate_python({'a': 11, 'b': '12', 'c': 1}, allow_partial=True) == snapshot({'a': 11, 'b': 12})
    with pytest.raises(ValidationError, match=r'b\s+Field required'):
        v.validate_python({'a': 11, 'c': 12}, allow_partial=True)
    with pytest.raises(ValidationError, match=r'b\s+Input should be greater than 10'):
        v.validate_python({'a': 11, 'c': 12, 'b': 1}, allow_partial=True)


def test_double_nested():
    v = SchemaValidator(
        core_schema.typed_dict_schema(
            {
                'a': core_schema.typed_dict_field(core_schema.int_schema(gt=10)),
                'b': core_schema.typed_dict_field(
                    core_schema.list_schema(
                        core_schema.dict_schema(core_schema.str_schema(), core_schema.int_schema(ge=10))
                    )
                ),
            },
            total=False,
        )
    )
    assert v.validate_python({'a': 11, 'b': [{'a': 10, 'b': 20}, {'a': 30, 'b': 40}]}) == snapshot(
        {'a': 11, 'b': [{'a': 10, 'b': 20}, {'a': 30, 'b': 40}]}
    )
    assert v.validate_python({'a': 11, 'b': [{'a': 10, 'b': 20}, {'a': 30, 'b': 4}]}, allow_partial=True) == snapshot(
        {'a': 11, 'b': [{'a': 10, 'b': 20}, {'a': 30}]}
    )
    assert v.validate_python({'a': 11, 'b': [{'a': 10, 'b': 20}, {'a': 30, 123: 4}]}, allow_partial=True) == snapshot(
        {'a': 11, 'b': [{'a': 10, 'b': 20}]}
    )
    # the first element of the list is invalid, so the whole list is invalid
    assert v.validate_python({'a': 11, 'b': [{'a': 10, 'b': 2}, {'a': 30}]}, allow_partial=True) == snapshot({'a': 11})
    with pytest.raises(ValidationError, match=r'b\.0\.b\s+Input should be greater than or equal to 10'):
        v.validate_python({'b': [{'a': 10, 'b': 2}, {'a': 30}], 'a': 11}, allow_partial=True)

    with pytest.raises(ValidationError, match=r'b\.1\.a\s+Input should be greater than or equal to 10'):
        v.validate_python({'b': [{'a': 10, 'b': 20}, {'a': 3}], 'a': 11}, allow_partial=True)

    assert v.validate_python({'a': 11, 'b': [{'a': 1, 'b': 20}, {'a': 3, 'b': 40}]}, allow_partial=True) == snapshot(
        {'a': 11}
    )
    json = b'{"a": 11, "b": [{"a": 10, "b": 20}, {"a": 30, "b": 40}]}'
    assert v.validate_json(json, allow_partial=True) == snapshot(
        {'a': 11, 'b': [{'a': 10, 'b': 20}, {'a': 30, 'b': 40}]}
    )
    for i in range(1, len(json)):
        value = v.validate_json(json[:i], allow_partial=True)
        assert isinstance(value, dict)


def test_tuple_list():
    """Tuples don't support partial, so behaviour should be disabled."""
    v = SchemaValidator(
        core_schema.tuple_positional_schema(
            [core_schema.list_schema(core_schema.int_schema()), core_schema.int_schema()]
        )
    )
    assert v.validate_python([['1', '2'], '3'], allow_partial=True) == snapshot(([1, 2], 3))
    with pytest.raises(ValidationError, match=r'1\s+Input should be a valid integer'):
        v.validate_python([['1', '2'], 'x'], allow_partial=True)
    with pytest.raises(ValidationError, match=r'0\.1\s+Input should be a valid integer'):
        v.validate_python([['1', 'x'], '2'], allow_partial=True)


def test_dataclass():
    """Tuples don't support partial, so behaviour should be disabled."""

    schema = core_schema.dataclass_args_schema(
        'MyDataclass',
        [
            core_schema.dataclass_field(name='a', schema=core_schema.str_schema(), kw_only=False),
            core_schema.dataclass_field(
                name='b', schema=core_schema.list_schema(core_schema.str_schema(min_length=2)), kw_only=False
            ),
        ],
    )
    v = SchemaValidator(schema)
    assert v.validate_python({'a': 'x', 'b': ['ab', 'cd']}) == snapshot(({'a': 'x', 'b': ['ab', 'cd']}, None))
    assert v.validate_python({'a': 'x', 'b': ['ab', 'cd']}, allow_partial=True) == snapshot(
        ({'a': 'x', 'b': ['ab', 'cd']}, None)
    )
    with pytest.raises(ValidationError, match=r'b\.1\s+String should have at least 2 characters'):
        v.validate_python({'a': 'x', 'b': ['ab', 'c']}, allow_partial=True)


def test_nullable():
    v = SchemaValidator(core_schema.nullable_schema(core_schema.list_schema(core_schema.str_schema(min_length=2))))

    assert v.validate_python(None, allow_partial=True) is None
    assert v.validate_python(['ab', 'cd'], allow_partial=True) == ['ab', 'cd']
    assert v.validate_python(['ab', 'c'], allow_partial=True) == ['ab']
    assert v.validate_json('["ab", "cd"]', allow_partial=True) == ['ab', 'cd']
    assert v.validate_json('["ab", "cd', allow_partial=True) == ['ab']
    assert v.validate_json('["ab", "cd', allow_partial='trailing-strings') == ['ab', 'cd']
    assert v.validate_json('["ab", "c', allow_partial=True) == ['ab']
    assert v.validate_json('["ab", "c', allow_partial='trailing-strings') == ['ab']


@pytest.mark.parametrize(
    'json_nested_type', [None, core_schema.dict_schema(core_schema.str_schema(), core_schema.int_schema())]
)
def test_json(json_nested_type):
    v = SchemaValidator(core_schema.list_schema(core_schema.json_schema(json_nested_type)))

    assert v.validate_python(['{"a": 1}', '{"b": 2}']) == snapshot([{'a': 1}, {'b': 2}])
    assert v.validate_python(['{"a": 1}', '{"b": 2}'], allow_partial=True) == snapshot([{'a': 1}, {'b': 2}])
    assert v.validate_python(['{"a": 1}', 'xxx'], allow_partial=True) == snapshot([{'a': 1}])
    assert v.validate_python(['{"a": 1}', '{"b": 2'], allow_partial=True) == snapshot([{'a': 1}, {'b': 2}])
    assert v.validate_json('["{\\"a\\": 1}", "{\\"b\\": 2}', allow_partial='trailing-strings') == snapshot(
        [{'a': 1}, {'b': 2}]
    )
    assert v.validate_json('["{\\"a\\": 1}", "{\\"b\\": 2', allow_partial='trailing-strings') == snapshot(
        [{'a': 1}, {'b': 2}]
    )


def test_json_trailing_strings():
    v = SchemaValidator(core_schema.list_schema(core_schema.json_schema()))
    assert v.validate_python(['{"a": 1}', '{"b": "x'], allow_partial=True) == snapshot([{'a': 1}, {}])
    assert v.validate_python(['{"a": 1}', '{"b": "x'], allow_partial='trailing-strings') == snapshot(
        [{'a': 1}, {'b': 'x'}]
    )

    assert v.validate_json('["{\\"a\\": 1}", "{\\"b\\": 2}"]') == snapshot([{'a': 1}, {'b': 2}])
    assert v.validate_json('["{\\"a\\": 1}", "{\\"b\\": 2, \\"c\\": \\"x', allow_partial=True) == snapshot([{'a': 1}])
    assert v.validate_json(
        '["{\\"a\\": 1}", "{\\"b\\": 2, \\"c\\": \\"x', allow_partial='trailing-strings'
    ) == snapshot([{'a': 1}, {'b': 2, 'c': 'x'}])
