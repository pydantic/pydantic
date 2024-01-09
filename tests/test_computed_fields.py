import random
import sys
from abc import ABC, abstractmethod
from typing import Any, Callable, ClassVar, Generic, List, Tuple, TypeVar

import pytest
from pydantic_core import ValidationError, core_schema
from typing_extensions import TypedDict

from pydantic import (
    BaseModel,
    Field,
    GetCoreSchemaHandler,
    PrivateAttr,
    TypeAdapter,
    computed_field,
    dataclasses,
    field_serializer,
    field_validator,
)
from pydantic.alias_generators import to_camel
from pydantic.errors import PydanticUserError

try:
    from functools import cached_property, lru_cache, singledispatchmethod
except ImportError:
    cached_property = None
    lru_cache = None
    singledispatchmethod = None


def test_computed_fields_get():
    class Rectangle(BaseModel):
        width: int
        length: int

        @computed_field
        def area(self) -> int:
            """An awesome area"""
            return self.width * self.length

        @computed_field(title='Pikarea', description='Another area')
        @property
        def area2(self) -> int:
            return self.width * self.length

        @property
        def double_width(self) -> int:
            return self.width * 2

    rect = Rectangle(width=10, length=5)
    assert set(rect.model_fields) == {'width', 'length'}
    assert set(rect.model_computed_fields) == {'area', 'area2'}
    assert rect.__dict__ == {'width': 10, 'length': 5}

    assert rect.model_computed_fields['area'].description == 'An awesome area'
    assert rect.model_computed_fields['area2'].title == 'Pikarea'
    assert rect.model_computed_fields['area2'].description == 'Another area'

    assert rect.area == 50
    assert rect.double_width == 20
    assert rect.model_dump() == {'width': 10, 'length': 5, 'area': 50, 'area2': 50}
    assert rect.model_dump_json() == '{"width":10,"length":5,"area":50,"area2":50}'

    assert set(Rectangle.model_fields) == {'width', 'length'}
    assert set(Rectangle.model_computed_fields) == {'area', 'area2'}

    assert Rectangle.model_computed_fields['area'].description == 'An awesome area'
    assert Rectangle.model_computed_fields['area2'].title == 'Pikarea'
    assert Rectangle.model_computed_fields['area2'].description == 'Another area'


def test_computed_fields_json_schema():
    class Rectangle(BaseModel):
        width: int
        length: int

        @computed_field
        def area(self) -> int:
            """An awesome area"""
            return self.width * self.length

        @computed_field(
            title='Pikarea',
            description='Another area',
            examples=[100, 200],
            json_schema_extra={'foo': 42},
        )
        @property
        def area2(self) -> int:
            return self.width * self.length

        @property
        def double_width(self) -> int:
            return self.width * 2

    assert Rectangle.model_json_schema(mode='serialization') == {
        'title': 'Rectangle',
        'type': 'object',
        'properties': {
            'width': {
                'title': 'Width',
                'type': 'integer',
            },
            'length': {
                'title': 'Length',
                'type': 'integer',
            },
            'area': {
                'title': 'Area',
                'description': 'An awesome area',
                'type': 'integer',
                'readOnly': True,
            },
            'area2': {
                'title': 'Pikarea',
                'description': 'Another area',
                'examples': [100, 200],
                'foo': 42,
                'type': 'integer',
                'readOnly': True,
            },
        },
        'required': ['width', 'length', 'area', 'area2'],
    }


def test_computed_fields_set():
    class Square(BaseModel):
        side: float

        @computed_field
        @property
        def area(self) -> float:
            return self.side**2

        @computed_field
        @property
        def area_string(self) -> str:
            return f'{self.area} square units'

        @field_serializer('area_string')
        def serialize_area_string(self, area_string):
            return area_string.upper()

        @area.setter
        def area(self, new_area: int):
            self.side = new_area**0.5

    s = Square(side=10)
    assert s.model_dump() == {'side': 10.0, 'area': 100.0, 'area_string': '100.0 SQUARE UNITS'}
    s.area = 64
    assert s.model_dump() == {'side': 8.0, 'area': 64.0, 'area_string': '64.0 SQUARE UNITS'}


def test_computed_fields_del():
    class User(BaseModel):
        first: str
        last: str

        @computed_field
        def fullname(self) -> str:
            return f'{self.first} {self.last}'

        @fullname.setter
        def fullname(self, new_fullname: str) -> None:
            self.first, self.last = new_fullname.split()

        @fullname.deleter
        def fullname(self):
            self.first = ''
            self.last = ''

    user = User(first='John', last='Smith')
    assert user.model_dump() == {'first': 'John', 'last': 'Smith', 'fullname': 'John Smith'}
    user.fullname = 'Pika Chu'
    assert user.model_dump() == {'first': 'Pika', 'last': 'Chu', 'fullname': 'Pika Chu'}
    del user.fullname
    assert user.model_dump() == {'first': '', 'last': '', 'fullname': ' '}


@pytest.mark.skipif(cached_property is None, reason='cached_property not available')
def test_cached_property():
    class Model(BaseModel):
        minimum: int = Field(alias='min')
        maximum: int = Field(alias='max')

        @computed_field(alias='the magic number')
        @cached_property
        def random_number(self) -> int:
            """An awesome area"""
            return random.randint(self.minimum, self.maximum)

        @cached_property
        def cached_property_2(self) -> int:
            return 42

        @cached_property
        def _cached_property_3(self) -> int:
            return 43

    rect = Model(min=10, max=10_000)
    assert rect.__private_attributes__ == {}
    assert rect.cached_property_2 == 42
    assert rect._cached_property_3 == 43
    first_n = rect.random_number
    second_n = rect.random_number
    assert first_n == second_n
    assert rect.model_dump() == {'minimum': 10, 'maximum': 10_000, 'random_number': first_n}
    assert rect.model_dump(by_alias=True) == {'min': 10, 'max': 10_000, 'the magic number': first_n}
    assert rect.model_dump(by_alias=True, exclude={'random_number'}) == {'min': 10, 'max': 10000}


def test_properties_and_computed_fields():
    class Model(BaseModel):
        x: str
        _private_float: float = PrivateAttr(0)

        @property
        def public_int(self) -> int:
            return int(self._private_float)

        @public_int.setter
        def public_int(self, v: float) -> None:
            self._private_float = v

        @computed_field
        @property
        def public_str(self) -> str:
            return f'public {self.public_int}'

    m = Model(x='pika')
    assert m.model_dump() == {'x': 'pika', 'public_str': 'public 0'}
    m._private_float = 3.1
    assert m.model_dump() == {'x': 'pika', 'public_str': 'public 3'}
    m.public_int = 2
    assert m._private_float == 2.0
    assert m.model_dump() == {'x': 'pika', 'public_str': 'public 2'}


def test_computed_fields_repr():
    class Model(BaseModel):
        x: int

        @computed_field(repr=False)
        @property
        def double(self) -> int:
            return self.x * 2

        @computed_field  # repr=True by default
        @property
        def triple(self) -> int:
            return self.x * 3

    assert repr(Model(x=2)) == 'Model(x=2, triple=6)'


@pytest.mark.skipif(singledispatchmethod is None, reason='singledispatchmethod not available')
def test_functools():
    class Model(BaseModel, frozen=True):
        x: int

        @lru_cache
        def x_pow(self, p):
            return self.x**p

        @singledispatchmethod
        def neg(self, arg):
            raise NotImplementedError('Cannot negate a')

        @neg.register
        def _(self, arg: int):
            return -arg

        @neg.register
        def _(self, arg: bool):
            return not arg

    m = Model(x=2)
    assert m.x_pow(1) == 2
    assert m.x_pow(2) == 4
    assert m.neg(1) == -1
    assert m.neg(True) is False


def test_include_exclude():
    class Model(BaseModel):
        x: int
        y: int

        @computed_field
        def x_list(self) -> List[int]:
            return [self.x, self.x + 1]

        @computed_field
        def y_list(self) -> List[int]:
            return [self.y, self.y + 1, self.y + 2]

    m = Model(x=1, y=2)
    assert m.model_dump() == {'x': 1, 'y': 2, 'x_list': [1, 2], 'y_list': [2, 3, 4]}
    assert m.model_dump(include={'x'}) == {'x': 1}
    assert m.model_dump(include={'x': None, 'x_list': {0}}) == {'x': 1, 'x_list': [1]}
    assert m.model_dump(exclude={'x': ..., 'y_list': {2}}) == {'y': 2, 'x_list': [1, 2], 'y_list': [2, 3]}


def test_exclude_none():
    class Model(BaseModel):
        x: int
        y: int

        @computed_field
        def sum(self) -> int:
            return self.x + self.y

        @computed_field
        def none(self) -> None:
            return None

    m = Model(x=1, y=2)
    assert m.model_dump(exclude_none=False) == {'x': 1, 'y': 2, 'sum': 3, 'none': None}
    assert m.model_dump(exclude_none=True) == {'x': 1, 'y': 2, 'sum': 3}
    assert m.model_dump(mode='json', exclude_none=False) == {'x': 1, 'y': 2, 'sum': 3, 'none': None}
    assert m.model_dump(mode='json', exclude_none=True) == {'x': 1, 'y': 2, 'sum': 3}


def test_expected_type():
    class Model(BaseModel):
        x: int
        y: int

        @computed_field
        def x_list(self) -> List[int]:
            return [self.x, self.x + 1]

        @computed_field
        def y_str(self) -> bytes:
            s = f'y={self.y}'
            return s.encode()

    m = Model(x=1, y=2)
    assert m.model_dump() == {'x': 1, 'y': 2, 'x_list': [1, 2], 'y_str': b'y=2'}
    assert m.model_dump(mode='json') == {'x': 1, 'y': 2, 'x_list': [1, 2], 'y_str': 'y=2'}
    assert m.model_dump_json() == '{"x":1,"y":2,"x_list":[1,2],"y_str":"y=2"}'


def test_expected_type_wrong():
    class Model(BaseModel):
        x: int

        @computed_field
        def x_list(self) -> List[int]:
            return 'not a list'

    m = Model(x=1)
    with pytest.warns(UserWarning, match=r'Expected `list\[int\]` but got `str`'):
        m.model_dump()
    with pytest.warns(UserWarning, match=r'Expected `list\[int\]` but got `str`'):
        m.model_dump(mode='json')
    with pytest.warns(UserWarning, match=r'Expected `list\[int\]` but got `str`'):
        m.model_dump_json()


def test_inheritance():
    class Base(BaseModel):
        x: int

        @computed_field
        def double(self) -> int:
            return self.x * 2

    class Child(Base):
        y: int

        @computed_field
        def triple(self) -> int:
            return self.y * 3

    c = Child(x=2, y=3)
    assert c.double == 4
    assert c.triple == 9
    assert c.model_dump() == {'x': 2, 'y': 3, 'double': 4, 'triple': 9}


def test_dataclass():
    @dataclasses.dataclass
    class MyDataClass:
        x: int

        @computed_field
        def double(self) -> int:
            return self.x * 2

    m = MyDataClass(x=2)
    assert m.double == 4
    assert TypeAdapter(MyDataClass).dump_python(m) == {'x': 2, 'double': 4}


def test_free_function():
    @property
    def double_func(self) -> int:
        return self.x * 2

    class MyModel(BaseModel):
        x: int
        double = computed_field(double_func)

    m = MyModel(x=2)
    assert set(m.model_fields) == {'x'}
    assert m.__private_attributes__ == {}
    assert m.double == 4
    assert repr(m) == 'MyModel(x=2, double=4)'
    assert m.model_dump() == {'x': 2, 'double': 4}


def test_private_computed_field():
    class MyModel(BaseModel):
        x: int

        @computed_field(repr=True)
        def _double(self) -> int:
            return self.x * 2

    m = MyModel(x=2)
    assert repr(m) == 'MyModel(x=2, _double=4)'
    assert m.__private_attributes__ == {}
    assert m._double == 4
    assert m.model_dump() == {'x': 2, '_double': 4}


@pytest.mark.skipif(sys.version_info < (3, 9), reason='@computed_field @classmethod @property only works in 3.9+')
def test_classmethod():
    class MyModel(BaseModel):
        x: int
        y: ClassVar[int] = 4

        @computed_field
        @classmethod
        @property
        def two_y(cls) -> int:
            return cls.y * 2

    m = MyModel(x=1)
    assert m.two_y == 8
    assert m.model_dump() == {'x': 1, 'two_y': 8}


def test_frozen():
    class Square(BaseModel, frozen=True):
        side: float

        @computed_field
        @property
        def area(self) -> float:
            return self.side**2

        @area.setter
        def area(self, new_area: int):
            self.side = new_area**0.5

    m = Square(side=4)
    assert m.area == 16.0
    assert m.model_dump() == {'side': 4.0, 'area': 16.0}

    with pytest.raises(ValidationError) as exc_info:
        m.area = 4
    assert exc_info.value.errors(include_url=False) == [
        {'type': 'frozen_instance', 'loc': ('area',), 'msg': 'Instance is frozen', 'input': 4}
    ]


def test_validate_assignment():
    class Square(BaseModel, validate_assignment=True):
        side: float

        @field_validator('side')
        def small_side(cls, s):
            if s < 2:
                raise ValueError('must be >=2')
            return float(round(s))

        @computed_field
        @property
        def area(self) -> float:
            return self.side**2

        @area.setter
        def area(self, new_area: int):
            self.side = new_area**0.5

    with pytest.raises(ValidationError, match=r'side\s+Value error, must be >=2'):
        Square(side=1)

    m = Square(side=4.0)
    assert m.area == 16.0
    assert m.model_dump() == {'side': 4.0, 'area': 16.0}
    m.area = 10.0
    assert m.side == 3.0

    with pytest.raises(ValidationError, match=r'side\s+Value error, must be >=2'):
        m.area = 3


def test_abstractmethod():
    class AbstractSquare(BaseModel):
        side: float

        @computed_field
        @property
        @abstractmethod
        def area(self) -> float:
            raise NotImplementedError()

    class Square(AbstractSquare):
        @computed_field
        @property
        def area(self) -> float:
            return self.side + 1

    m = Square(side=4.0)
    assert m.model_dump() == {'side': 4.0, 'area': 5.0}


@pytest.mark.skipif(sys.version_info < (3, 12), reason='error message is different on older versions')
@pytest.mark.parametrize(
    'bases',
    [
        (BaseModel, ABC),
        (ABC, BaseModel),
        (BaseModel,),
    ],
)
def test_abstractmethod_missing(bases: Tuple[Any, ...]):
    class AbstractSquare(*bases):
        side: float

        @computed_field
        @property
        @abstractmethod
        def area(self) -> float:
            raise NotImplementedError()

    class Square(AbstractSquare):
        pass

    with pytest.raises(
        TypeError, match="Can't instantiate abstract class Square without an implementation for abstract method 'area'"
    ):
        Square(side=4.0)


class CustomType(str):
    @classmethod
    def __get_pydantic_core_schema__(cls, source: Any, handler: GetCoreSchemaHandler) -> core_schema.CoreSchema:
        schema = handler(str)
        schema['serialization'] = core_schema.plain_serializer_function_ser_schema(lambda x: '123')
        return schema


def test_computed_fields_infer_return_type():
    class Model(BaseModel):
        @computed_field
        def cfield(self) -> CustomType:
            return CustomType('abc')

    assert Model().model_dump() == {'cfield': '123'}
    assert Model().model_dump_json() == '{"cfield":"123"}'


def test_computed_fields_missing_return_type():
    with pytest.raises(PydanticUserError, match='Computed field is missing return type annotation'):

        class _Model(BaseModel):
            @computed_field
            def cfield(self):
                raise NotImplementedError

    class Model(BaseModel):
        @computed_field(return_type=CustomType)
        def cfield(self):
            return CustomType('abc')

    assert Model().model_dump() == {'cfield': '123'}
    assert Model().model_dump_json() == '{"cfield":"123"}'


def test_alias_generator():
    class MyModel(BaseModel):
        my_standard_field: int

        @computed_field  # *will* be overridden by alias generator
        @property
        def my_computed_field(self) -> int:
            return self.my_standard_field + 1

        @computed_field(alias='my_alias_none')  # will *not* be overridden by alias generator
        @property
        def my_aliased_computed_field_none(self) -> int:
            return self.my_standard_field + 2

        @computed_field(alias='my_alias_1', alias_priority=1)  # *will* be overridden by alias generator
        @property
        def my_aliased_computed_field_1(self) -> int:
            return self.my_standard_field + 3

        @computed_field(alias='my_alias_2', alias_priority=2)  # will *not* be overridden by alias generator
        @property
        def my_aliased_computed_field_2(self) -> int:
            return self.my_standard_field + 4

    class MySubModel(MyModel):
        model_config = dict(alias_generator=to_camel, populate_by_name=True)

    model = MyModel(my_standard_field=1)
    assert model.model_dump() == {
        'my_standard_field': 1,
        'my_computed_field': 2,
        'my_aliased_computed_field_none': 3,
        'my_aliased_computed_field_1': 4,
        'my_aliased_computed_field_2': 5,
    }
    assert model.model_dump(by_alias=True) == {
        'my_standard_field': 1,
        'my_computed_field': 2,
        'my_alias_none': 3,
        'my_alias_1': 4,
        'my_alias_2': 5,
    }

    submodel = MySubModel(my_standard_field=1)
    assert submodel.model_dump() == {
        'my_standard_field': 1,
        'my_computed_field': 2,
        'my_aliased_computed_field_none': 3,
        'my_aliased_computed_field_1': 4,
        'my_aliased_computed_field_2': 5,
    }
    assert submodel.model_dump(by_alias=True) == {
        'myStandardField': 1,
        'myComputedField': 2,
        'my_alias_none': 3,
        'myAliasedComputedField1': 4,
        'my_alias_2': 5,
    }


def make_base_model() -> Any:
    class CompModel(BaseModel):
        pass

    class Model(BaseModel):
        @computed_field
        @property
        def comp_1(self) -> CompModel:
            return CompModel()

        @computed_field
        @property
        def comp_2(self) -> CompModel:
            return CompModel()

    return Model


def make_dataclass() -> Any:
    class CompModel(BaseModel):
        pass

    @dataclasses.dataclass
    class Model:
        @computed_field
        @property
        def comp_1(self) -> CompModel:
            return CompModel()

        @computed_field
        @property
        def comp_2(self) -> CompModel:
            return CompModel()

    return Model


def make_typed_dict() -> Any:
    class CompModel(BaseModel):
        pass

    class Model(TypedDict):
        @computed_field  # type: ignore
        @property
        def comp_1(self) -> CompModel:
            return CompModel()

        @computed_field  # type: ignore
        @property
        def comp_2(self) -> CompModel:
            return CompModel()

    return Model


@pytest.mark.parametrize(
    'model_factory',
    [
        make_base_model,
        pytest.param(
            make_typed_dict,
            marks=pytest.mark.xfail(
                reason='computed fields do not work with TypedDict yet. See https://github.com/pydantic/pydantic-core/issues/657'
            ),
        ),
        make_dataclass,
    ],
)
def test_multiple_references_to_schema(model_factory: Callable[[], Any]) -> None:
    """
    https://github.com/pydantic/pydantic/issues/5980
    """

    model = model_factory()

    ta = TypeAdapter(model)

    assert ta.dump_python(model()) == {'comp_1': {}, 'comp_2': {}}

    assert ta.json_schema() == {'type': 'object', 'properties': {}, 'title': 'Model'}

    assert ta.json_schema(mode='serialization') == {
        '$defs': {'CompModel': {'properties': {}, 'title': 'CompModel', 'type': 'object'}},
        'properties': {
            'comp_1': {'allOf': [{'$ref': '#/$defs/CompModel'}], 'readOnly': True},
            'comp_2': {'allOf': [{'$ref': '#/$defs/CompModel'}], 'readOnly': True},
        },
        'required': ['comp_1', 'comp_2'],
        'title': 'Model',
        'type': 'object',
    }


def test_generic_computed_field():
    T = TypeVar('T')

    class A(BaseModel, Generic[T]):
        x: T

        @computed_field
        @property
        def double_x(self) -> T:
            return self.x * 2

    assert A[int](x=1).model_dump() == {'x': 1, 'double_x': 2}
    assert A[str](x='abc').model_dump() == {'x': 'abc', 'double_x': 'abcabc'}

    assert A(x='xxxxxx').model_computed_fields['double_x'].return_type == T
    assert A[int](x=123).model_computed_fields['double_x'].return_type == int
    assert A[str](x='x').model_computed_fields['double_x'].return_type == str

    class B(BaseModel, Generic[T]):
        @computed_field
        @property
        def double_x(self) -> T:
            return 'abc'  # this may not match the annotated return type, and will warn if not

    with pytest.warns(UserWarning, match='Expected `int` but got `str` - serialized value may not be as expected'):
        B[int]().model_dump()


def test_computed_field_override_raises():
    class Model(BaseModel):
        name: str = 'foo'

    with pytest.raises(ValueError, match="you can't override a field with a computed field"):

        class SubModel(Model):
            @computed_field
            @property
            def name(self) -> str:
                return 'bar'
