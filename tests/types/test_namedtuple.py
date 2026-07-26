from collections import namedtuple
from collections.abc import Mapping
from typing import Annotated, Generic, NamedTuple, Optional, TypeVar

import pytest
from typing_extensions import NamedTuple as TypingExtensionsNamedTuple

from pydantic import BaseModel, ConfigDict, Field, PlainSerializer, PositiveInt, TypeAdapter, ValidationError
from pydantic.errors import PydanticSchemaGenerationError


def test_namedtuple_simple():
    Position = namedtuple('Pos', 'x y')

    class Model(BaseModel):
        pos: Position

    model = Model(pos=('1', 2))
    assert isinstance(model.pos, Position)
    assert model.pos.x == '1'
    assert model.pos == Position('1', 2)

    model = Model(pos={'x': '1', 'y': 2})
    assert model.pos == Position('1', 2)


def test_namedtuple():
    class Event(NamedTuple):
        a: int
        b: int
        c: int
        d: str

    class Model(BaseModel):
        # pos: Position
        event: Event

    model = Model(event=(b'1', '2', 3, 'qwe'))
    assert isinstance(model.event, Event)
    assert model.event == Event(1, 2, 3, 'qwe')
    assert repr(model) == "Model(event=Event(a=1, b=2, c=3, d='qwe'))"

    with pytest.raises(ValidationError) as exc_info:
        Model(pos=('1', 2), event=['qwe', '2', 3, 'qwe'])
    # insert_assert(exc_info.value.errors(include_url=False))
    assert exc_info.value.errors(include_url=False) == [
        {
            'type': 'int_parsing',
            'loc': ('event', 0),
            'msg': 'Input should be a valid integer, unable to parse string as an integer',
            'input': 'qwe',
        }
    ]


def test_namedtuple_schema():
    class Position1(NamedTuple):
        x: int
        y: int

    Position2 = namedtuple('Position2', 'x y')

    class Model(BaseModel):
        pos1: Position1
        pos2: Position2
        pos3: tuple[int, int]

    assert Model.model_json_schema() == {
        'title': 'Model',
        'type': 'object',
        '$defs': {
            'Position1': {
                'maxItems': 2,
                'minItems': 2,
                'prefixItems': [{'title': 'X', 'type': 'integer'}, {'title': 'Y', 'type': 'integer'}],
                'type': 'array',
            },
            'Position2': {
                'maxItems': 2,
                'minItems': 2,
                'prefixItems': [{'title': 'X'}, {'title': 'Y'}],
                'type': 'array',
            },
        },
        'properties': {
            'pos1': {'$ref': '#/$defs/Position1'},
            'pos2': {'$ref': '#/$defs/Position2'},
            'pos3': {
                'maxItems': 2,
                'minItems': 2,
                'prefixItems': [{'type': 'integer'}, {'type': 'integer'}],
                'title': 'Pos3',
                'type': 'array',
            },
        },
        'required': ['pos1', 'pos2', 'pos3'],
    }


def test_namedtuple_right_length():
    class Point(NamedTuple):
        x: int
        y: int

    class Model(BaseModel):
        p: Point

    assert isinstance(Model(p=(1, 2)), Model)

    with pytest.raises(ValidationError) as exc_info:
        Model(p=(1, 2, 3))
    # insert_assert(exc_info.value.errors(include_url=False))
    assert exc_info.value.errors(include_url=False) == [
        {
            'type': 'too_long',
            'loc': ('p',),
            'msg': 'NamedTuple should have at most 2 items after validation, not 3',
            'input': (1, 2, 3),
            'ctx': {'field_type': 'NamedTuple', 'max_length': 2, 'actual_length': 3},
        }
    ]


def test_namedtuple_postponed_annotation():
    """https://github.com/pydantic/pydantic/issues/2760"""

    class Tup(NamedTuple):
        v: 'PositiveInt'

    class Model(BaseModel):
        t: Tup

    # The effect of issue #2760 is that this call raises a `PydanticUserError` even though the type declared on `Tup.v`
    # references a binding in this module's global scope.
    with pytest.raises(ValidationError):
        Model.model_validate({'t': [-1]})


def test_namedtuple_different_module(create_module) -> None:
    """https://github.com/pydantic/pydantic/issues/10336"""

    @create_module
    def other_module():
        from typing import NamedTuple

        TestIntOtherModule = int

        class Tup(NamedTuple):
            f: 'TestIntOtherModule'

    class Model(BaseModel):
        tup: other_module.Tup

    assert Model(tup={'f': 1}).tup.f == 1


def test_namedtuple_arbitrary_type():
    class CustomClass:
        pass

    class Tup(NamedTuple):
        c: CustomClass

    class Model(BaseModel):
        x: Tup

        model_config = ConfigDict(arbitrary_types_allowed=True)

    data = {'x': Tup(c=CustomClass())}
    model = Model.model_validate(data)
    assert isinstance(model.x.c, CustomClass)

    with pytest.raises(PydanticSchemaGenerationError):

        class ModelNoArbitraryTypes(BaseModel):
            x: Tup


def test_recursive_namedtuple():
    class MyNamedTuple(NamedTuple):
        x: int
        y: Optional['MyNamedTuple']

    ta = TypeAdapter(MyNamedTuple)
    assert ta.validate_python({'x': 1, 'y': {'x': 2, 'y': None}}) == (1, (2, None))

    with pytest.raises(ValidationError) as exc_info:
        ta.validate_python({'x': 1, 'y': {'x': 2, 'y': {'x': 'a', 'y': None}}})
    assert exc_info.value.errors(include_url=False) == [
        {
            'input': 'a',
            'loc': ('y', 'y', 'x'),
            'msg': 'Input should be a valid integer, unable to parse string as an integer',
            'type': 'int_parsing',
        }
    ]


def test_recursive_generic_namedtuple():
    # Need to use TypingExtensionsNamedTuple to make it work with Python <3.11
    T = TypeVar('T')

    class MyNamedTuple(TypingExtensionsNamedTuple, Generic[T]):
        x: T
        y: Optional['MyNamedTuple[T]']

    ta = TypeAdapter(MyNamedTuple[int])
    assert ta.validate_python({'x': 1, 'y': {'x': 2, 'y': None}}) == (1, (2, None))

    with pytest.raises(ValidationError) as exc_info:
        ta.validate_python({'x': 1, 'y': {'x': 2, 'y': {'x': 'a', 'y': None}}})
    assert exc_info.value.errors(include_url=False) == [
        {
            'input': 'a',
            'loc': ('y', 'y', 'x'),
            'msg': 'Input should be a valid integer, unable to parse string as an integer',
            'type': 'int_parsing',
        }
    ]


def test_namedtuple_defaults():
    class NT(NamedTuple):
        x: int
        y: int = 33

    assert TypeAdapter(NT).validate_python([1]) == (1, 33)
    assert TypeAdapter(NT).validate_python({'x': 22}) == (22, 33)


def test_namedtuple_inheritance_with_annotations():
    """https://github.com/pydantic/pydantic/issues/7987."""

    class Foo(NamedTuple):
        test: str
        test2: str

    class Bar(Foo):
        test3: str

    ta = TypeAdapter(Bar)

    # test3 should not be part of the schema
    assert ta.validate_python({'test': 'a', 'test2': 'b'}) == Bar(test='a', test2='b')

    with pytest.raises(ValidationError) as exc_info:
        ta.validate_python({'test': 'a', 'test2': 'b', 'test3': 'c'})

    assert exc_info.value.errors(include_url=False) == [
        {
            'type': 'extra_forbidden',
            'loc': ('test3',),
            'msg': 'Extra inputs are not permitted',
            'input': 'c',
        }
    ]


def test_namedtuple_smart_union_preserves_class():
    """https://github.com/pydantic/pydantic/issues/12529"""

    class A(NamedTuple):
        x: int

    class B(NamedTuple):
        x: int

    class Model(BaseModel):
        a_or_b: A | B

    assert type(Model(a_or_b=B(x=1)).a_or_b) is B
    assert type(Model(a_or_b=A(x=1)).a_or_b) is A
    # Non-instance inputs still use the first matching member:
    assert type(Model(a_or_b=(1,)).a_or_b) is A


def test_namedtuple_field_serializers():
    """https://github.com/pydantic/pydantic/issues/8155"""

    from pydantic import PlainSerializer

    HexInt = Annotated[int, PlainSerializer(hex, return_type=str)]

    class NT(NamedTuple):
        x: HexInt

    ta = TypeAdapter(NT)
    assert ta.dump_python(NT(255)) == ('0xff',)
    assert ta.dump_json(NT(255)) == b'["0xff"]'


def test_namedtuple_defer_build_serialization():
    """https://github.com/pydantic/pydantic/issues/13448"""

    class LazyModel(BaseModel, defer_build=True):
        x: int

    class LazyNT(NamedTuple):
        bar: LazyModel

    class Model(BaseModel):
        nt: LazyNT

    m = Model(nt=[{'x': 1}])
    assert m.model_dump() == {'nt': ({'x': 1},)}
    assert m.model_dump_json() == '{"nt":[{"x":1}]}'


def test_namedtuple_from_attributes_error_locs():
    """https://github.com/pydantic/pydantic/issues/11925

    Field names (not indices) are used in error locations when validating
    an instance of the named tuple class.
    """

    class NT(NamedTuple):
        x: Annotated[int, Field(gt=0)]

    class Model(BaseModel):
        nt: NT

    class Attributes:
        def __init__(self):
            self.nt = NT(x=0)

    with pytest.raises(ValidationError) as exc_info:
        Model.model_validate(Attributes(), from_attributes=True)
    assert exc_info.value.errors(include_url=False) == [
        {
            'type': 'greater_than',
            'loc': ('nt', 'x'),
            'msg': 'Input should be greater than 0',
            'input': 0,
            'ctx': {'gt': 0},
        }
    ]


def test_namedtuple_strict_ignored():
    """Strict mode is currently ignored for named tuples, matching the behavior of the
    `'call'` core schema previously used for them."""

    class NT(NamedTuple):
        x: int

    ta = TypeAdapter(NT)

    assert ta.validate_python(NT(1), strict=True) == NT(1)
    assert ta.validate_python((1,), strict=True) == NT(1)
    assert ta.validate_python([1], strict=True) == NT(1)
    assert ta.validate_python({'x': 1}, strict=True) == NT(1)
    assert ta.validate_json('[1]', strict=True) == NT(1)
    assert ta.validate_json('{"x": 1}', strict=True) == NT(1)


def test_namedtuple_instances_revalidated():
    class NT(NamedTuple):
        x: int

    ta = TypeAdapter(NT)
    validated = ta.validate_python(NT(x='1'))
    assert validated.x == 1


def test_namedtuple_invalid_input_type():
    class Point(NamedTuple):
        x: int
        y: int

    ta = TypeAdapter(Point)

    with pytest.raises(ValidationError) as exc_info:
        ta.validate_python('invalid')
    assert exc_info.value.errors(include_url=False) == [
        {
            'type': 'named_tuple_type',
            'loc': (),
            'msg': 'Input should be a tuple, list, dictionary or an instance of Point',
            'input': 'invalid',
            'ctx': {'class_name': 'Point'},
        }
    ]

    with pytest.raises(ValidationError) as exc_info:
        ta.validate_json('"invalid"')
    assert exc_info.value.errors(include_url=False) == [
        {
            'type': 'named_tuple_type',
            'loc': (),
            'msg': 'Input should be an array or an object',
            'input': 'invalid',
            'ctx': {'class_name': 'Point'},
        }
    ]


def test_namedtuple_missing_errors():
    """Missing fields use the index as location for positional inputs, and the field name for dict inputs."""

    class Point(NamedTuple):
        x: int
        y: int

    ta = TypeAdapter(Point)

    with pytest.raises(ValidationError) as exc_info:
        ta.validate_python([1])
    assert exc_info.value.errors(include_url=False) == [
        {'type': 'missing', 'loc': (1,), 'msg': 'Field required', 'input': [1]}
    ]

    with pytest.raises(ValidationError) as exc_info:
        ta.validate_python({'x': 1})
    assert exc_info.value.errors(include_url=False) == [
        {'type': 'missing', 'loc': ('y',), 'msg': 'Field required', 'input': {'x': 1}}
    ]


def test_namedtuple_validation_alias():
    class Point(NamedTuple):
        x: Annotated[int, Field(validation_alias='ex')]
        y: int

    ta = TypeAdapter(Point)

    assert ta.validate_python({'ex': 1, 'y': 2}) == Point(1, 2)
    # The alias only applies to dict inputs, positional inputs are unaffected:
    assert ta.validate_python((1, 2)) == Point(1, 2)

    with pytest.raises(ValidationError) as exc_info:
        ta.validate_python({'x': 1, 'y': 2})
    assert exc_info.value.errors(include_url=False) == [
        {'type': 'missing', 'loc': ('ex',), 'msg': 'Field required', 'input': {'x': 1, 'y': 2}},
        {'type': 'extra_forbidden', 'loc': ('x',), 'msg': 'Extra inputs are not permitted', 'input': 1},
    ]


def test_namedtuple_mapping_input():
    class Map(Mapping):
        def __init__(self, **kwargs):
            self._d = kwargs

        def __iter__(self):
            return iter(self._d)

        def __len__(self) -> int:
            return len(self._d)

        def __getitem__(self, k, /):
            return self._d[k]

    class Point(NamedTuple):
        x: int
        y: int

    assert TypeAdapter(Point).validate_python(Map(x=1, y=2)) == Point(1, 2)


def test_namedtuple_other_class_converted():
    """Instances of other named tuple classes are treated as regular tuples (positional)."""

    class A(NamedTuple):
        x: int

    class B(NamedTuple):
        x: int

    validated = TypeAdapter(A).validate_python(B(x=1))
    assert type(validated) is A


def test_namedtuple_serialization():
    class Point(NamedTuple):
        x: int
        y: str

    ta = TypeAdapter(Point)

    dumped = ta.dump_python(Point(1, 'a'))
    assert dumped == (1, 'a')
    assert type(dumped) is tuple
    assert ta.dump_python(Point(1, 'a'), mode='json') == [1, 'a']
    assert ta.dump_json(Point(1, 'a')) == b'[1,"a"]'

    # Any tuple is accepted:
    assert ta.dump_python((1, 'a')) == (1, 'a')


def test_namedtuple_serialization_warnings():
    class Point(NamedTuple):
        x: int
        y: str

    ta = TypeAdapter(Point)

    with pytest.warns(UserWarning, match='Expected `Point` - serialized value may not be as expected'):
        assert ta.dump_python('not a tuple') == 'not a tuple'
    with pytest.warns(UserWarning, match='Unexpected extra items present in named tuple'):
        assert ta.dump_python((1, 'a', 'extra')) == (1, 'a')
    with pytest.warns(UserWarning, match='Unexpected too few items present in named tuple'):
        assert ta.dump_python((1,)) == (1,)


def test_namedtuple_serialization_include_exclude():
    class Point(NamedTuple):
        x: int
        y: str

    ta = TypeAdapter(Point)

    assert ta.dump_python(Point(1, 'a'), include={0}) == (1,)
    assert ta.dump_python(Point(1, 'a'), exclude={0}) == ('a',)
    assert ta.dump_json(Point(1, 'a'), include={0}) == b'[1]'


def test_namedtuple_as_dict_key_serialization():
    class Point(NamedTuple):
        x: int
        y: str

    ta = TypeAdapter(dict[Point, int])
    assert ta.dump_json({Point(1, 'a'): 2}) == b'{"1,a":2}'


def test_namedtuple_union_serialization_preserves_class():
    """In unions, the value must be an instance of the named tuple class for the member to match."""

    class A(NamedTuple):
        x: Annotated[int, PlainSerializer(lambda v: v + 1)]

    class B(NamedTuple):
        x: Annotated[int, PlainSerializer(lambda v: v + 2)]

    ta = TypeAdapter(A | B)
    assert ta.dump_json(A(0)) == b'[1]'
    assert ta.dump_json(B(0)) == b'[2]'
