import dataclasses
import json
import platform

import pytest

from pydantic_core import SchemaSerializer, SchemaValidator, core_schema

on_pypy = platform.python_implementation() == 'PyPy'
# pypy doesn't seem to maintain order of `__dict__`
if on_pypy:
    IsStrictDict = dict
else:
    from dirty_equals import IsStrictDict


class BasicModel:
    def __init__(self, **kwargs):
        for key, value in kwargs.items():
            setattr(self, key, value)


def test_new_class():
    s = SchemaSerializer(
        core_schema.new_class_schema(
            type('Anything', (), {}),
            core_schema.typed_dict_schema(
                {
                    'foo': core_schema.typed_dict_field(core_schema.int_schema()),
                    'bar': core_schema.typed_dict_field(core_schema.bytes_schema()),
                }
            ),
        )
    )
    assert s.to_python(BasicModel(foo=1, bar=b'more')) == IsStrictDict(foo=1, bar=b'more')
    assert s.to_python(BasicModel(bar=b'more', foo=1)) == IsStrictDict(bar=b'more', foo=1)
    assert s.to_python(BasicModel(foo=1, c=3, bar=b'more')) == IsStrictDict(foo=1, bar=b'more')
    assert s.to_python(BasicModel(bar=b'more', foo=1, c=3), mode='json') == IsStrictDict(bar='more', foo=1)

    j = s.to_json(BasicModel(bar=b'more', foo=1, c=3))
    if on_pypy:
        assert json.loads(j) == {'bar': 'more', 'foo': 1}
    else:
        assert j == b'{"bar":"more","foo":1}'


@dataclasses.dataclass
class DataClass:
    foo: int
    bar: str
    spam: bytes


def test_dataclass():
    schema = core_schema.call_schema(
        core_schema.arguments_schema(
            core_schema.arguments_parameter('foo', core_schema.int_schema()),
            core_schema.arguments_parameter('bar', core_schema.string_schema()),
            core_schema.arguments_parameter('spam', core_schema.bytes_schema(), mode='keyword_only'),
        ),
        DataClass,
        serialization={
            'type': 'new-class',
            'schema': core_schema.typed_dict_schema(
                {
                    'foo': core_schema.typed_dict_field(core_schema.int_schema()),
                    'bar': core_schema.typed_dict_field(core_schema.string_schema()),
                    'spam': core_schema.typed_dict_field(core_schema.bytes_schema()),
                }
            ),
        },
    )
    # just check validation works as expected
    v = SchemaValidator(schema)
    dc = v.validate_python({'foo': 1, 'bar': 'bar-str', 'spam': 'bite'})
    assert dc == DataClass(foo=1, bar='bar-str', spam=b'bite')
    assert dataclasses.is_dataclass(dc)

    s = SchemaSerializer(schema)

    assert s.to_python(dc) == IsStrictDict(foo=1, bar='bar-str', spam=b'bite')

    assert s.to_python(dc, mode='json') == {'foo': 1, 'bar': 'bar-str', 'spam': 'bite'}
    assert json.loads(s.to_json(dc)) == {'foo': 1, 'bar': 'bar-str', 'spam': 'bite'}


def test_new_class_allow_extra():
    s = SchemaSerializer(
        core_schema.new_class_schema(
            BasicModel,
            core_schema.typed_dict_schema(
                {
                    'foo': core_schema.typed_dict_field(core_schema.int_schema()),
                    'bar': core_schema.typed_dict_field(core_schema.bytes_schema()),
                },
                extra_behavior='allow',
            ),
        )
    )
    assert s.to_python(BasicModel(foo=1, bar=b'more')) == IsStrictDict(foo=1, bar=b'more')
    assert s.to_python(BasicModel(bar=b'more', foo=1)) == IsStrictDict(bar=b'more', foo=1)
    assert s.to_python(BasicModel(foo=1, c=3, bar=b'more')) == IsStrictDict(foo=1, c=3, bar=b'more')
    assert s.to_python(BasicModel(bar=b'more', c=3, foo=1), mode='json') == IsStrictDict(bar='more', c=3, foo=1)

    j = s.to_json(BasicModel(bar=b'more', foo=1, c=3))
    if on_pypy:
        assert json.loads(j) == {'bar': 'more', 'foo': 1, 'c': 3}
    else:
        assert j == b'{"bar":"more","foo":1,"c":3}'


@pytest.mark.parametrize(
    'params',
    [
        dict(include=None, exclude=None, expected={'a': 0, 'b': 1, 'c': 2, 'd': 3}),
        dict(include={'a', 'b'}, exclude=None, expected={'a': 0, 'b': 1}),
        dict(include={'a': None, 'b': None}, exclude=None, expected={'a': 0, 'b': 1}),
        dict(include={'a': {1}, 'b': {1}}, exclude=None, expected={'a': 0, 'b': 1}),
        dict(include=None, exclude={'a', 'b'}, expected={'c': 2, 'd': 3}),
        dict(include=None, exclude={'a': None, 'b': None}, expected={'c': 2, 'd': 3}),
        dict(include={'a', 'b'}, exclude={'b', 'c'}, expected={'a': 0}),
        dict(include=None, exclude={'d': {1}}, expected={'a': 0, 'b': 1, 'c': 2, 'd': 3}),
        dict(include={'a', 'b'}, exclude={'d': {1}}, expected={'a': 0, 'b': 1}),
        dict(include={'a', 'b'}, exclude={'b': {1}}, expected={'a': 0, 'b': 1}),
        dict(include={'a', 'b'}, exclude={'b': None}, expected={'a': 0}),
    ],
)
def test_include_exclude_args(params):
    s = SchemaSerializer(
        core_schema.new_class_schema(
            BasicModel,
            core_schema.typed_dict_schema(
                {
                    'a': core_schema.typed_dict_field(core_schema.int_schema()),
                    'b': core_schema.typed_dict_field(core_schema.int_schema()),
                    'c': core_schema.typed_dict_field(core_schema.int_schema()),
                    'd': core_schema.typed_dict_field(core_schema.int_schema()),
                }
            ),
        )
    )

    # user IsStrictDict to check dict order
    include, exclude, expected = params['include'], params['exclude'], IsStrictDict(params['expected'])
    value = BasicModel(a=0, b=1, c=2, d=3)
    assert s.to_python(value, include=include, exclude=exclude) == expected
    assert s.to_python(value, mode='json', include=include, exclude=exclude) == expected
    assert json.loads(s.to_json(value, include=include, exclude=exclude)) == expected


def test_alias():
    s = SchemaSerializer(
        core_schema.new_class_schema(
            BasicModel,
            core_schema.typed_dict_schema(
                {
                    'cat': core_schema.typed_dict_field(core_schema.int_schema(), serialization_alias='Meow'),
                    'dog': core_schema.typed_dict_field(core_schema.int_schema(), serialization_alias='Woof'),
                    'bird': core_schema.typed_dict_field(core_schema.int_schema()),
                }
            ),
        )
    )
    value = BasicModel(cat=0, dog=1, bird=2)
    assert s.to_python(value) == IsStrictDict(Meow=0, Woof=1, bird=2)


def test_new_class_wrong():
    s = SchemaSerializer(
        core_schema.new_class_schema(
            type('Anything', (), {}),
            core_schema.typed_dict_schema(
                {
                    'foo': core_schema.typed_dict_field(core_schema.int_schema()),
                    'bar': core_schema.typed_dict_field(core_schema.bytes_schema()),
                }
            ),
        )
    )
    with pytest.raises(AttributeError, match="'int' object has no attribute '__dict__'"):
        s.to_python(123)
    with pytest.raises(AttributeError, match="'dict' object has no attribute '__dict__'"):
        s.to_python({'foo': 1, 'bar': b'more'})


def test_exclude_none():
    s = SchemaSerializer(
        core_schema.new_class_schema(
            BasicModel,
            core_schema.typed_dict_schema(
                {
                    'foo': core_schema.typed_dict_field(core_schema.nullable_schema(core_schema.int_schema())),
                    'bar': core_schema.typed_dict_field(core_schema.bytes_schema()),
                },
                extra_behavior='ignore',  # this is the default
            ),
        )
    )
    assert s.to_python(BasicModel(foo=1, bar=b'more')) == {'foo': 1, 'bar': b'more'}
    assert s.to_python(BasicModel(foo=None, bar=b'more')) == {'foo': None, 'bar': b'more'}
    assert s.to_python(BasicModel(foo=None, bar=b'more'), exclude_none=True) == {'bar': b'more'}

    assert s.to_python(BasicModel(foo=None, bar=b'more'), mode='json') == {'foo': None, 'bar': 'more'}
    assert s.to_python(BasicModel(foo=None, bar=b'more'), mode='json', exclude_none=True) == {'bar': 'more'}

    assert s.to_json(BasicModel(foo=1, bar=b'more')) == b'{"foo":1,"bar":"more"}'
    assert s.to_json(BasicModel(foo=None, bar=b'more')) == b'{"foo":null,"bar":"more"}'
    assert s.to_json(BasicModel(foo=None, bar=b'more'), exclude_none=True) == b'{"bar":"more"}'


class FieldsSetModel:
    __slots__ = '__dict__', '__fields_set__'

    def __init__(self, **kwargs):
        for key, value in kwargs.items():
            setattr(self, key, value)


def test_exclude_unset():
    s = SchemaSerializer(
        core_schema.new_class_schema(
            BasicModel,
            core_schema.typed_dict_schema(
                {
                    'foo': core_schema.typed_dict_field(core_schema.int_schema()),
                    'bar': core_schema.typed_dict_field(core_schema.int_schema()),
                    'spam': core_schema.typed_dict_field(core_schema.int_schema()),
                },
                extra_behavior='ignore',  # this is the default
            ),
        )
    )
    m = FieldsSetModel(foo=1, bar=2, spam=3, __fields_set__={'bar', 'spam'})
    assert s.to_python(m) == {'foo': 1, 'bar': 2, 'spam': 3}
    assert s.to_python(m, exclude_unset=True) == {'bar': 2, 'spam': 3}
    assert s.to_python(m, exclude=None, exclude_unset=True) == {'bar': 2, 'spam': 3}
    assert s.to_python(m, exclude={'bar'}, exclude_unset=True) == {'spam': 3}
    assert s.to_python(m, exclude={'bar': None}, exclude_unset=True) == {'spam': 3}
    assert s.to_python(m, exclude={'bar': {}}, exclude_unset=True) == {'bar': 2, 'spam': 3}

    assert s.to_json(m, exclude=None, exclude_unset=True) == b'{"bar":2,"spam":3}'
    assert s.to_json(m, exclude={'bar'}, exclude_unset=True) == b'{"spam":3}'
    assert s.to_json(m, exclude={'bar': None}, exclude_unset=True) == b'{"spam":3}'
    assert s.to_json(m, exclude={'bar': {}}, exclude_unset=True) == b'{"bar":2,"spam":3}'

    m2 = FieldsSetModel(foo=1, bar=2, spam=3, __fields_set__={'bar', 'spam', 'missing'})
    assert s.to_python(m2) == {'foo': 1, 'bar': 2, 'spam': 3}
    assert s.to_python(m2, exclude_unset=True) == {'bar': 2, 'spam': 3}
