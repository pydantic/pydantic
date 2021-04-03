import random

import pytest

from pydantic import BaseModel
from pydantic.fields import Field, field

try:
    from functools import cached_property
except ImportError:
    cached_property = None


def test_computed_fields_get():
    class Rectangle(BaseModel):
        width: int
        length: int

        @field
        @property
        def area(self) -> int:
            """An awesome area"""
            return self.width * self.length

        @field(title='Pikarea', description='Another area')
        @property
        def area2(self) -> int:
            return self.width * self.length

        @property
        def double_width(self) -> int:
            return self.width * 2

    rect = Rectangle(width=10, length=5)
    assert set(rect.__fields__) == {'width', 'length'}
    assert set(rect.__computed_fields__) == {'area', 'area2'}
    assert rect.__dict__ == {'width': 10, 'length': 5}

    assert rect.area == 50
    assert rect.double_width == 20
    assert rect.dict() == {'width': 10, 'length': 5, 'area': 50, 'area2': 50}
    assert rect.json() == '{"width": 10, "length": 5, "area": 50, "area2": 50}'
    assert Rectangle.schema() == {
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

        @field
        def area(self) -> float:
            return self.side ** 2

        @area.setter
        def area(self, new_area: int):
            self.side = new_area ** 0.5

    s = Square(side=10)
    assert s.dict() == {'side': 10.0, 'area': 100.0}
    s.area = 64
    assert s.dict() == {'side': 8.0, 'area': 64.0}
    assert Square.schema() == {
        'title': 'Square',
        'type': 'object',
        'properties': {
            'side': {
                'title': 'Side',
                'type': 'number',
            },
            'area': {
                'title': 'Area',
                'type': 'number',
            },
        },
        'required': ['side'],
    }


def test_computed_fields_del():
    class User(BaseModel):
        first: str
        last: str

        @field
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
    assert user.dict() == {'first': 'John', 'last': 'Smith', 'fullname': 'John Smith'}
    user.fullname = 'Pika Chu'
    assert user.dict() == {'first': 'Pika', 'last': 'Chu', 'fullname': 'Pika Chu'}
    del user.fullname
    assert user.dict() == {'first': '', 'last': '', 'fullname': ' '}


@pytest.mark.skipif(cached_property is None, reason='Need cached_property')
def test_cached_property():
    class Model(BaseModel):
        minimum: int = Field(alias='min')
        maximum: int = Field(alias='max')

        @field(alias='the magic number')
        @cached_property
        def random_number(self) -> int:
            """An awesome area"""
            return random.randint(self.minimum, self.maximum)

    rect = Model(min=10, max=10_000)
    first_n = rect.random_number
    second_n = rect.random_number
    assert first_n == second_n
    assert rect.dict() == {'minimum': 10, 'maximum': 10_000, 'random_number': first_n}
    assert rect.dict(by_alias=True, exclude={'random_number'}) == {'min': 10, 'max': 10000, 'the magic number': first_n}
