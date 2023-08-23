import dataclasses
import json
import platform
from random import randint
from typing import Any, ClassVar, Dict

try:
    from functools import cached_property
except ImportError:
    cached_property = None

import pytest
from dirty_equals import IsJson

from pydantic_core import PydanticSerializationError, SchemaSerializer, SchemaValidator, core_schema

from ..conftest import plain_repr

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
            core_schema.model_fields_schema(
                {
                    'foo': core_schema.model_field(core_schema.int_schema()),
                    'bar': core_schema.model_field(core_schema.bytes_schema()),
                }
            ),
        )
    )
    assert 'mode:SimpleDict' in plain_repr(s)
    assert 'has_extra:false' in plain_repr(s)
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
            [
                core_schema.arguments_parameter('foo', core_schema.int_schema()),
                core_schema.arguments_parameter('bar', core_schema.str_schema()),
                core_schema.arguments_parameter('spam', core_schema.bytes_schema(), mode='keyword_only'),
                core_schema.arguments_parameter('frog', core_schema.int_schema(), mode='keyword_only'),
            ]
        ),
        DataClass,
        serialization=core_schema.model_ser_schema(
            DataClass,
            core_schema.model_fields_schema(
                {
                    'foo': core_schema.model_field(core_schema.int_schema()),
                    'bar': core_schema.model_field(core_schema.str_schema()),
                    'spam': core_schema.model_field(core_schema.bytes_schema()),
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
            core_schema.model_fields_schema(
                {
                    'foo': core_schema.model_field(core_schema.int_schema()),
                    'bar': core_schema.model_field(core_schema.bytes_schema()),
                },
                extra_behavior='allow',
            ),
            extra_behavior='allow',
        )
    )
    assert s.to_python(BasicModel(foo=1, bar=b'more', __pydantic_extra__={})) == IsStrictDict(foo=1, bar=b'more')
    assert s.to_python(BasicModel(bar=b'more', foo=1, __pydantic_extra__={})) == IsStrictDict(bar=b'more', foo=1)
    assert s.to_python(BasicModel(foo=1, __pydantic_extra__=dict(c=3), bar=b'more')) == IsStrictDict(
        foo=1, bar=b'more', c=3
    )
    assert s.to_python(BasicModel(bar=b'more', __pydantic_extra__=dict(c=3, foo=1)), mode='json') == IsStrictDict(
        bar='more', c=3, foo=1
    )

    j = s.to_json(BasicModel(bar=b'more', foo=1, __pydantic_extra__=dict(c=3)))
    if on_pypy:
        assert j == IsJson({'bar': 'more', 'foo': 1, 'c': 3})
    else:
        assert j == b'{"bar":"more","foo":1,"c":3}'


def test_model_recursive_in_extra():
    # See https://github.com/pydantic/pydantic/issues/6571

    class Model(BasicModel):
        __slots__ = '__pydantic_extra__'

    s = SchemaSerializer(
        core_schema.model_schema(
            Model, core_schema.model_fields_schema({}, extra_behavior='allow'), extra_behavior='allow'
        )
    )
    Model.__pydantic_serializer__ = s

    assert s.to_json(Model(__pydantic_extra__=dict(other=Model(__pydantic_extra__={})))) == b'{"other":{}}'


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
            core_schema.model_fields_schema(
                {
                    'a': core_schema.model_field(core_schema.int_schema()),
                    'b': core_schema.model_field(core_schema.int_schema()),
                    'c': core_schema.model_field(core_schema.int_schema()),
                    'd': core_schema.model_field(core_schema.int_schema()),
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
            core_schema.model_fields_schema(
                {
                    'cat': core_schema.model_field(core_schema.int_schema(), serialization_alias='Meow'),
                    'dog': core_schema.model_field(core_schema.int_schema(), serialization_alias='Woof'),
                    'bird': core_schema.model_field(core_schema.int_schema()),
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
            core_schema.model_fields_schema(
                {
                    'foo': core_schema.model_field(core_schema.int_schema()),
                    'bar': core_schema.model_field(core_schema.bytes_schema()),
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
            core_schema.model_fields_schema(
                {
                    'foo': core_schema.model_field(core_schema.nullable_schema(core_schema.int_schema())),
                    'bar': core_schema.model_field(core_schema.bytes_schema()),
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
    __slots__ = '__dict__', '__pydantic_fields_set__', '__pydantic_extra__', '__pydantic_private__'

    def __init__(self, **kwargs):
        for key, value in kwargs.items():
            setattr(self, key, value)


def test_exclude_unset():
    s = SchemaSerializer(
        core_schema.model_schema(
            FieldsSetModel,
            core_schema.model_fields_schema(
                {
                    'foo': core_schema.model_field(core_schema.int_schema()),
                    'bar': core_schema.model_field(core_schema.int_schema()),
                    'spam': core_schema.model_field(core_schema.int_schema()),
                },
                extra_behavior='ignore',  # this is the default
            ),
        )
    )
    m = FieldsSetModel(foo=1, bar=2, spam=3, __pydantic_fields_set__={'bar', 'spam'})
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

    m2 = FieldsSetModel(foo=1, bar=2, spam=3, __pydantic_fields_set__={'bar', 'spam', 'missing'})
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
        core_schema.model_fields_schema(
            dict(
                i=core_schema.model_field(core_schema.int_schema()), j=core_schema.model_field(core_schema.int_schema())
            )
        ),
    )

    # class SubModel(BaseModel):
    #     k: int
    #     subsubs: List[SubSubModel]

    sub_model_schema = core_schema.model_schema(
        type('SubModel', (), {}),
        core_schema.model_fields_schema(
            dict(
                k=core_schema.model_field(core_schema.int_schema()),
                subsubs=core_schema.model_field(core_schema.list_schema(sub_sub_model_schema)),
            )
        ),
    )

    # class Model(BaseModel):
    #     subs: List[SubModel]

    model_schema = core_schema.model_schema(
        BasicModel,
        core_schema.model_fields_schema(dict(subs=core_schema.model_field(core_schema.list_schema(sub_model_schema)))),
    )
    v = SchemaValidator(model_schema)

    data = v.validate_python(
        dict(subs=[dict(k=1, subsubs=[dict(i=1, j=1), dict(i=2, j=2)]), dict(k=2, subsubs=[dict(i=3, j=3)])])
    )

    s = SchemaSerializer(model_schema)

    assert s.to_python(data, exclude=exclude) == expected


def test_function_plain_field_serializer_to_python():
    @dataclasses.dataclass
    class Model:
        x: int

        def ser_x(self, v: Any, _) -> str:
            assert self.x == 1_000
            return f'{v:_}'

    s = SchemaSerializer(
        core_schema.model_schema(
            Model,
            core_schema.model_fields_schema(
                {
                    'x': core_schema.model_field(
                        core_schema.int_schema(
                            serialization=core_schema.plain_serializer_function_ser_schema(
                                Model.ser_x, is_field_serializer=True, info_arg=True
                            )
                        )
                    )
                }
            ),
        )
    )
    assert s.to_python(Model(x=1000)) == {'x': '1_000'}


def test_function_wrap_field_serializer_to_python():
    @dataclasses.dataclass
    class Model:
        x: int

        def ser_x(self, v: Any, serializer: core_schema.SerializerFunctionWrapHandler, _) -> str:
            x = serializer(v)
            assert self.x == 1_000
            return f'{x:_}'

    s = SchemaSerializer(
        core_schema.model_schema(
            Model,
            core_schema.model_fields_schema(
                {
                    'x': core_schema.model_field(
                        core_schema.int_schema(
                            serialization=core_schema.wrap_serializer_function_ser_schema(
                                Model.ser_x, is_field_serializer=True, info_arg=True, schema=core_schema.any_schema()
                            )
                        )
                    )
                }
            ),
        )
    )
    assert s.to_python(Model(x=1000)) == {'x': '1_000'}


def test_function_plain_field_serializer_to_json():
    @dataclasses.dataclass
    class Model:
        x: int

        def ser_x(self, v: Any, _) -> str:
            assert self.x == 1_000
            return f'{v:_}'

    s = SchemaSerializer(
        core_schema.model_schema(
            Model,
            core_schema.model_fields_schema(
                {
                    'x': core_schema.model_field(
                        core_schema.int_schema(
                            serialization=core_schema.plain_serializer_function_ser_schema(
                                Model.ser_x, is_field_serializer=True, info_arg=True
                            )
                        )
                    )
                }
            ),
        )
    )
    assert json.loads(s.to_json(Model(x=1000))) == {'x': '1_000'}


def test_function_wrap_field_serializer_to_json():
    @dataclasses.dataclass
    class Model:
        x: int

        def ser_x(self, v: Any, serializer: core_schema.SerializerFunctionWrapHandler, _) -> str:
            assert self.x == 1_000
            x = serializer(v)
            return f'{x:_}'

    s = SchemaSerializer(
        core_schema.model_schema(
            Model,
            core_schema.model_fields_schema(
                {
                    'x': core_schema.model_field(
                        core_schema.int_schema(
                            serialization=core_schema.wrap_serializer_function_ser_schema(
                                Model.ser_x, is_field_serializer=True, info_arg=True, schema=core_schema.any_schema()
                            )
                        )
                    )
                }
            ),
        )
    )
    assert json.loads(s.to_json(Model(x=1000))) == {'x': '1_000'}


def test_property():
    @dataclasses.dataclass
    class Model:
        def __init__(self, **kwargs):
            for key, value in kwargs.items():
                setattr(self, key, value)

        @property
        def area(self) -> bytes:
            a = self.width * self.height
            return b'%d' % a

    s = SchemaSerializer(
        core_schema.model_schema(
            Model,
            core_schema.model_fields_schema(
                {
                    'width': core_schema.model_field(core_schema.int_schema()),
                    'height': core_schema.model_field(core_schema.int_schema()),
                },
                computed_fields=[core_schema.computed_field('area', core_schema.bytes_schema())],
            ),
        )
    )
    assert s.to_python(Model(width=3, height=4)) == {'width': 3, 'height': 4, 'area': b'12'}
    assert s.to_python(Model(width=3, height=4), mode='json') == {'width': 3, 'height': 4, 'area': '12'}
    assert s.to_json(Model(width=3, height=4)) == b'{"width":3,"height":4,"area":"12"}'


def test_property_alias():
    @dataclasses.dataclass
    class Model:
        width: int
        height: int

        @property
        def area(self) -> int:
            return self.width * self.height

        @property
        def volume(self) -> int:
            return self.area * self.height

    s = SchemaSerializer(
        core_schema.model_schema(
            Model,
            core_schema.model_fields_schema(
                {
                    'width': core_schema.model_field(core_schema.int_schema()),
                    'height': core_schema.model_field(core_schema.int_schema()),
                },
                computed_fields=[
                    core_schema.computed_field('area', core_schema.int_schema(), alias='Area'),
                    core_schema.computed_field('volume', core_schema.int_schema()),
                ],
            ),
        )
    )
    assert s.to_python(Model(3, 4)) == {'width': 3, 'height': 4, 'Area': 12, 'volume': 48}
    assert s.to_python(Model(3, 4), mode='json') == {'width': 3, 'height': 4, 'Area': 12, 'volume': 48}
    assert s.to_json(Model(3, 4)) == b'{"width":3,"height":4,"Area":12,"volume":48}'


def test_computed_field_to_python_exclude_none():
    @dataclasses.dataclass
    class Model:
        width: int
        height: int

        @property
        def area(self) -> int:
            return self.width * self.height

        @property
        def volume(self) -> None:
            return None

    s = SchemaSerializer(
        core_schema.model_schema(
            Model,
            core_schema.model_fields_schema(
                {
                    'width': core_schema.model_field(core_schema.int_schema()),
                    'height': core_schema.model_field(core_schema.int_schema()),
                },
                computed_fields=[
                    core_schema.computed_field('area', core_schema.int_schema(), alias='Area'),
                    core_schema.computed_field('volume', core_schema.int_schema()),
                ],
            ),
        )
    )
    assert s.to_python(Model(3, 4), exclude_none=False) == {'width': 3, 'height': 4, 'Area': 12, 'volume': None}
    assert s.to_python(Model(3, 4), exclude_none=True) == {'width': 3, 'height': 4, 'Area': 12}
    assert s.to_python(Model(3, 4), mode='json', exclude_none=False) == {
        'width': 3,
        'height': 4,
        'Area': 12,
        'volume': None,
    }
    assert s.to_python(Model(3, 4), mode='json', exclude_none=True) == {'width': 3, 'height': 4, 'Area': 12}


@pytest.mark.skipif(cached_property is None, reason='cached_property is not available')
def test_cached_property_alias():
    @dataclasses.dataclass
    class Model:
        width: int
        height: int

        @cached_property
        def area(self) -> int:
            return self.width * self.height

    s = SchemaSerializer(
        core_schema.model_schema(
            Model,
            core_schema.model_fields_schema(
                {
                    'width': core_schema.model_field(core_schema.int_schema()),
                    'height': core_schema.model_field(core_schema.int_schema()),
                },
                computed_fields=[core_schema.computed_field('area', core_schema.int_schema())],
            ),
        )
    )
    assert s.to_python(Model(3, 4)) == {'width': 3, 'height': 4, 'area': 12}
    assert s.to_python(Model(3, 4), mode='json') == {'width': 3, 'height': 4, 'area': 12}
    assert s.to_json(Model(3, 4)) == b'{"width":3,"height":4,"area":12}'


def test_property_attribute_error():
    @dataclasses.dataclass
    class Model:
        width: int

    s = SchemaSerializer(
        core_schema.model_schema(
            Model,
            core_schema.model_fields_schema(
                {'width': core_schema.model_field(core_schema.int_schema())},
                computed_fields=[core_schema.computed_field('area', core_schema.bytes_schema())],
            ),
        )
    )
    with pytest.raises(AttributeError, match="^'Model' object has no attribute 'area'$"):
        s.to_python(Model(3))
    with pytest.raises(AttributeError, match="^'Model' object has no attribute 'area'$"):
        s.to_python(Model(3), mode='json')

    e = "^Error serializing to JSON: AttributeError: 'Model' object has no attribute 'area'$"
    with pytest.raises(PydanticSerializationError, match=e):
        s.to_json(Model(3))


def test_property_other_error():
    @dataclasses.dataclass
    class Model:
        width: int

        @property
        def area(self) -> int:
            raise ValueError('xxx')

    s = SchemaSerializer(
        core_schema.model_schema(
            Model,
            core_schema.model_fields_schema(
                {'width': core_schema.model_field(core_schema.int_schema())},
                computed_fields=[core_schema.computed_field('area', core_schema.bytes_schema())],
            ),
        )
    )
    with pytest.raises(ValueError, match='^xxx$'):
        s.to_python(Model(3))

    with pytest.raises(ValueError, match='^xxx$'):
        s.to_python(Model(3), mode='json')

    e = '^Error serializing to JSON: ValueError: xxx$'
    with pytest.raises(PydanticSerializationError, match=e):
        s.to_json(Model(3))


def test_property_include_exclude():
    @dataclasses.dataclass
    class Model:
        a: int

        @property
        def b(self):
            return [1, 2, b'3']

    s = SchemaSerializer(
        core_schema.model_schema(
            Model,
            core_schema.model_fields_schema(
                {'a': core_schema.model_field(core_schema.int_schema())},
                computed_fields=[core_schema.computed_field('b', core_schema.list_schema())],
            ),
        )
    )
    assert s.to_python(Model(1)) == {'a': 1, 'b': [1, 2, b'3']}
    assert s.to_python(Model(1), exclude={'b'}) == {'a': 1}
    assert s.to_python(Model(1), include={'a'}) == {'a': 1}
    assert s.to_python(Model(1), exclude={'b': [0]}) == {'a': 1, 'b': [2, b'3']}

    assert s.to_python(Model(1), mode='json') == {'a': 1, 'b': [1, 2, '3']}
    assert s.to_python(Model(1), mode='json', exclude={'b'}) == {'a': 1}
    assert s.to_python(Model(1), mode='json', include={'a'}) == {'a': 1}
    assert s.to_python(Model(1), mode='json', exclude={'b': [0]}) == {'a': 1, 'b': [2, '3']}

    assert s.to_json(Model(1)) == b'{"a":1,"b":[1,2,"3"]}'
    assert s.to_json(Model(1), exclude={'b'}) == b'{"a":1}'
    assert s.to_json(Model(1), include={'a'}) == b'{"a":1}'
    assert s.to_json(Model(1), exclude={'b': [0]}) == b'{"a":1,"b":[2,"3"]}'


@pytest.mark.skipif(cached_property is None, reason='cached_property is not available')
def test_property_setter():
    class Square:
        side: float

        def __init__(self, **kwargs):
            self.__dict__ = kwargs

        @property
        def area(self) -> float:
            return self.side**2

        @area.setter
        def area(self, area: float) -> None:
            self.side = area**0.5

        @area.deleter
        def area(self) -> None:
            self.side = 0.0

        @cached_property
        def random_n(self) -> int:
            return randint(0, 1_000)

    s = SchemaSerializer(
        core_schema.model_schema(
            Square,
            core_schema.model_fields_schema(
                {'side': core_schema.model_field(core_schema.float_schema())},
                computed_fields=[
                    core_schema.computed_field('area', core_schema.float_schema()),
                    core_schema.computed_field('random_n', core_schema.int_schema(), alias='The random number'),
                ],
            ),
        )
    )

    sq = Square(side=10.0)
    the_random_n = sq.random_n
    assert s.to_python(sq, by_alias=True) == {'side': 10.0, 'area': 100.0, 'The random number': the_random_n}
    assert s.to_json(sq, by_alias=True) == b'{"side":10.0,"area":100.0,"The random number":%d}' % the_random_n
    sq.area = 49.0
    assert s.to_python(sq, by_alias=False) == {'side': 7, 'area': 49, 'random_n': the_random_n}
    assert s.to_json(sq, by_alias=False) == b'{"side":7.0,"area":49.0,"random_n":%d}' % the_random_n
    del sq.area
    assert s.to_python(sq, by_alias=False) == {'side': 0, 'area': 0, 'random_n': the_random_n}
    assert s.to_python(sq, exclude={'random_n'}) == {'side': 0, 'area': 0}


def test_extra():
    class MyModel:
        # this is not required, but it avoids `__pydantic_fields_set__` being included in `__dict__`
        __slots__ = '__dict__', '__pydantic_fields_set__', '__pydantic_extra__', '__pydantic_private__'
        field_a: str
        field_b: int

    schema = core_schema.model_schema(
        MyModel,
        core_schema.model_fields_schema(
            {
                'field_a': core_schema.model_field(core_schema.bytes_schema()),
                'field_b': core_schema.model_field(core_schema.int_schema()),
            },
            extra_behavior='allow',
        ),
        extra_behavior='allow',
    )
    v = SchemaValidator(schema)
    m = v.validate_python({'field_a': b'test', 'field_b': 12, 'field_c': 'extra'})
    assert isinstance(m, MyModel)
    assert m.__dict__ == {'field_a': b'test', 'field_b': 12}
    assert m.__pydantic_extra__ == {'field_c': 'extra'}
    assert m.__pydantic_fields_set__ == {'field_a', 'field_b', 'field_c'}

    s = SchemaSerializer(schema)
    assert 'mode:ModelExtra' in plain_repr(s)
    assert 'has_extra:true' in plain_repr(s)
    assert s.to_python(m) == {'field_a': b'test', 'field_b': 12, 'field_c': 'extra'}
    assert s.to_python(m, mode='json') == {'field_a': 'test', 'field_b': 12, 'field_c': 'extra'}
    assert s.to_json(m) == b'{"field_a":"test","field_b":12,"field_c":"extra"}'

    # test filtering
    m = v.validate_python({'field_a': b'test', 'field_b': 12, 'field_c': None, 'field_d': [1, 2, 3]})
    assert isinstance(m, MyModel)
    assert m.__dict__ == {'field_a': b'test', 'field_b': 12}
    assert m.__pydantic_extra__ == {'field_c': None, 'field_d': [1, 2, 3]}
    assert m.__pydantic_fields_set__ == {'field_a', 'field_b', 'field_c', 'field_d'}

    assert s.to_python(m) == {'field_a': b'test', 'field_b': 12, 'field_c': None, 'field_d': [1, 2, 3]}
    assert s.to_json(m) == b'{"field_a":"test","field_b":12,"field_c":null,"field_d":[1,2,3]}'

    assert s.to_python(m, exclude_none=True) == {'field_a': b'test', 'field_b': 12, 'field_d': [1, 2, 3]}
    assert s.to_json(m, exclude_none=True) == b'{"field_a":"test","field_b":12,"field_d":[1,2,3]}'

    assert s.to_python(m, exclude={'field_c'}) == {'field_a': b'test', 'field_b': 12, 'field_d': [1, 2, 3]}
    assert s.to_json(m, exclude={'field_c'}) == b'{"field_a":"test","field_b":12,"field_d":[1,2,3]}'

    assert s.to_python(m, exclude={'field_d': [0]}) == {
        'field_a': b'test',
        'field_b': 12,
        'field_c': None,
        'field_d': [2, 3],
    }
    assert s.to_json(m, exclude={'field_d': [0]}) == b'{"field_a":"test","field_b":12,"field_c":null,"field_d":[2,3]}'


def test_extra_config():
    class MyModel:
        # this is not required, but it avoids `__pydantic_fields_set__` being included in `__dict__`
        __slots__ = '__dict__', '__pydantic_fields_set__', '__pydantic_extra__', '__pydantic_private__'
        field_a: str
        field_b: int

    schema = core_schema.model_schema(
        MyModel,
        core_schema.model_fields_schema(
            {
                'field_a': core_schema.model_field(core_schema.bytes_schema()),
                'field_b': core_schema.model_field(core_schema.int_schema()),
            }
        ),
        config=core_schema.CoreConfig(extra_fields_behavior='allow'),
    )
    s = SchemaSerializer(schema)
    assert 'mode:ModelExtra' in plain_repr(s)
    assert 'has_extra:true' in plain_repr(s)


def test_extra_config_nested_model():
    class OuterModel:
        pass

    class InnerModel:
        pass

    schema = core_schema.model_schema(
        OuterModel,
        core_schema.model_fields_schema(
            {
                'sub_model': core_schema.model_field(
                    core_schema.model_schema(
                        InnerModel,
                        core_schema.model_fields_schema({'int': core_schema.model_field(core_schema.int_schema())}),
                        config=core_schema.CoreConfig(extra_fields_behavior='allow'),
                    )
                )
            }
        ),
        config={},
    )
    s = SchemaSerializer(schema)
    # debug(s)
    s_repr = plain_repr(s)
    assert 'has_extra:true,root_model:false,name:"InnerModel"' in s_repr
    assert 'has_extra:false,root_model:false,name:"OuterModel"' in s_repr


def test_extra_custom_serializer():
    class Model:
        __slots__ = ('__pydantic_extra__', '__dict__')
        __pydantic_extra__: Dict[str, Any]

    schema = core_schema.model_schema(
        Model,
        core_schema.model_fields_schema(
            {},
            extra_behavior='allow',
            extras_schema=core_schema.any_schema(
                serialization=core_schema.plain_serializer_function_ser_schema(lambda v: v + ' bam!')
            ),
        ),
        extra_behavior='allow',
    )
    s = SchemaSerializer(schema)

    m = Model()
    m.__pydantic_extra__ = {'extra': 'extra'}

    assert s.to_python(m) == {'extra': 'extra bam!'}
