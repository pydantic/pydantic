import re
from typing import Any

import pytest

import pydantic
from pydantic import BaseModel, ConfigDict, Field
from pydantic.json_schema import model_json_schema


def make_title(name: str):
    def _capitalize(v: str):
        return v[0].upper() + v[1:]

    return re.sub(r'(?<=[a-z])([A-Z])', r' \1', _capitalize(name))


@pytest.mark.parametrize(
    'class_title_generator',
    (lambda m: m.lower(), lambda m: m * 2, lambda m: 'My Title', make_title),
)
def test_class_title_generator(class_title_generator):
    class Model(BaseModel):
        model_config = ConfigDict(class_title_generator=class_title_generator)

    assert Model.model_json_schema() == {
        'properties': {},
        'title': class_title_generator(Model.__name__),
        'type': 'object',
    }


@pytest.mark.parametrize(
    'class_title_generator', (lambda m: m.lower(), lambda m: m * 2, lambda m: 'My Title', make_title)
)
def test_class_title_generator_in_submodel(class_title_generator):
    class SubModel(BaseModel):
        model_config = ConfigDict(class_title_generator=class_title_generator)

    class Model(BaseModel):
        sub: SubModel

    assert Model.model_json_schema() == {
        '$defs': {'SubModel': {'properties': {}, 'title': class_title_generator(SubModel.__name__), 'type': 'object'}},
        'properties': {'sub': {'$ref': '#/$defs/SubModel'}},
        'required': ['sub'],
        'title': 'Model',
        'type': 'object',
    }


@pytest.mark.parametrize('invalid_return_value', (1, 2, 3, tuple(), list(), object()))
def test_class_title_generator_returns_invalid_type(invalid_return_value):
    with pytest.raises(TypeError, match='class_title_generator .* must return str, not .*'):

        class Model(BaseModel):
            model_config = ConfigDict(class_title_generator=lambda m: invalid_return_value)

    with pytest.raises(TypeError, match='class_title_generator .* must return str, not .*'):

        @pydantic.dataclasses.dataclass(config=ConfigDict(class_title_generator=lambda m: invalid_return_value))
        class MyDataclass:
            pass


@pytest.mark.parametrize('invalid_return_value', (1, 2, 3, tuple(), list(), object()))
def test_config_field_title_generator_returns_invalid_type(invalid_return_value):
    with pytest.raises(TypeError, match='field_title_generator .* must return str, not .*'):

        class Model(BaseModel):
            model_config = ConfigDict(field_title_generator=lambda m: invalid_return_value)

            field_a: str

    with pytest.raises(TypeError, match='field_title_generator .* must return str, not .*'):

        @pydantic.dataclasses.dataclass(config=ConfigDict(field_title_generator=lambda m: invalid_return_value))
        class MyDataclass:
            field_a: str


@pytest.mark.parametrize('invalid_return_value', (1, 2, 3, tuple(), list(), object()))
def test_field_title_generator_returns_invalid_type(invalid_return_value):
    with pytest.raises(TypeError, match='field_title_generator .* must return str, not .*'):

        class Model(BaseModel):
            field_a: Any = Field(field_title_generator=lambda f: invalid_return_value)

        Model(field_a=invalid_return_value).model_json_schema()

    with pytest.raises(TypeError, match='field_title_generator .* must return str, not .*'):

        @pydantic.dataclasses.dataclass
        class MyDataclass:
            field_a: Any = Field(field_title_generator=lambda f: invalid_return_value)

        model_json_schema(MyDataclass)


@pytest.mark.parametrize('class_title_generator', (lambda m: m.lower(), lambda m: 'dc', make_title))
def test_dataclass_class_title_generator(class_title_generator):
    @pydantic.dataclasses.dataclass(config=ConfigDict(class_title_generator=class_title_generator))
    class MyDataclass:
        field_a: int

    assert model_json_schema(MyDataclass) == {
        'properties': {'field_a': {'title': 'Field A', 'type': 'integer'}},
        'required': ['field_a'],
        'title': class_title_generator(MyDataclass.__name__),
        'type': 'object',
    }


@pytest.mark.parametrize('field_title_generator', (lambda f: f.upper(), lambda f: f.replace('_', ''), make_title))
def test_dataclass_field_title_generator(field_title_generator):
    @pydantic.dataclasses.dataclass(config=ConfigDict(field_title_generator=field_title_generator))
    class MyDataclass:
        field_a: str
        field_b: int
        field___c: bool

    assert model_json_schema(MyDataclass) == {
        'properties': {
            'field_a': {'title': field_title_generator('field_a'), 'type': 'string'},
            'field_b': {'title': field_title_generator('field_b'), 'type': 'integer'},
            'field___c': {'title': field_title_generator('field___c'), 'type': 'boolean'},
        },
        'required': ['field_a', 'field_b', 'field___c'],
        'title': 'MyDataclass',
        'type': 'object',
    }


@pytest.mark.parametrize('field_title_generator', (lambda f: f.upper(), lambda f: f.replace('_', ''), make_title))
def test_model_config_field_title_generator(field_title_generator):
    class Model(BaseModel):
        model_config = ConfigDict(field_title_generator=field_title_generator)

        field_a: str
        field_b: int
        field___c: bool

    assert Model.model_json_schema() == {
        'properties': {
            'field_a': {'title': field_title_generator('field_a'), 'type': 'string'},
            'field_b': {'title': field_title_generator('field_b'), 'type': 'integer'},
            'field___c': {'title': field_title_generator('field___c'), 'type': 'boolean'},
        },
        'required': ['field_a', 'field_b', 'field___c'],
        'title': 'Model',
        'type': 'object',
    }


def test_field_title_overrides_config_field_title_generator_model():
    class Model(BaseModel):
        model_config = ConfigDict(field_title_generator=lambda f: f.replace('_', ''))

        field_a: str = Field(title='Field A', title_priority=2)
        field_b: int = Field(title='Field B', title_priority=1)
        field___c: bool = Field(title='Field C', title_priority=10)

    assert Model.model_json_schema() == {
        'properties': {
            'field_a': {'title': 'Field A', 'type': 'string'},
            'field_b': {'title': 'fieldb', 'type': 'integer'},
            'field___c': {'title': 'Field C', 'type': 'boolean'},
        },
        'required': ['field_a', 'field_b', 'field___c'],
        'title': 'Model',
        'type': 'object',
    }


def test_field_title_overrides_config_field_title_generator_dataclass():
    @pydantic.dataclasses.dataclass(config=ConfigDict(field_title_generator=lambda f: f.replace('_', '')))
    class MyDataclass:
        field_a: str = Field(title='MyFieldA', title_priority=2)
        field_b: int = Field(title='MyFieldB', title_priority=1)
        field___c: bool = Field(title='MyFieldC', title_priority=10)

    assert model_json_schema(MyDataclass) == {
        'properties': {
            'field_a': {'title': 'MyFieldA', 'type': 'string'},
            'field_b': {'title': 'fieldb', 'type': 'integer'},
            'field___c': {'title': 'MyFieldC', 'type': 'boolean'},
        },
        'required': ['field_a', 'field_b', 'field___c'],
        'title': 'MyDataclass',
        'type': 'object',
    }


@pytest.mark.parametrize(
    'field_level_title_generator,config_level_title_generator',
    ((lambda f: f.lower(), lambda f: f.upper()), (lambda f: f, make_title)),
)
def test_field_level_field_title_generator_precedence_over_config_level(
    field_level_title_generator, config_level_title_generator
):
    class MyModel(BaseModel):
        model_config = ConfigDict(field_title_generator=field_level_title_generator)
        field_a: str = Field(field_title_generator=field_level_title_generator)

    assert MyModel.model_json_schema() == {
        'properties': {'field_a': {'title': field_level_title_generator('field_a'), 'type': 'string'}},
        'required': ['field_a'],
        'title': 'MyModel',
        'type': 'object',
    }

    @pydantic.dataclasses.dataclass(config=ConfigDict(field_title_generator=field_level_title_generator))
    class MyDataclass:
        field_a: str = Field(field_title_generator=field_level_title_generator)

    assert model_json_schema(MyDataclass) == {
        'properties': {'field_a': {'title': field_level_title_generator('field_a'), 'type': 'string'}},
        'required': ['field_a'],
        'title': 'MyDataclass',
        'type': 'object',
    }


def test_field_title_precedence_over_generators():
    class Model(BaseModel):
        model_config = ConfigDict(field_title_generator=lambda f: f.upper())

        field_a: str = Field(title='MyTitle', field_title_generator=lambda f: f.upper())

    assert Model.model_json_schema() == {
        'properties': {'field_a': {'title': 'MyTitle', 'type': 'string'}},
        'required': ['field_a'],
        'title': 'Model',
        'type': 'object',
    }

    @pydantic.dataclasses.dataclass(config=ConfigDict(field_title_generator=lambda f: f.upper()))
    class MyDataclass:
        field_a: str = Field(title='MyTitle', field_title_generator=lambda f: f.upper())

    assert model_json_schema(MyDataclass) == {
        'properties': {'field_a': {'title': 'MyTitle', 'type': 'string'}},
        'required': ['field_a'],
        'title': 'MyDataclass',
        'type': 'object',
    }


def test_class_title_precedence_over_generator():
    class Model(BaseModel):
        model_config = ConfigDict(title='MyTitle', class_title_generator=lambda c: c.upper())

    assert Model.model_json_schema() == {
        'properties': {},
        'title': 'MyTitle',
        'type': 'object',
    }

    @pydantic.dataclasses.dataclass(config=ConfigDict(title='MyTitle', class_title_generator=lambda c: c.upper()))
    class MyDataclass:
        pass

    assert model_json_schema(MyDataclass) == {
        'properties': {},
        'title': 'MyTitle',
        'type': 'object',
    }
