import platform
import re
import sys
from datetime import timedelta
from pathlib import Path
from types import SimpleNamespace
from typing import Any, Dict, List, Type

import pytest
from typing_extensions import Literal

from pydantic import BaseModel, ConfigDict, Field, PydanticUserError, ValidationError, root_validator
from pydantic.config import Extra
from pydantic.deprecated.decorator import validate_arguments
from pydantic.deprecated.json import custom_pydantic_encoder, pydantic_encoder, timedelta_isoformat
from pydantic.deprecated.parse import load_file, load_str_bytes
from pydantic.deprecated.tools import parse_obj_as, schema_json_of, schema_of
from pydantic.functional_serializers import model_serializer

if sys.version_info < (3, 11):
    from typing_extensions import get_overloads
else:
    from typing import get_overloads


def deprecated_from_orm(model_type: Type[BaseModel], obj: Any) -> Any:
    with pytest.warns(
        DeprecationWarning,
        match=re.escape(
            'The `from_orm` method is deprecated; set `model_config["from_attributes"]=True` '
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

    with pytest.warns(DeprecationWarning, match='Pydantic V1 style `@root_validator` validators are deprecated.'):

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

    with pytest.warns(DeprecationWarning, match='Pydantic V1 style `@root_validator` validators are deprecated.'):

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


@pytest.mark.parametrize('extra', ['ignore', 'forbid', 'allow'])
def test_extra_allow_from_orm(extra: Literal['ignore', 'forbid', 'allow']):
    class TestCls:
        x = 1
        y = 2

    class Model(BaseModel):
        model_config = ConfigDict(from_attributes=True, extra=extra)
        x: int

    model = deprecated_from_orm(Model, TestCls())
    assert model.x == 1
    assert not hasattr(model, 'y')


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

    # insert_assert(exc_info.value.errors(include_url=False))
    assert exc_info.value.errors(include_url=False) == [
        {
            'type': 'value_error.jsondecode',
            'loc': ('__root__',),
            'msg': 'Expecting value: line 1 column 1 (char 0)',
            'input': 'invalid',
        }
    ]


def test_fields_set():
    class Model(BaseModel):
        x: int
        y: int = 2

    m = Model(x=1)
    assert m.model_fields_set == {'x'}
    match = '^The `__fields_set__` attribute is deprecated, use `model_fields_set` instead.$'
    with pytest.warns(DeprecationWarning, match=match):
        assert m.__fields_set__ == {'x'}


@pytest.mark.parametrize('attribute,value', [('allow', 'allow'), ('ignore', 'ignore'), ('forbid', 'forbid')])
def test_extra_used_as_enum(
    attribute: str,
    value: str,
) -> None:
    with pytest.raises(
        DeprecationWarning,
        match=re.escape("`pydantic.config.Extra` is deprecated, use literal values instead (e.g. `extra='allow'`)"),
    ):
        assert getattr(Extra, attribute) == value


def test_field_min_items_deprecation():
    m = '`min_items` is deprecated and will be removed. use `min_length` instead'
    with pytest.warns(DeprecationWarning, match=m):

        class Model(BaseModel):
            x: List[int] = Field(None, min_items=1)

    with pytest.raises(ValidationError) as exc_info:
        Model(x=[])
    assert exc_info.value.errors(include_url=False) == [
        {
            'type': 'too_short',
            'loc': ('x',),
            'msg': 'List should have at least 1 item after validation, not 0',
            'input': [],
            'ctx': {'field_type': 'List', 'min_length': 1, 'actual_length': 0},
        }
    ]


def test_field_min_items_with_min_length():
    m = '`min_items` is deprecated and will be removed. use `min_length` instead'
    with pytest.warns(DeprecationWarning, match=m):

        class Model(BaseModel):
            x: List[int] = Field(None, min_items=1, min_length=2)

    with pytest.raises(ValidationError) as exc_info:
        Model(x=[1])
    assert exc_info.value.errors(include_url=False) == [
        {
            'type': 'too_short',
            'loc': ('x',),
            'msg': 'List should have at least 2 items after validation, not 1',
            'input': [1],
            'ctx': {'field_type': 'List', 'min_length': 2, 'actual_length': 1},
        }
    ]


def test_field_max_items():
    m = '`max_items` is deprecated and will be removed. use `max_length` instead'
    with pytest.warns(DeprecationWarning, match=m):

        class Model(BaseModel):
            x: List[int] = Field(None, max_items=1)

    with pytest.raises(ValidationError) as exc_info:
        Model(x=[1, 2])
    assert exc_info.value.errors(include_url=False) == [
        {
            'type': 'too_long',
            'loc': ('x',),
            'msg': 'List should have at most 1 item after validation, not 2',
            'input': [1, 2],
            'ctx': {'field_type': 'List', 'max_length': 1, 'actual_length': 2},
        }
    ]


def test_field_max_items_with_max_length():
    m = '`max_items` is deprecated and will be removed. use `max_length` instead'
    with pytest.warns(DeprecationWarning, match=m):

        class Model(BaseModel):
            x: List[int] = Field(None, max_items=1, max_length=2)

    with pytest.raises(ValidationError) as exc_info:
        Model(x=[1, 2, 3])
    assert exc_info.value.errors(include_url=False) == [
        {
            'type': 'too_long',
            'loc': ('x',),
            'msg': 'List should have at most 2 items after validation, not 3',
            'input': [1, 2, 3],
            'ctx': {'field_type': 'List', 'max_length': 2, 'actual_length': 3},
        }
    ]


def test_field_const():
    with pytest.raises(PydanticUserError, match='`const` is removed. use `Literal` instead'):

        class Model(BaseModel):
            x: str = Field('test', const=True)


def test_unique_items_items():
    with pytest.raises(PydanticUserError, match='`unique_items` is removed. use `Set` instead'):

        class Model(BaseModel):
            x: List[int] = Field(None, unique_items=True)


def test_allow_mutation():
    m = '`allow_mutation` is deprecated and will be removed. use `frozen` instead'
    with pytest.warns(DeprecationWarning, match=m):

        class Model(BaseModel):
            model_config = ConfigDict(validate_assignment=True)
            x: int = Field(allow_mutation=False)

    m = Model(x=1)
    assert m.x == 1
    with pytest.raises(ValidationError) as exc_info:
        m.x = 2
    assert exc_info.value.errors(include_url=False) == [
        {'input': 2, 'loc': ('x',), 'msg': 'Field is frozen', 'type': 'frozen_field'}
    ]


def test_field_regex():
    with pytest.raises(PydanticUserError, match='`regex` is removed. use `Pattern` instead'):

        class Model(BaseModel):
            x: str = Field('test', regex=r'^test$')


def test_field_extra_arguments():
    m = 'Extra keyword arguments on `Field` is deprecated and will be removed. use `json_schema_extra` instead'
    with pytest.warns(DeprecationWarning, match=m):

        class Model(BaseModel):
            x: str = Field('test', test='test')

    assert Model.model_json_schema(by_alias=True)['properties'] == {
        'x': {'default': 'test', 'test': 'test', 'title': 'X', 'type': 'string'}
    }


class SimpleModel(BaseModel):
    x: int


def test_dict():
    m = SimpleModel(x=1)
    with pytest.warns(DeprecationWarning, match=r'^The `dict` method is deprecated; use `model_dump` instead\.$'):
        assert m.dict() == {'x': 1}


def test_json():
    m = SimpleModel(x=1)
    with pytest.warns(DeprecationWarning, match=r'^The `json` method is deprecated; use `model_dump_json` instead\.$'):
        assert m.json() == '{"x":1}'

    with pytest.warns(DeprecationWarning):
        with pytest.raises(TypeError, match='The `encoder` argument is no longer supported'):
            m.json(encoder=1)
        with pytest.raises(TypeError, match='The `models_as_dict` argument is no longer supported'):
            m.json(models_as_dict=True)
        with pytest.raises(TypeError, match='`dumps_kwargs` keyword arguments are no longer supported.'):
            m.json(foo=4)


def test_parse_obj():
    with pytest.warns(DeprecationWarning, match='^The `parse_obj` method is deprecated; use `model_validate` instead.'):
        m = SimpleModel.parse_obj({'x': 1})

    assert m.model_dump() == {'x': 1}


def test_parse_file(tmp_path):
    path = tmp_path / 'test.json'
    path.write_text('{"x": 12}')
    with pytest.warns(DeprecationWarning, match='^The `parse_file` method is deprecated; load the data from file,'):
        assert SimpleModel.parse_file(str(path)).model_dump() == {'x': 12}


def test_construct():
    with pytest.warns(DeprecationWarning, match='The `construct` method is deprecated; use `model_construct` instead.'):
        m = SimpleModel.construct(x='not an int')

    assert m.x == 'not an int'


def test_json_schema():
    m = SimpleModel(x=1)
    with pytest.warns(DeprecationWarning, match='^The `schema` method is deprecated; use `model_json_schema` instead.'):
        assert m.schema() == {
            'title': 'SimpleModel',
            'type': 'object',
            'properties': {'x': {'title': 'X', 'type': 'integer'}},
            'required': ['x'],
        }


def test_validate():
    with pytest.warns(DeprecationWarning, match='^The `validate` method is deprecated; use `model_validate` instead.'):
        m = SimpleModel.validate({'x': 1})

    assert m.model_dump() == {'x': 1}


def test_update_forward_refs():
    with pytest.warns(DeprecationWarning, match='^The `update_forward_refs` method is deprecated;'):
        SimpleModel.update_forward_refs()


def test_copy_and_set_values():
    m = SimpleModel(x=1)
    with pytest.warns(DeprecationWarning, match='^The private method  `_copy_and_set_values` will be removed and '):
        m2 = m._copy_and_set_values(values={'x': 2}, fields_set={'x'}, deep=False)

    assert m2.x == 2


def test_get_value():
    m = SimpleModel(x=1)
    with pytest.warns(DeprecationWarning, match='^The private method  `_get_value` will be removed and '):
        v = m._get_value(
            [1, 2, 3],
            to_dict=False,
            by_alias=False,
            include=None,
            exclude=None,
            exclude_unset=False,
            exclude_defaults=False,
            exclude_none=False,
        )
    assert v == [1, 2, 3]


def test_deprecated_module(tmp_path: Path) -> None:
    class Model(BaseModel):
        x: int

    assert hasattr(parse_obj_as, '__deprecated__')
    with pytest.warns(
        DeprecationWarning, match='parse_obj_as is deprecated. Use pydantic.TypeAdapter.validate_python instead.'
    ):
        parse_obj_as(Model, {'x': 1})

    assert hasattr(schema_json_of, '__deprecated__')
    with pytest.warns(
        DeprecationWarning, match='schema_json_of is deprecated. Use pydantic.TypeAdapter.json_schema instead.'
    ):
        schema_json_of(Model)

    assert hasattr(schema_of, '__deprecated__')
    with pytest.warns(
        DeprecationWarning, match='schema_of is deprecated. Use pydantic.TypeAdapter.json_schema instead.'
    ):
        schema_of(Model)

    assert hasattr(load_str_bytes, '__deprecated__')
    with pytest.warns(DeprecationWarning, match='load_str_bytes is deprecated.'):
        load_str_bytes('{"x": 1}')

    assert hasattr(load_file, '__deprecated__')
    file = tmp_path / 'main.py'
    file.write_text('{"x": 1}')
    with pytest.warns(DeprecationWarning, match='load_file is deprecated.'):
        load_file(file)

    assert hasattr(pydantic_encoder, '__deprecated__')
    with pytest.warns(DeprecationWarning, match='pydantic_encoder is deprecated, use BaseModel.model_dump instead.'):
        pydantic_encoder(Model(x=1))

    assert hasattr(custom_pydantic_encoder, '__deprecated__')
    with pytest.warns(
        DeprecationWarning, match='custom_pydantic_encoder is deprecated, use BaseModel.model_dump instead.'
    ):
        custom_pydantic_encoder({int: lambda x: str(x)}, Model(x=1))

    assert hasattr(timedelta_isoformat, '__deprecated__')
    with pytest.warns(DeprecationWarning, match='timedelta_isoformat is deprecated.'):
        timedelta_isoformat(timedelta(seconds=1))

    assert all(hasattr(func, '__deprecated__') for func in get_overloads(validate_arguments))
    with pytest.warns(
        DeprecationWarning, match='The `validate_arguments` method is deprecated; use `validate_call` instead.'
    ):

        def test(a: int, b: int):
            pass

        validate_arguments()(test)
