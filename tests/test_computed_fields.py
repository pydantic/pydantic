import random

import pytest

from pydantic import BaseModel, Field, PrivateAttr, ValidationError, computed_field

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

    assert rect.model_computed_fields['area'].info.description == 'An awesome area'
    assert rect.model_computed_fields['area2'].info.title == 'Pikarea'
    assert rect.model_computed_fields['area2'].info.description == 'Another area'

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


@pytest.mark.skip(reason='ComputedField not implemented yet')
def test_computed_field_syntax():
    from pydantic import ComputedField

    class User(BaseModel):
        first_name: str
        surname: str
        full_name: str = ComputedField(lambda self: f'{self.first_name} {self.surname}')

    u = User(first_name='John', surname='Smith')
    assert u.model_dump() == {'first_name': 'John', 'surname': 'Smith', 'full_name': 'John Smith'}
    u.first_name = 'Mike'
    assert u.model_dump()['full_name'] == 'Mike Smith'

    with pytest.raises(ValidationError) as exc_info:
        User(first_name='pika', surname='chu')
    assert exc_info.value.errors() == [
        {
            'loc': ('full_name',),
            'msg': 'We love pika but not that much!',
            'type': 'value_error',
        }
    ]


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
