import json

import pytest
from dirty_equals import IsStrictDict

from pydantic_core import SchemaSerializer, core_schema


def test_typed_dict():
    v = SchemaSerializer(
        core_schema.typed_dict_schema(
            {
                'foo': core_schema.typed_dict_field(core_schema.int_schema()),
                'bar': core_schema.typed_dict_field(core_schema.bytes_schema()),
            },
            extra_behavior='ignore',  # this is the default
        )
    )
    assert v.to_python({'foo': 1, 'bar': b'more'}) == IsStrictDict(foo=1, bar=b'more')
    assert v.to_python({'bar': b'more', 'foo': 1}) == IsStrictDict(bar=b'more', foo=1)
    assert v.to_python({'foo': 1, 'bar': b'more', 'c': 3}) == IsStrictDict(foo=1, bar=b'more')
    assert v.to_python({'bar': b'more', 'foo': 1, 'c': 3}, mode='json') == IsStrictDict(bar='more', foo=1)

    assert v.to_json({'bar': b'more', 'foo': 1, 'c': 3}) == b'{"bar":"more","foo":1}'


def test_typed_dict_allow_extra():
    v = SchemaSerializer(
        core_schema.typed_dict_schema(
            {
                'foo': core_schema.typed_dict_field(core_schema.int_schema()),
                'bar': core_schema.typed_dict_field(core_schema.bytes_schema()),
            },
            extra_behavior='allow',
        )
    )
    # extra fields go last but retain their order
    assert v.to_python({'bar': b'more', 'b': 3, 'foo': 1, 'a': 4}) == IsStrictDict(bar=b'more', b=3, foo=1, a=4)
    assert v.to_python({'bar': b'more', 'c': 3, 'foo': 1}, mode='json') == IsStrictDict(bar='more', c=3, foo=1)

    assert v.to_json({'bar': b'more', 'c': 3, 'foo': 1, 'cc': 4}) == b'{"bar":"more","c":3,"foo":1,"cc":4}'


@pytest.mark.parametrize(
    'params',
    [
        dict(include=None, exclude=None, expected={'0': 0, '1': 1, '2': 2, '3': 3}),
        dict(include={'0', '1'}, exclude=None, expected={'0': 0, '1': 1}),
        dict(include={'0': ..., '1': ...}, exclude=None, expected={'0': 0, '1': 1}),
        dict(include={'0': {1}, '1': {1}}, exclude=None, expected={'0': 0, '1': 1}),
        dict(include=None, exclude={'0', '1'}, expected={'2': 2, '3': 3}),
        dict(include=None, exclude={'0': ..., '1': ...}, expected={'2': 2, '3': 3}),
        dict(include={'0', '1'}, exclude={'1', '2'}, expected={'0': 0}),
        dict(include=None, exclude={'3': {1}}, expected={'0': 0, '1': 1, '2': 2, '3': 3}),
        dict(include={'0', '1'}, exclude={'3': {1}}, expected={'0': 0, '1': 1}),
        dict(include={'0', '1'}, exclude={'1': {1}}, expected={'0': 0, '1': 1}),
        dict(include={'0', '1'}, exclude={'1': ...}, expected={'0': 0}),
    ],
)
def test_include_exclude_args(params):
    s = SchemaSerializer(
        core_schema.typed_dict_schema(
            {
                '0': core_schema.typed_dict_field(core_schema.int_schema()),
                '1': core_schema.typed_dict_field(core_schema.int_schema()),
                '2': core_schema.typed_dict_field(core_schema.int_schema()),
                '3': core_schema.typed_dict_field(core_schema.int_schema()),
            }
        )
    )

    # user IsStrictDict to check dict order
    include, exclude, expected = params['include'], params['exclude'], IsStrictDict(params['expected'])
    value = {'0': 0, '1': 1, '2': 2, '3': 3}
    assert s.to_python(value, include=include, exclude=exclude) == expected
    assert s.to_python(value, mode='json', include=include, exclude=exclude) == expected
    assert json.loads(s.to_json(value, include=include, exclude=exclude)) == expected


def test_include_exclude_schema():
    s = SchemaSerializer(
        core_schema.typed_dict_schema(
            {
                '0': core_schema.typed_dict_field(core_schema.int_schema(), serialization_exclude=True),
                '1': core_schema.typed_dict_field(core_schema.int_schema()),
                '2': core_schema.typed_dict_field(core_schema.int_schema(), serialization_exclude=True),
                '3': core_schema.typed_dict_field(core_schema.int_schema(), serialization_exclude=False),
            }
        )
    )
    value = {'0': 0, '1': 1, '2': 2, '3': 3}
    assert s.to_python(value) == {'1': 1, '3': 3}
    assert s.to_python(value, mode='json') == {'1': 1, '3': 3}
    assert json.loads(s.to_json(value)) == {'1': 1, '3': 3}


def test_alias():
    s = SchemaSerializer(
        core_schema.typed_dict_schema(
            {
                'cat': core_schema.typed_dict_field(core_schema.int_schema(), serialization_alias='Meow'),
                'dog': core_schema.typed_dict_field(core_schema.int_schema(), serialization_alias='Woof'),
                'bird': core_schema.typed_dict_field(core_schema.int_schema()),
            }
        )
    )
    value = {'cat': 0, 'dog': 1, 'bird': 2}
    assert s.to_python(value) == IsStrictDict(Meow=0, Woof=1, bird=2)
    assert s.to_python(value, exclude={'dog'}) == IsStrictDict(Meow=0, bird=2)
    assert s.to_python(value, by_alias=False) == IsStrictDict(cat=0, dog=1, bird=2)

    assert s.to_python(value, mode='json') == IsStrictDict(Meow=0, Woof=1, bird=2)
    assert s.to_python(value, mode='json', include={'cat'}) == IsStrictDict(Meow=0)
    assert s.to_python(value, mode='json', by_alias=False) == IsStrictDict(cat=0, dog=1, bird=2)

    assert json.loads(s.to_json(value)) == IsStrictDict(Meow=0, Woof=1, bird=2)
    assert json.loads(s.to_json(value, include={'cat', 'bird'})) == IsStrictDict(Meow=0, bird=2)
    assert json.loads(s.to_json(value, by_alias=False)) == IsStrictDict(cat=0, dog=1, bird=2)


def test_exclude_none():
    v = SchemaSerializer(
        core_schema.typed_dict_schema(
            {
                'foo': core_schema.typed_dict_field(core_schema.nullable_schema(core_schema.int_schema())),
                'bar': core_schema.typed_dict_field(core_schema.bytes_schema()),
            },
            extra_behavior='allow',
        )
    )
    assert v.to_python({'foo': 1, 'bar': b'more', 'c': 3}) == {'foo': 1, 'bar': b'more', 'c': 3}
    assert v.to_python({'foo': None, 'bar': b'more', 'c': None}) == {'foo': None, 'bar': b'more', 'c': None}
    assert v.to_python({'foo': None, 'bar': b'more', 'c': None}, exclude_none=True) == {'bar': b'more'}

    assert v.to_python({'foo': None, 'bar': b'more', 'c': None}, mode='json') == {'foo': None, 'bar': 'more', 'c': None}
    assert v.to_python({'foo': None, 'bar': b'more', 'c': None}, mode='json', exclude_none=True) == {'bar': 'more'}

    assert v.to_json({'foo': 1, 'bar': b'more', 'c': None}) == b'{"foo":1,"bar":"more","c":null}'
    assert v.to_json({'foo': None, 'bar': b'more'}) == b'{"foo":null,"bar":"more"}'
    assert v.to_json({'foo': None, 'bar': b'more', 'c': None}, exclude_none=True) == b'{"bar":"more"}'


def test_exclude_default():
    v = SchemaSerializer(
        core_schema.typed_dict_schema(
            {
                'foo': core_schema.typed_dict_field(core_schema.nullable_schema(core_schema.int_schema())),
                'bar': core_schema.typed_dict_field(
                    core_schema.with_default_schema(core_schema.bytes_schema(), default=b'[default]')
                ),
            }
        )
    )
    assert v.to_python({'foo': 1, 'bar': b'x'}) == {'foo': 1, 'bar': b'x'}
    assert v.to_python({'foo': 1, 'bar': b'[default]'}) == {'foo': 1, 'bar': b'[default]'}
    assert v.to_python({'foo': 1, 'bar': b'[default]'}, exclude_defaults=True) == {'foo': 1}
    assert v.to_python({'foo': 1, 'bar': b'[default]'}, mode='json') == {'foo': 1, 'bar': '[default]'}
    assert v.to_python({'foo': 1, 'bar': b'[default]'}, exclude_defaults=True, mode='json') == {'foo': 1}

    assert v.to_json({'foo': 1, 'bar': b'[default]'}) == b'{"foo":1,"bar":"[default]"}'
    assert v.to_json({'foo': 1, 'bar': b'[default]'}, exclude_defaults=True) == b'{"foo":1}'
