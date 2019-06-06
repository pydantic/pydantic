from typing import List

import pytest

from pydantic import BaseModel, ConfigError, ValidationError
from pydantic.utils import GetterDict


def test_getdict():
    class TestCls:
        a = 1
        b: int

        def __init__(self):
            self.c = 3

        @property
        def d(self):
            return 4

        def __getattr__(self, key):
            if key == 'e':
                return 5
            else:
                raise AttributeError()

    t = TestCls()
    gd = GetterDict(t)
    assert gd.keys() == set()
    assert gd.get('a', None) == 1
    assert gd.get('b', None) is None
    assert gd.get('b', 1234) == 1234
    assert gd.get('c', None) == 3
    assert gd.get('d', None) == 4
    assert gd.get('e', None) == 5
    assert gd.get('f', 'missing') == 'missing'


def test_orm_mode():
    class PetCls:
        def __init__(self, *, name: str, species: str):
            self.name = name
            self.species = species

    class PersonCls:
        def __init__(self, *, name: str, age: float = None, pets: List[PetCls]):
            self.name = name
            self.age = age
            self.pets = pets

    class Pet(BaseModel):
        name: str
        species: str

        class Config:
            orm_mode = True

    class Person(BaseModel):
        name: str
        age: float = None
        pets: List[Pet]

        class Config:
            orm_mode = True

    bones = PetCls(name='Bones', species='dog')
    orion = PetCls(name='Orion', species='cat')
    anna = PersonCls(name='Anna', age=20, pets=[bones, orion])

    anna_model = Person.from_orm(anna)

    assert anna_model.dict() == {
        'name': 'Anna',
        'pets': [{'name': 'Bones', 'species': 'dog'}, {'name': 'Orion', 'species': 'cat'}],
        'age': 20.0,
    }


def test_not_orm_mode():
    class Pet(BaseModel):
        name: str
        species: str

    with pytest.raises(ConfigError):
        Pet.from_orm(None)


def test_object_with_getattr():
    class FooGetAttr:
        def __getattr__(self, key: str):
            if key == 'foo':
                return 'Foo'
            else:
                raise AttributeError

    class Model(BaseModel):
        foo: str
        bar: int = 1

        class Config:
            orm_mode = True

    class ModelInvalid(BaseModel):
        foo: str
        bar: int

        class Config:
            orm_mode = True

    foo = FooGetAttr()
    model = Model.from_orm(foo)
    assert model.foo == 'Foo'
    assert model.bar == 1
    assert model.dict(skip_defaults=True) == {'foo': 'Foo'}
    with pytest.raises(ValidationError):
        ModelInvalid.from_orm(foo)


def test_properties():
    class XyProperty:
        x = 4

        @property
        def y(self):
            return '5'

    class Model(BaseModel):
        x: int
        y: int

        class Config:
            orm_mode = True

    model = Model.from_orm(XyProperty())
    assert model.x == 4
    assert model.y == 5


def test_extra_allow():
    class TestCls:
        x = 1
        y = 2

    class Model(BaseModel):
        x: int

        class Config:
            orm_mode = True
            extra = 'allow'

    model = Model.from_orm(TestCls())
    assert model.dict() == {'x': 1}


def test_extra_forbid():
    class TestCls:
        x = 1
        y = 2

    class Model(BaseModel):
        x: int

        class Config:
            orm_mode = True
            extra = 'forbid'

    model = Model.from_orm(TestCls())
    assert model.dict() == {'x': 1}
