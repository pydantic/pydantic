from types import SimpleNamespace
from typing import Any, Dict, List

import pytest

from pydantic import BaseModel, ConfigError, ValidationError, root_validator
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
    assert gd.keys() == ['a', 'c', 'd']
    assert gd.get('a') == 1
    assert gd['a'] == 1
    with pytest.raises(KeyError):
        assert gd['foobar']
    assert gd.get('b', None) is None
    assert gd.get('b', 1234) == 1234
    assert gd.get('c', None) == 3
    assert gd.get('d', None) == 4
    assert gd.get('e', None) == 5
    assert gd.get('f', 'missing') == 'missing'
    assert list(gd.values()) == [1, 3, 4]
    assert list(gd.items()) == [('a', 1), ('c', 3), ('d', 4)]
    assert list(gd) == ['a', 'c', 'd']
    assert gd == {'a': 1, 'c': 3, 'd': 4}
    assert 'a' in gd
    assert len(gd) == 3
    assert str(gd) == "{'a': 1, 'c': 3, 'd': 4}"
    assert repr(gd) == "GetterDict[TestCls]({'a': 1, 'c': 3, 'd': 4})"


def test_orm_mode_root():
    class PokemonCls:
        def __init__(self, *, en_name: str, jp_name: str):
            self.en_name = en_name
            self.jp_name = jp_name

    class Pokemon(BaseModel):
        en_name: str
        jp_name: str

        class Config:
            orm_mode = True

    class PokemonList(BaseModel):
        __root__: List[Pokemon]

        class Config:
            orm_mode = True

    pika = PokemonCls(en_name='Pikachu', jp_name='ピカチュウ')
    bulbi = PokemonCls(en_name='Bulbasaur', jp_name='フシギダネ')

    pokemons = PokemonList.from_orm([pika, bulbi])
    assert pokemons.__root__ == [
        Pokemon(en_name='Pikachu', jp_name='ピカチュウ'),
        Pokemon(en_name='Bulbasaur', jp_name='フシギダネ'),
    ]

    class PokemonDict(BaseModel):
        __root__: Dict[str, Pokemon]

        class Config:
            orm_mode = True

    pokemons = PokemonDict.from_orm({'pika': pika, 'bulbi': bulbi})
    assert pokemons.__root__ == {
        'pika': Pokemon(en_name='Pikachu', jp_name='ピカチュウ'),
        'bulbi': Pokemon(en_name='Bulbasaur', jp_name='フシギダネ'),
    }


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
    assert model.dict(exclude_unset=True) == {'foo': 'Foo'}
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


def test_root_validator():
    validator_value = None

    class TestCls:
        x = 1
        y = 2

    class Model(BaseModel):
        x: int
        y: int
        z: int

        @root_validator(pre=True)
        def change_input_data(cls, value):
            nonlocal validator_value
            validator_value = value
            return {**value, 'z': value['x'] + value['y']}

        class Config:
            orm_mode = True

    model = Model.from_orm(TestCls())
    assert model.dict() == {'x': 1, 'y': 2, 'z': 3}
    assert isinstance(validator_value, GetterDict)
    assert validator_value == {'x': 1, 'y': 2}


def test_custom_getter_dict():
    class TestCls:
        x = 1
        y = 2

    def custom_getter_dict(obj):
        assert isinstance(obj, TestCls)
        return {'x': 42, 'y': 24}

    class Model(BaseModel):
        x: int
        y: int

        class Config:
            orm_mode = True
            getter_dict = custom_getter_dict

    model = Model.from_orm(TestCls())
    assert model.dict() == {'x': 42, 'y': 24}


def test_custom_getter_dict_derived_model_class():
    class CustomCollection:
        __custom__ = True

        def __iter__(self):
            yield from range(5)

    class Example:
        def __init__(self, *args, **kwargs):
            self.col = CustomCollection()
            self.id = 1
            self.name = 'name'

    class MyGetterDict(GetterDict):
        def get(self, key: Any, default: Any = None) -> Any:
            res = getattr(self._obj, key, default)
            if hasattr(res, '__custom__'):
                return list(res)
            return res

    class ExampleBase(BaseModel):
        name: str
        col: List[int]

    class ExampleOrm(ExampleBase):
        id: int

        class Config:
            orm_mode = True
            getter_dict = MyGetterDict

    model = ExampleOrm.from_orm(Example())
    assert model.dict() == {'name': 'name', 'col': [0, 1, 2, 3, 4], 'id': 1}


def test_recursive_parsing():
    class Getter(GetterDict):
        # try to read the modified property name
        # either as an attribute or as a key
        def get(self, key, default):
            key = key + key
            try:
                v = self._obj[key]
                return Getter(v) if isinstance(v, dict) else v
            except TypeError:
                return getattr(self._obj, key, default)
            except KeyError:
                return default

    class Model(BaseModel):
        class Config:
            orm_mode = True
            getter_dict = Getter

    class ModelA(Model):
        a: int

    class ModelB(Model):
        b: ModelA

    # test recursive parsing with object attributes
    dct = dict(bb=SimpleNamespace(aa=1))
    assert ModelB.from_orm(dct) == ModelB(b=ModelA(a=1))

    # test recursive parsing with dict keys
    obj = dict(bb=dict(aa=1))
    assert ModelB.from_orm(obj) == ModelB(b=ModelA(a=1))


def test_nested_orm():
    class User(BaseModel):
        first_name: str
        last_name: str

        class Config:
            orm_mode = True

    class State(BaseModel):
        user: User

        class Config:
            orm_mode = True

    # Pass an "orm instance"
    State.from_orm(SimpleNamespace(user=SimpleNamespace(first_name='John', last_name='Appleseed')))

    # Pass dictionary data directly
    State(**{'user': {'first_name': 'John', 'last_name': 'Appleseed'}})
