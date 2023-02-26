import dataclasses
import json
import platform
from typing import ClassVar

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


class BasicSubModel(BasicModel):
    pass


def test_model():
    s = SchemaSerializer(
        core_schema.model_schema(
            BasicModel,
            core_schema.typed_dict_schema(
                {
                    'foo': core_schema.typed_dict_field(core_schema.int_schema()),
                    'bar': core_schema.typed_dict_field(core_schema.bytes_schema()),
                }
            ),
        )
    )
    assert s.to_python(BasicModel(foo=1, bar=b'more')) == IsStrictDict(foo=1, bar=b'more')
    assert s.to_python(BasicSubModel(foo=1, bar=b'more')) == IsStrictDict(foo=1, bar=b'more')
    assert s.to_python(BasicModel(bar=b'more', foo=1)) == IsStrictDict(bar=b'more', foo=1)
    assert s.to_python(BasicModel(foo=1, c=3, bar=b'more')) == IsStrictDict(foo=1, bar=b'more')
    assert s.to_python(BasicModel(bar=b'more', foo=1, c=3), mode='json') == IsStrictDict(bar='more', foo=1)
    assert s.to_python(BasicSubModel(bar=b'more', foo=1, c=3), mode='json') == IsStrictDict(bar='more', foo=1)

    j = s.to_json(BasicModel(bar=b'more', foo=1, c=3))
    if on_pypy:
        assert json.loads(j) == {'bar': 'more', 'foo': 1}
    else:
        assert j == b'{"bar":"more","foo":1}'

    assert json.loads(s.to_json(BasicSubModel(bar=b'more', foo=1, c=3))) == {'bar': 'more', 'foo': 1}


@dataclasses.dataclass
class DataClass:
    class_var: ClassVar[int] = 1
    foo: int
    bar: str
    spam: bytes
    frog: dataclasses.InitVar[int]


def test_dataclass():
    schema = core_schema.call_schema(
        core_schema.arguments_schema(
            core_schema.arguments_parameter('foo', core_schema.int_schema()),
            core_schema.arguments_parameter('bar', core_schema.str_schema()),
            core_schema.arguments_parameter('spam', core_schema.bytes_schema(), mode='keyword_only'),
            core_schema.arguments_parameter('frog', core_schema.int_schema(), mode='keyword_only'),
        ),
        DataClass,
        serialization=core_schema.model_ser_schema(
            DataClass,
            core_schema.typed_dict_schema(
                {
                    'foo': core_schema.typed_dict_field(core_schema.int_schema()),
                    'bar': core_schema.typed_dict_field(core_schema.str_schema()),
                    'spam': core_schema.typed_dict_field(core_schema.bytes_schema()),
                }
            ),
        ),
    )
    # just check validation works as expected
    v = SchemaValidator(schema)
    dc = v.validate_python({'foo': 1, 'bar': 'bar-str', 'spam': 'bite', 'frog': 123})
    assert dc == DataClass(foo=1, bar='bar-str', spam=b'bite', frog=123)
    dc.class_var = 2
    assert dataclasses.is_dataclass(dc)

    s = SchemaSerializer(schema)

    assert dataclasses.asdict(dc) == IsStrictDict(foo=1, bar='bar-str', spam=b'bite')
    assert s.to_python(dc) == IsStrictDict(foo=1, bar='bar-str', spam=b'bite')

    assert s.to_python(dc, mode='json') == {'foo': 1, 'bar': 'bar-str', 'spam': 'bite'}
    assert json.loads(s.to_json(dc)) == {'foo': 1, 'bar': 'bar-str', 'spam': 'bite'}


def test_model_allow_extra():
    s = SchemaSerializer(
        core_schema.model_schema(
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
        dict(include={'a': ..., 'b': ...}, exclude=None, expected={'a': 0, 'b': 1}),
        dict(include={'a': {1}, 'b': {1}}, exclude=None, expected={'a': 0, 'b': 1}),
        dict(include=None, exclude={'a', 'b'}, expected={'c': 2, 'd': 3}),
        dict(include=None, exclude={'a': ..., 'b': ...}, expected={'c': 2, 'd': 3}),
        dict(include={'a', 'b'}, exclude={'b', 'c'}, expected={'a': 0}),
        dict(include=None, exclude={'d': {1}}, expected={'a': 0, 'b': 1, 'c': 2, 'd': 3}),
        dict(include={'a', 'b'}, exclude={'d': {1}}, expected={'a': 0, 'b': 1}),
        dict(include={'a', 'b'}, exclude={'b': {1}}, expected={'a': 0, 'b': 1}),
        dict(include={'a', 'b'}, exclude={'b': ...}, expected={'a': 0}),
        dict(include=None, exclude={'__all__'}, expected={}),
    ],
)
def test_include_exclude_args(params):
    s = SchemaSerializer(
        core_schema.model_schema(
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
        core_schema.model_schema(
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


def test_model_wrong_warn():
    s = SchemaSerializer(
        core_schema.model_schema(
            type('MyModel', (), {}),
            core_schema.typed_dict_schema(
                {
                    'foo': core_schema.typed_dict_field(core_schema.int_schema()),
                    'bar': core_schema.typed_dict_field(core_schema.bytes_schema()),
                }
            ),
        )
    )
    assert s.to_python(None) is None
    assert s.to_python(None, mode='json') is None
    assert s.to_json(None) == b'null'

    with pytest.warns(UserWarning, match='Expected `MyModel` but got `int` - serialized value may.+'):
        assert s.to_python(123) == 123
    with pytest.warns(UserWarning, match='Expected `MyModel` but got `int` - serialized value may.+'):
        assert s.to_python(123, mode='json') == 123
    with pytest.warns(UserWarning, match='Expected `MyModel` but got `int` - serialized value may.+'):
        assert s.to_json(123) == b'123'

    with pytest.warns(UserWarning, match='Expected `MyModel` but got `dict` - serialized value may.+'):
        assert s.to_python({'foo': 1, 'bar': b'more'}) == {'foo': 1, 'bar': b'more'}


def test_exclude_none():
    s = SchemaSerializer(
        core_schema.model_schema(
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
        core_schema.model_schema(
            FieldsSetModel,
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
    assert s.to_python(m, exclude={'bar': ...}, exclude_unset=True) == {'spam': 3}
    assert s.to_python(m, exclude={'bar': {}}, exclude_unset=True) == {'bar': 2, 'spam': 3}

    assert s.to_json(m, exclude=None, exclude_unset=True) == b'{"bar":2,"spam":3}'
    assert s.to_json(m, exclude={'bar'}, exclude_unset=True) == b'{"spam":3}'
    assert s.to_json(m, exclude={'bar': ...}, exclude_unset=True) == b'{"spam":3}'
    assert s.to_json(m, exclude={'bar': {}}, exclude_unset=True) == b'{"bar":2,"spam":3}'

    m2 = FieldsSetModel(foo=1, bar=2, spam=3, __fields_set__={'bar', 'spam', 'missing'})
    assert s.to_python(m2) == {'foo': 1, 'bar': 2, 'spam': 3}
    assert s.to_python(m2, exclude_unset=True) == {'bar': 2, 'spam': 3}


@pytest.mark.parametrize(
    'exclude,expected',
    [
        pytest.param(
            {'subs': {'__all__': {'subsubs': {'__all__': {'i'}}}}},
            {'subs': [{'k': 1, 'subsubs': [{'j': 1}, {'j': 2}]}, {'k': 2, 'subsubs': [{'j': 3}]}]},
            id='Normal nested __all__',
        ),
        pytest.param(
            {'subs': {'__all__': {'subsubs': {'__all__': {'i'}}}, 0: {'subsubs': {'__all__': {'j'}}}}},
            {'subs': [{'k': 1, 'subsubs': [{}, {}]}, {'k': 2, 'subsubs': [{'j': 3}]}]},
            id='Merge sub dicts 1',
        ),
        pytest.param(
            {'subs': {'__all__': {'subsubs': ...}, 0: {'subsubs': {'__all__': {'j'}}}}},
            {'subs': [{'k': 1, 'subsubs': [{'i': 1}, {'i': 2}]}, {'k': 2}]},
            # {'subs': [{'k': 1                                 }, {'k': 2}]}
            id='Merge sub sets 2',
        ),
        pytest.param(
            {'subs': {'__all__': {'subsubs': {'__all__': {'j'}}}, 0: {'subsubs': ...}}},
            {'subs': [{'k': 1}, {'k': 2, 'subsubs': [{'i': 3}]}]},
            id='Merge sub sets 3',
        ),
        pytest.param(
            {'subs': {'__all__': {'subsubs': {0}}, 0: {'subsubs': {1}}}},
            {'subs': [{'k': 1, 'subsubs': []}, {'k': 2, 'subsubs': []}]},
            id='Merge sub sets 1',
        ),
        pytest.param(
            {'subs': {'__all__': {'subsubs': {0: {'i'}}}, 0: {'subsubs': {1}}}},
            {'subs': [{'k': 1, 'subsubs': [{'j': 1}]}, {'k': 2, 'subsubs': [{'j': 3}]}]},
            id='Merge sub dict-set',
        ),
        pytest.param({'subs': {'__all__': {'subsubs'}, 0: {'k'}}}, {'subs': [{}, {'k': 2}]}, id='Different keys 1'),
        pytest.param(
            {'subs': {'__all__': {'subsubs': ...}, 0: {'k'}}}, {'subs': [{}, {'k': 2}]}, id='Different keys 2'
        ),
        pytest.param(
            {'subs': {'__all__': {'subsubs'}, 0: {'k': ...}}}, {'subs': [{}, {'k': 2}]}, id='Different keys 3'
        ),
        pytest.param(
            {'subs': {'__all__': {'subsubs': {'__all__': {'i'}, 0: {'j'}}}}},
            {'subs': [{'k': 1, 'subsubs': [{}, {'j': 2}]}, {'k': 2, 'subsubs': [{}]}]},
            id='Nested different keys 1',
        ),
        pytest.param(
            {'subs': {'__all__': {'subsubs': {'__all__': {'i': ...}, 0: {'j'}}}}},
            {'subs': [{'k': 1, 'subsubs': [{}, {'j': 2}]}, {'k': 2, 'subsubs': [{}]}]},
            id='Nested different keys 2',
        ),
        pytest.param(
            {'subs': {'__all__': {'subsubs': {'__all__': {'i'}, 0: {'j': ...}}}}},
            {'subs': [{'k': 1, 'subsubs': [{}, {'j': 2}]}, {'k': 2, 'subsubs': [{}]}]},
            id='Nested different keys 3',
        ),
        pytest.param(
            {'subs': {'__all__': {'subsubs'}, 0: {'subsubs': {'__all__': {'j'}}}}},
            {'subs': [{'k': 1, 'subsubs': [{'i': 1}, {'i': 2}]}, {'k': 2}]},
            id='Ignore __all__ for index with defined exclude 1',
        ),
        pytest.param(
            {'subs': {'__all__': {'subsubs': {'__all__': {'j'}}}, 0: ...}},
            {'subs': [{'k': 2, 'subsubs': [{'i': 3}]}]},
            id='Ignore __all__ for index with defined exclude 2',
        ),
        pytest.param(
            {'subs': {'__all__': ..., 0: {'subsubs'}}},
            {'subs': [{'k': 1}]},
            id='Ignore __all__ for index with defined exclude 3',
        ),
    ],
)
def test_advanced_exclude_nested_lists(exclude, expected):
    """
    Taken from pydantic and modified to generate the schema directly.
    """
    # class SubSubModel(BaseModel):
    #     i: int
    #     j: int

    sub_sub_model_schema = core_schema.model_schema(
        type('SubSubModel', (), {}),
        core_schema.typed_dict_schema(
            dict(
                i=core_schema.typed_dict_field(core_schema.int_schema(), required=True),
                j=core_schema.typed_dict_field(core_schema.int_schema(), required=True),
            )
        ),
    )

    # class SubModel(BaseModel):
    #     k: int
    #     subsubs: List[SubSubModel]

    sub_model_schema = core_schema.model_schema(
        type('SubModel', (), {}),
        core_schema.typed_dict_schema(
            dict(
                k=core_schema.typed_dict_field(core_schema.int_schema(), required=True),
                subsubs=core_schema.typed_dict_field(core_schema.list_schema(sub_sub_model_schema), required=True),
            )
        ),
    )

    # class Model(BaseModel):
    #     subs: List[SubModel]

    model_schema = core_schema.model_schema(
        BasicModel,
        core_schema.typed_dict_schema(
            dict(subs=core_schema.typed_dict_field(core_schema.list_schema(sub_model_schema), required=True))
        ),
    )
    v = SchemaValidator(model_schema)

    data = v.validate_python(
        dict(subs=[dict(k=1, subsubs=[dict(i=1, j=1), dict(i=2, j=2)]), dict(k=2, subsubs=[dict(i=3, j=3)])])
    )

    s = SchemaSerializer(model_schema)

    assert s.to_python(data, exclude=exclude) == expected
