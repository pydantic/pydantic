import json
import re
from functools import partial

import pytest

from pydantic_core import SchemaError, SchemaSerializer, core_schema


def test_list_any():
    v = SchemaSerializer(core_schema.list_schema(core_schema.any_schema()))
    assert v.to_python(['a', 'b', 'c']) == ['a', 'b', 'c']
    assert v.to_python(['a', 'b', 'c'], mode='json') == ['a', 'b', 'c']
    assert v.to_json(['a', 'b', 'c']) == b'["a","b","c"]'

    assert v.to_json(['a', 'b', 'c'], indent=2) == b'[\n  "a",\n  "b",\n  "c"\n]'


def test_list_fallback():
    v = SchemaSerializer(core_schema.list_schema(core_schema.any_schema()))
    msg = 'Expected `list[any]` but got `str` - serialized value may not be as expected'
    with pytest.warns(UserWarning, match=re.escape(msg)):
        assert v.to_python('apple') == 'apple'

    with pytest.warns(UserWarning) as warning_info:
        assert v.to_json('apple') == b'"apple"'
    assert [w.message.args[0] for w in warning_info.list] == [
        'Pydantic serializer warnings:\n  Expected `list[any]` but got `str` - serialized value may not be as expected'
    ]

    msg = 'Expected `list[any]` but got `bytes` - serialized value may not be as expected'
    with pytest.warns(UserWarning, match=re.escape(msg)):
        assert v.to_json(b'apple') == b'"apple"'

    msg = 'Expected `list[any]` but got `tuple` - serialized value may not be as expected'
    with pytest.warns(UserWarning, match=re.escape(msg)):
        assert v.to_python((1, 2, 3)) == (1, 2, 3)

    # # even though we're in the fallback state, non JSON types should still be converted to JSON here
    msg = 'Expected `list[any]` but got `tuple` - serialized value may not be as expected'
    with pytest.warns(UserWarning, match=re.escape(msg)):
        assert v.to_python((1, 2, 3), mode='json') == [1, 2, 3]


def test_list_str_fallback():
    v = SchemaSerializer(core_schema.list_schema(core_schema.str_schema()))
    with pytest.warns(UserWarning) as warning_info:
        assert v.to_json([1, 2, 3]) == b'[1,2,3]'
    assert [w.message.args[0] for w in warning_info.list] == [
        'Pydantic serializer warnings:\n'
        '  Expected `str` but got `int` - serialized value may not be as expected\n'
        '  Expected `str` but got `int` - serialized value may not be as expected\n'
        '  Expected `str` but got `int` - serialized value may not be as expected'
    ]


def test_tuple_any():
    v = SchemaSerializer(core_schema.tuple_variable_schema(core_schema.any_schema()))
    assert v.to_python(('a', 'b', 'c')) == ('a', 'b', 'c')
    assert v.to_python(('a', 'b', 'c'), mode='json') == ['a', 'b', 'c']
    assert v.to_json(('a', 'b', 'c')) == b'["a","b","c"]'

    assert v.to_json(('a', 'b', 'c'), indent=2) == b'[\n  "a",\n  "b",\n  "c"\n]'


def as_list(*items):
    return list(items)


def as_tuple(*items):
    return tuple(items)


@pytest.mark.parametrize(
    'schema_func,seq_f', [(core_schema.list_schema, as_list), (core_schema.tuple_variable_schema, as_tuple)]
)
def test_include(schema_func, seq_f):
    v = SchemaSerializer(
        schema_func(core_schema.any_schema(), serialization=core_schema.filter_seq_schema(include={1, 3, 5}))
    )
    assert v.to_python(seq_f(0, 1, 2, 3)) == seq_f(1, 3)
    assert v.to_python(seq_f('a', 'b', 'c', 'd', 'e', 'f', 'g', 'h')) == seq_f('b', 'd', 'f')
    assert v.to_python(seq_f('a', 'b', 'c', 'd', 'e', 'f', 'g', 'h'), mode='json') == ['b', 'd', 'f']
    assert v.to_json(seq_f('a', 'b', 'c', 'd', 'e', 'f', 'g', 'h')) == b'["b","d","f"]'
    # the two include lists are now combined via UNION! unlike in pydantic v1
    assert v.to_python(seq_f('a', 'b', 'c', 'd', 'e', 'f', 'g', 'h'), include={6}) == seq_f('b', 'd', 'f', 'g')
    assert v.to_python(seq_f('a', 'b', 'c', 'd', 'e', 'f', 'g', 'h'), include=[6]) == seq_f('b', 'd', 'f', 'g')
    assert v.to_json(seq_f('a', 'b', 'c', 'd', 'e', 'f', 'g', 'h'), include={6}) == b'["b","d","f","g"]'
    assert v.to_python(seq_f('a', 'b', 'c', 'd', 'e', 'f', 'g', 'h'), include={6: None}) == seq_f('b', 'd', 'f', 'g')
    assert v.to_python(seq_f('a', 'b', 'c', 'd', 'e', 'f', 'g', 'h'), include={-1: None, -2: None}, mode='json') == [
        'b',
        'd',
        'f',
        'g',
        'h',
    ]


@pytest.mark.parametrize(
    'schema_func,seq_f', [(core_schema.list_schema, as_list), (core_schema.tuple_variable_schema, as_tuple)]
)
def test_negative(schema_func, seq_f):
    v = SchemaSerializer(schema_func(core_schema.any_schema()))
    assert v.to_python(seq_f('a', 'b', 'c', 'd', 'e')) == seq_f('a', 'b', 'c', 'd', 'e')
    assert v.to_python(seq_f('a', 'b', 'c', 'd', 'e'), include={-1, -2}) == seq_f('d', 'e')
    assert v.to_python(seq_f('a', 'b', 'c', 'd', 'e'), include={-1: None, -2: None}) == seq_f('d', 'e')
    assert v.to_python(seq_f('a', 'b', 'c', 'd', 'e'), include={-1, -2}, mode='json') == ['d', 'e']
    assert v.to_python(seq_f('a', 'b', 'c', 'd', 'e'), include={-1: None, -2: None}, mode='json') == ['d', 'e']
    assert v.to_json(seq_f('a', 'b', 'c', 'd', 'e'), include={-1, -2}) == b'["d","e"]'


@pytest.mark.parametrize(
    'schema_func,seq_f', [(core_schema.list_schema, as_list), (core_schema.tuple_variable_schema, as_tuple)]
)
def test_include_dict(schema_func, seq_f):
    v = SchemaSerializer(
        schema_func(core_schema.any_schema(), serialization=core_schema.filter_seq_schema(include={1, 3, 5}))
    )
    assert v.to_python(seq_f(0, 1, 2, 3, 4)) == seq_f(1, 3)
    assert v.to_python(seq_f('a', 'b', 'c', 'd', 'e', 'f', 'g', 'h')) == seq_f('b', 'd', 'f')
    assert v.to_python(seq_f(0, 1, 2, 3, 4), include={2: None}) == seq_f(1, 2, 3)
    assert v.to_python(seq_f(0, 1, 2, 3, 4), include={2: {1, 2}}) == seq_f(1, 2, 3)
    assert v.to_python(seq_f(0, 1, 2, 3, 4), include={2}) == seq_f(1, 2, 3)


@pytest.mark.parametrize(
    'schema_func,seq_f', [(core_schema.list_schema, as_list), (core_schema.tuple_variable_schema, as_tuple)]
)
def test_exclude(schema_func, seq_f):
    v = SchemaSerializer(
        schema_func(core_schema.any_schema(), serialization=core_schema.filter_seq_schema(exclude={1, 3, 5}))
    )
    assert v.to_python(seq_f(0, 1, 2, 3)) == seq_f(0, 2)
    assert v.to_python(seq_f('a', 'b', 'c', 'd', 'e', 'f', 'g', 'h')) == seq_f('a', 'c', 'e', 'g', 'h')
    assert v.to_python(seq_f('a', 'b', 'c', 'd', 'e', 'f', 'g', 'h'), mode='json') == ['a', 'c', 'e', 'g', 'h']
    assert v.to_json(seq_f('a', 'b', 'c', 'd', 'e', 'f', 'g', 'h')) == b'["a","c","e","g","h"]'
    # the two exclude lists are combined via union as they used to be
    assert v.to_python(seq_f('a', 'b', 'c', 'd', 'e', 'f', 'g', 'h'), exclude={6}) == seq_f('a', 'c', 'e', 'h')
    assert v.to_python(seq_f('a', 'b', 'c', 'd', 'e', 'f', 'g', 'h'), exclude={-1, -2}) == seq_f('a', 'c', 'e')
    assert v.to_json(seq_f('a', 'b', 'c', 'd', 'e', 'f', 'g', 'h'), exclude={6}) == b'["a","c","e","h"]'
    assert v.to_json(seq_f('a', 'b', 'c', 'd', 'e', 'f', 'g', 'h'), exclude={-1, -2}) == b'["a","c","e"]'


@pytest.mark.parametrize('include,exclude', [({1, 3, 5}, {5, 6}), ([1, 3, 5], [5, 6])])
def test_filter(include, exclude):
    v = SchemaSerializer(
        core_schema.list_schema(
            core_schema.any_schema(), serialization=core_schema.filter_seq_schema(include=include, exclude=exclude)
        )
    )
    assert v.to_python([0, 1, 2, 3, 4, 5, 6, 7]) == [1, 3]


def test_filter_runtime():
    v = SchemaSerializer(
        core_schema.list_schema(core_schema.any_schema(), serialization=core_schema.filter_seq_schema(exclude={0, 1}))
    )
    assert v.to_python([0, 1, 2, 3]) == [2, 3]
    # `include` as a call argument trumps schema `exclude`
    assert v.to_python([0, 1, 2, 3], include={1, 2}) == [1, 2]


class ImplicitContains:
    def __iter__(self):
        return iter([1, 2, 5])


class ExplicitContains(ImplicitContains):
    def __contains__(self, item):
        return item in {2, 5}


class RemovedContains(ImplicitContains):
    __contains__ = None  # This might be done to explicitly force the `x in RemovedContains()` check to not be allowed


@pytest.mark.parametrize(
    'include_value,error_msg',
    [
        ('foobar', 'Input should be a valid set'),
        ({'a': 'dict'}, 'Input should be a valid set'),
        ({4.2}, 'Input should be a valid integer, got a number with a fractional part'),
        ({'a'}, 'Input should be a valid integer, unable to parse string as an integer'),
    ],
)
@pytest.mark.parametrize('schema_func', [core_schema.list_schema, core_schema.tuple_variable_schema])
def test_include_error(schema_func, include_value, error_msg):
    with pytest.raises(SchemaError, match=error_msg):
        SchemaSerializer(
            schema_func(core_schema.any_schema(), serialization=core_schema.filter_seq_schema(include=include_value))
        )


@pytest.mark.parametrize(
    'include,exclude,expected',
    [
        ({1, 3}, None, ['b', 'd']),
        ({1, 3, 5}, {5}, ['b', 'd']),
        ({2: None, 3: None, 5: None}.keys(), {5}, ['c', 'd']),
        (ExplicitContains(), set(), ['c', 'f']),
        (ExplicitContains(), {5}, ['c']),
        ({2, 3}, ExplicitContains(), ['d']),
        ([1, 2, 3], [2, 3], ['b']),
    ],
)
def test_filter_runtime_more(include, exclude, expected):
    v = SchemaSerializer(core_schema.list_schema(core_schema.any_schema()))
    assert v.to_python(list('abcdefgh'), include=include, exclude=exclude) == expected


@pytest.mark.parametrize(
    'schema_func,seq_f', [(core_schema.list_schema, as_list), (core_schema.tuple_variable_schema, as_tuple)]
)
@pytest.mark.parametrize(
    'include,exclude',
    [
        (ImplicitContains(), None),
        (RemovedContains(), None),
        (1, None),
        (None, ImplicitContains()),
        (None, RemovedContains()),
        (None, 1),
    ],
)
def test_include_error_call_time(schema_func, seq_f, include, exclude):
    kind = 'include' if include is not None else 'exclude'
    v = SchemaSerializer(schema_func(core_schema.any_schema()))
    with pytest.raises(TypeError, match=f'`{kind}` argument must be a set or dict.'):
        v.to_python(seq_f(0, 1, 2, 3), include=include, exclude=exclude)


def test_tuple_fallback():
    v = SchemaSerializer(core_schema.tuple_variable_schema(core_schema.any_schema()))
    msg = 'Expected `tuple[any, ...]` but got `str` - serialized value may not be as expected'
    with pytest.warns(UserWarning, match=re.escape(msg)):
        assert v.to_python('apple') == 'apple'

    with pytest.warns(UserWarning) as warning_info:
        assert v.to_json([1, 2, 3]) == b'[1,2,3]'
    assert [w.message.args[0] for w in warning_info.list] == [
        'Pydantic serializer warnings:\n  Expected `tuple[any, ...]` but got `list` - '
        'serialized value may not be as expected'
    ]

    msg = 'Expected `tuple[any, ...]` but got `bytes` - serialized value may not be as expected'
    with pytest.warns(UserWarning, match=re.escape(msg)):
        assert v.to_json(b'apple') == b'"apple"'

    assert v.to_python((1, 2, 3)) == (1, 2, 3)

    # even though we're in the fallback state, non JSON types should still be converted to JSON here
    msg = 'Expected `tuple[any, ...]` but got `list` - serialized value may not be as expected'
    with pytest.warns(UserWarning, match=re.escape(msg)):
        assert v.to_python([1, 2, 3], mode='json') == [1, 2, 3]


@pytest.mark.parametrize(
    'params',
    [
        dict(include=None, exclude=None, expected=['0', '1', '2', '3']),
        dict(include={0, 1}, exclude=None, expected=['0', '1']),
        dict(include={0: ..., 1: ...}, exclude=None, expected=['0', '1']),
        dict(include={0: True, 1: True}, exclude=None, expected=['0', '1']),
        dict(include={0: {1}, 1: {1}}, exclude=None, expected=['0', '1']),
        dict(include=None, exclude={0, 1}, expected=['2', '3']),
        dict(include=None, exclude={0: ..., 1: ...}, expected=['2', '3']),
        dict(include={0, 1}, exclude={1, 2}, expected=['0']),
        dict(include=None, exclude={3: {1}}, expected=['0', '1', '2', '3']),
        dict(include={0, 1}, exclude={3: {1}}, expected=['0', '1']),
        dict(include={0, 1}, exclude={1: {1}}, expected=['0', '1']),
        dict(include={0, 1}, exclude={1: ...}, expected=['0']),
        dict(include={1}, exclude={1}, expected=[]),
        dict(include={0}, exclude={1}, expected=['0']),
        dict(include={'__all__'}, exclude={1}, expected=['0', '2', '3']),
        dict(include=None, exclude={1}, expected=['0', '2', '3']),
        dict(include=None, exclude={'__all__'}, expected=[]),
    ],
)
def test_filter_args(params):
    s = SchemaSerializer(core_schema.list_schema())

    include, exclude, expected = params['include'], params['exclude'], params['expected']
    value = ['0', '1', '2', '3']
    assert s.to_python(value, include=include, exclude=exclude) == expected
    assert s.to_python(value, mode='json', include=include, exclude=exclude) == expected
    assert json.loads(s.to_json(value, include=include, exclude=exclude)) == expected


@pytest.mark.parametrize(
    'params',
    [
        dict(include=None, exclude=None, expected=[[0], [0, 1], [0, 1, 2], [0, 1, 2, 3]]),
        dict(include=None, exclude={1: {0}}, expected=[[0], [1], [0, 1, 2], [0, 1, 2, 3]]),
        dict(include=None, exclude={1: {0}, 2: ...}, expected=[[0], [1], [0, 1, 2, 3]]),
        dict(include=None, exclude={1: {0}, 2: True}, expected=[[0], [1], [0, 1, 2, 3]]),
        dict(include={1: {0}}, exclude=None, expected=[[0]]),
    ],
)
def test_filter_args_nested(params):
    s = SchemaSerializer(core_schema.list_schema(core_schema.list_schema()))

    include, exclude, expected = params['include'], params['exclude'], params['expected']
    value = [[0], [0, 1], [0, 1, 2], [0, 1, 2, 3]]
    assert s.to_python(value, include=include, exclude=exclude) == expected
    assert s.to_python(value, mode='json', include=include, exclude=exclude) == expected
    assert json.loads(s.to_json(value, include=include, exclude=exclude)) == expected


def test_filter_list_of_dicts():
    s = SchemaSerializer(core_schema.list_schema(core_schema.dict_schema()))
    v = [{'a': 1, 'b': 2}, {'a': 3, 'b': 4}]
    assert s.to_python(v) == v
    assert s.to_python(v, exclude={0: {'a'}}) == [{'b': 2}, {'a': 3, 'b': 4}]
    assert s.to_python(v, exclude={0: {'__all__'}}) == [{}, {'a': 3, 'b': 4}]
    assert s.to_python(v, exclude={'__all__': {'a'}}) == [{'b': 2}, {'b': 4}]

    assert s.to_json(v) == b'[{"a":1,"b":2},{"a":3,"b":4}]'
    assert s.to_json(v, exclude={0: {'a'}}) == b'[{"b":2},{"a":3,"b":4}]'
    assert s.to_json(v, exclude={0: {'__all__'}}) == b'[{},{"a":3,"b":4}]'
    assert s.to_json(v, exclude={'__all__': {'a'}}) == b'[{"b":2},{"b":4}]'

    assert s.to_python(v, include={0: {'a'}, 1: None}) == [{'a': 1}, {'a': 3, 'b': 4}]
    assert s.to_python(v, include={'__all__': {'a'}}) == [{'a': 1}, {'a': 3}]

    assert s.to_json(v, include={0: {'a'}, 1: None}) == b'[{"a":1},{"a":3,"b":4}]'
    assert s.to_json(v, include={'__all__': {'a'}}) == b'[{"a":1},{"a":3}]'


def test_positional_tuple():
    s = SchemaSerializer(
        {'type': 'tuple-positional', 'items_schema': [{'type': 'int'}, {'type': 'bytes'}, {'type': 'float'}]}
    )
    assert s.to_python((1, b'2', 3.0)) == (1, b'2', 3.0)
    assert s.to_python((1, b'2', 3.0, 123)) == (1, b'2', 3.0, 123)
    assert s.to_python((1, b'2')) == (1, b'2')

    assert s.to_python((1, b'2', 3.0), mode='json') == [1, '2', 3.0]
    assert s.to_python((1, b'2', 3.0, 123), mode='json') == [1, '2', 3.0, 123]
    assert s.to_python((1, b'2'), mode='json') == [1, '2']

    assert s.to_json((1, b'2', 3.0)) == b'[1,"2",3.0]'
    assert s.to_json((1, b'2', 3.0, 123)) == b'[1,"2",3.0,123]'
    assert s.to_json((1, b'2')) == b'[1,"2"]'


def test_function_positional_tuple():
    def f(prefix, value, _info):
        return f'{prefix}{value}'

    s = SchemaSerializer(
        {
            'type': 'tuple-positional',
            'items_schema': [
                core_schema.any_schema(
                    serialization=core_schema.plain_serializer_function_ser_schema(partial(f, 'a'), info_arg=True)
                ),
                core_schema.any_schema(
                    serialization=core_schema.plain_serializer_function_ser_schema(partial(f, 'b'), info_arg=True)
                ),
            ],
            'extras_schema': core_schema.any_schema(
                serialization=core_schema.plain_serializer_function_ser_schema(partial(f, 'extra'), info_arg=True)
            ),
        }
    )
    assert s.to_python((1,)) == ('a1',)
    assert s.to_python((1, 2)) == ('a1', 'b2')
    assert s.to_python((1, 2, 3)) == ('a1', 'b2', 'extra3')

    assert s.to_python((1,), mode='json') == ['a1']
    assert s.to_python((1, 2), mode='json') == ['a1', 'b2']
    assert s.to_python((1, 2, 3), mode='json') == ['a1', 'b2', 'extra3']

    assert s.to_json((1,)) == b'["a1"]'
    assert s.to_json((1, 2)) == b'["a1","b2"]'
    assert s.to_json((1, 2, 3)) == b'["a1","b2","extra3"]'


def test_list_dict_key():
    s = SchemaSerializer(core_schema.dict_schema(core_schema.list_schema(), core_schema.int_schema()))
    with pytest.warns(UserWarning, match=r'Expected `list\[any\]` but got `str`'):
        assert s.to_python({'xx': 1}) == {'xx': 1}


def test_tuple_var_dict_key():
    s = SchemaSerializer(core_schema.dict_schema(core_schema.tuple_variable_schema(), core_schema.int_schema()))
    with pytest.warns(UserWarning, match=r'Expected `tuple\[any, ...\]` but got `str`'):
        assert s.to_python({'xx': 1}) == {'xx': 1}

    assert s.to_python({(1, 2): 1}) == {(1, 2): 1}
    assert s.to_python({(1, 2): 1}, mode='json') == {'1,2': 1}
    assert s.to_json({(1, 2): 1}) == b'{"1,2":1}'


def test_tuple_pos_dict_key():
    s = SchemaSerializer(
        core_schema.dict_schema(
            core_schema.tuple_positional_schema(
                [core_schema.int_schema(), core_schema.str_schema()], extras_schema=core_schema.int_schema()
            ),
            core_schema.int_schema(),
        )
    )
    assert s.to_python({(1, 'a'): 1}) == {(1, 'a'): 1}
    assert s.to_python({(1, 'a', 2): 1}) == {(1, 'a', 2): 1}
    assert s.to_python({(1, 'a'): 1}, mode='json') == {'1,a': 1}
    assert s.to_python({(1, 'a', 2): 1}, mode='json') == {'1,a,2': 1}
    assert s.to_json({(1, 'a'): 1}) == b'{"1,a":1}'
    assert s.to_json({(1, 'a', 2): 1}) == b'{"1,a,2":1}'
