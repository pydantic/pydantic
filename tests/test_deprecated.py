import platform
import re
from types import SimpleNamespace
from typing import Dict, List

import pytest

from pydantic import BaseModel, ConfigDict, PydanticUserError, ValidationError, model_serializer, root_validator


def deprecated_from_orm(model_type, obj):
    with pytest.warns(
        DeprecationWarning,
        match=re.escape(
            'The `from_orm` method is deprecated; set model_config["from_attributes"]=True '
            'and use `model_validate` instead.'
        ),
    ):
        return model_type.from_orm(obj)


@pytest.mark.xfail(reason='working on V2')
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
    # gd = GetterDict(t)
    gd = object(t)
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


def test_from_attributes_root():
    class PokemonCls:
        def __init__(self, *, en_name: str, jp_name: str):
            self.en_name = en_name
            self.jp_name = jp_name

    class Pokemon(BaseModel):
        model_config = ConfigDict(from_attributes=True)
        en_name: str
        jp_name: str

    class PokemonList(BaseModel):
        root: List[Pokemon]

        @root_validator(pre=True)
        @classmethod
        def populate_root(cls, values):
            return {'root': values}

        @model_serializer(mode='wrap')
        def _serialize(self, handler, info):
            data = handler(self)
            if info.mode == 'json':
                return data['root']
            else:
                return data

        @classmethod
        def model_modify_json_schema(cls, json_schema):
            return json_schema['properties']['root']

        model_config = ConfigDict(from_attributes=True)

    pika = PokemonCls(en_name='Pikachu', jp_name='ピカチュウ')
    bulbi = PokemonCls(en_name='Bulbasaur', jp_name='フシギダネ')

    pokemons = deprecated_from_orm(PokemonList, [pika, bulbi])
    assert pokemons.root == [
        Pokemon(en_name='Pikachu', jp_name='ピカチュウ'),
        Pokemon(en_name='Bulbasaur', jp_name='フシギダネ'),
    ]

    class PokemonDict(BaseModel):
        root: Dict[str, Pokemon]
        model_config = ConfigDict(from_attributes=True)

        @root_validator(pre=True)
        @classmethod
        def populate_root(cls, values):
            return {'root': values}

        @model_serializer(mode='wrap')
        def _serialize(self, handler, info):
            data = handler(self)
            if info.mode == 'json':
                return data['root']
            else:
                return data

        @classmethod
        def model_modify_json_schema(cls, json_schema):
            return json_schema['properties']['root']

    pokemons = deprecated_from_orm(PokemonDict, {'pika': pika, 'bulbi': bulbi})
    assert pokemons.root == {
        'pika': Pokemon(en_name='Pikachu', jp_name='ピカチュウ'),
        'bulbi': Pokemon(en_name='Bulbasaur', jp_name='フシギダネ'),
    }


def test_from_attributes():
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
        model_config = ConfigDict(from_attributes=True)
        name: str
        species: str

    class Person(BaseModel):
        model_config = ConfigDict(from_attributes=True)
        name: str
        age: float = None
        pets: List[Pet]

    bones = PetCls(name='Bones', species='dog')
    orion = PetCls(name='Orion', species='cat')
    anna = PersonCls(name='Anna', age=20, pets=[bones, orion])

    anna_model = deprecated_from_orm(Person, anna)

    assert anna_model.model_dump() == {
        'name': 'Anna',
        'pets': [{'name': 'Bones', 'species': 'dog'}, {'name': 'Orion', 'species': 'cat'}],
        'age': 20.0,
    }


def test_not_from_attributes():
    class Pet(BaseModel):
        name: str
        species: str

    with pytest.raises(PydanticUserError):
        deprecated_from_orm(Pet, None)


def test_object_with_getattr():
    class FooGetAttr:
        def __getattr__(self, key: str):
            if key == 'foo':
                return 'Foo'
            else:
                raise AttributeError

    class Model(BaseModel):
        model_config = ConfigDict(from_attributes=True)
        foo: str
        bar: int = 1

    class ModelInvalid(BaseModel):
        model_config = ConfigDict(from_attributes=True)
        foo: str
        bar: int

    foo = FooGetAttr()
    model = deprecated_from_orm(Model, foo)
    assert model.foo == 'Foo'
    assert model.bar == 1
    assert model.model_dump(exclude_unset=True) == {'foo': 'Foo'}
    with pytest.raises(ValidationError):
        deprecated_from_orm(ModelInvalid, foo)


def test_properties():
    class XyProperty:
        x = 4

        @property
        def y(self):
            return '5'

    class Model(BaseModel):
        model_config = ConfigDict(from_attributes=True)
        x: int
        y: int

    model = deprecated_from_orm(Model, XyProperty())
    assert model.x == 4
    assert model.y == 5


@pytest.mark.xfail(reason='working on V2')
def test_extra_allow():
    class TestCls:
        x = 1
        y = 2

    class Model(BaseModel):
        model_config = ConfigDict(from_attributes=True, extra='allow')
        x: int

    model = deprecated_from_orm(Model, TestCls())
    assert model.model_dump() == {'x': 1}


@pytest.mark.xfail(reason='working on V2')
def test_extra_forbid():
    class TestCls:
        x = 1
        y = 2

    class Model(BaseModel):
        model_config = ConfigDict(from_attributes=True, extra='forbid')
        x: int

    model = deprecated_from_orm(Model, TestCls())
    assert model.model_dump() == {'x': 1}


@pytest.mark.xfail(reason='working on V2')
def test_root_validator():
    validator_value = None

    class TestCls:
        x = 1
        y = 2

    class Model(BaseModel):
        model_config = ConfigDict(from_attributes=True)
        x: int
        y: int
        z: int

        @root_validator(pre=True)
        def change_input_data(cls, value):
            nonlocal validator_value
            validator_value = value
            return {**value, 'z': value['x'] + value['y']}

    model = deprecated_from_orm(Model, TestCls())
    assert model.model_dump() == {'x': 1, 'y': 2, 'z': 3}
    # assert isinstance(validator_value, GetterDict)
    assert validator_value == {'x': 1, 'y': 2}


@pytest.mark.xfail(reason='working on V2')
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
            from_attributes = True
            getter_dict = custom_getter_dict

    model = deprecated_from_orm(Model, TestCls())
    assert model.model_dump() == {'x': 42, 'y': 24}


@pytest.mark.xfail(reason='working on V2')
def test_recursive_parsing():
    class Getter:  # GetterDict
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
            from_attributes = True
            getter_dict = Getter

    class ModelA(Model):
        a: int

    class ModelB(Model):
        b: ModelA

    # test recursive parsing with object attributes
    dct = dict(bb=SimpleNamespace(aa=1))
    assert deprecated_from_orm(ModelB, dct) == ModelB(b=ModelA(a=1))

    # test recursive parsing with dict keys
    obj = dict(bb=dict(aa=1))
    assert deprecated_from_orm(ModelB, obj) == ModelB(b=ModelA(a=1))


def test_nested_orm():
    class User(BaseModel):
        model_config = ConfigDict(from_attributes=True)
        first_name: str
        last_name: str

    class State(BaseModel):
        model_config = ConfigDict(from_attributes=True)
        user: User

    # Pass an "orm instance"
    deprecated_from_orm(State, SimpleNamespace(user=SimpleNamespace(first_name='John', last_name='Appleseed')))

    # Pass dictionary data directly
    State(**{'user': {'first_name': 'John', 'last_name': 'Appleseed'}})


def test_parse_raw_pass():
    class Model(BaseModel):
        x: int
        y: int

    with pytest.warns(DeprecationWarning, match='The `parse_raw` method is deprecated'):
        model = Model.parse_raw('{"x": 1, "y": 2}')
    assert model.model_dump() == {'x': 1, 'y': 2}


@pytest.mark.skipif(platform.python_implementation() == 'PyPy', reason='Different error str on PyPy')
def test_parse_raw_pass_fail():
    class Model(BaseModel):
        x: int
        y: int

    with pytest.warns(DeprecationWarning, match='The `parse_raw` method is deprecated'):
        with pytest.raises(ValidationError, match='1 validation error for Model') as exc_info:
            Model.parse_raw('invalid')

    # insert_assert(exc_info.value.errors())
    assert exc_info.value.errors() == [
        {
            'type': 'value_error.jsondecode',
            'loc': ('__root__',),
            'msg': 'Expecting value: line 1 column 1 (char 0)',
            'input': 'invalid',
        }
    ]
