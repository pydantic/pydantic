from __future__ import annotations as _annotations

import random
import sys
from abc import ABC, abstractmethod
from typing import Any, ClassVar

import pytest
from pydantic_core import PydanticSerializationError, ValidationError

from pydantic import (
    BaseModel,
    Field,
    PrivateAttr,
    TypeAdapter,
    computed_field,
    dataclasses,
    field_validator,
)

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


@pytest.mark.skip(reason='waiting for https://github.com/pydantic/pydantic/issues/4697')
def test_computed_fields_json_schema():
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

    assert Rectangle.model_json_schema() == {
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
                'type': 'integer',
                'readOnly': True,
            },
        },
        'required': ['width', 'length'],
    }


def test_computed_fields_set():
    class Square(BaseModel):
        side: float

        @computed_field
        @property
        def area(self) -> float:
            return self.side**2

        @area.setter
        def area(self, new_area: int):
            self.side = new_area**0.5

    s = Square(side=10)
    assert s.model_dump() == {'side': 10.0, 'area': 100.0}
    s.area = 64
    assert s.model_dump() == {'side': 8.0, 'area': 64.0}


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
        def x_list(self) -> list[int]:
            return [self.x, self.x + 1]

        @computed_field
        def y_list(self) -> list[int]:
            return [self.y, self.y + 1, self.y + 2]

    m = Model(x=1, y=2)
    assert m.model_dump() == {'x': 1, 'y': 2, 'x_list': [1, 2], 'y_list': [2, 3, 4]}
    assert m.model_dump(include={'x'}) == {'x': 1}
    assert m.model_dump(include={'x': None, 'x_list': {0}}) == {'x': 1, 'x_list': [1]}
    assert m.model_dump(exclude={'x': ..., 'y_list': {2}}) == {'y': 2, 'x_list': [1, 2], 'y_list': [2, 3]}


def test_expected_type():
    class Model(BaseModel):
        x: int
        y: int

        @computed_field(json_return_type='list')
        def x_list(self) -> list[int]:
            return [self.x, self.x + 1]

        @computed_field(json_return_type='bytes')
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

        @computed_field(json_return_type='list')
        def x_list(self) -> list[int]:
            return 'not a list'

    m = Model(x=1)
    with pytest.raises(TypeError, match="^'str' object cannot be converted to 'PyList'$"):
        m.model_dump()
    with pytest.raises(TypeError, match="^'str' object cannot be converted to 'PyList'$"):
        m.model_dump(mode='json')
    with pytest.raises(PydanticSerializationError, match="Error serializing to JSON: 'str' object cannot be converted"):
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

        @computed_field
        def _double(self) -> int:
            return self.x * 2

    m = MyModel(x=2)
    assert repr(m) == 'MyModel(x=2, _double=4)'
    assert m.__private_attributes__ == {}
    assert m._double == 4
    assert m.model_dump() == {'x': 2, '_double': 4}


@pytest.mark.skipif(sys.version_info < (3, 9), reason='fails before 3.9 - Do we want to fix this???')
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

    with pytest.raises(TypeError, match='"Square" is frozen and does not support item assignment'):
        m.area = 4


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


@pytest.mark.parametrize(
    'bases',
    [
        (BaseModel, ABC),
        (ABC, BaseModel),
        (BaseModel,),
    ],
)
def test_abstractmethod_missing(bases: tuple[Any, ...]):
    class AbstractSquare(*bases):
        side: float

        @computed_field
        @property
        @abstractmethod
        def area(self) -> float:
            raise NotImplementedError()

    class Square(AbstractSquare):
        pass

    with pytest.raises(TypeError, match="Can't instantiate abstract class Square with abstract methods? area"):
        Square(side=4.0)
