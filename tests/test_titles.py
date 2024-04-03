import pytest

from pydantic import BaseModel, ConfigDict, Field
from pydantic.dataclasses import dataclass
from pydantic.json_schema import model_json_schema


@pytest.mark.parametrize(
    'model_title_generator',
    (lambda m: m.lower(), lambda m: m * 2, lambda m: 'My Title'),
)
def test_model_title_generator(model_title_generator):
    class Model(BaseModel):
        model_config = ConfigDict(model_title_generator=model_title_generator)

    assert Model.model_json_schema() == {
        'properties': {},
        'title': model_title_generator(Model.__name__),
        'type': 'object',
    }


@pytest.mark.parametrize('model_title_generator', (lambda m: m.lower(), lambda m: m * 2, lambda m: 'My Title'))
def test_submodel_title_generator(model_title_generator):
    class SubModel(BaseModel):
        model_config = ConfigDict(model_title_generator=model_title_generator)

    class Model(BaseModel):
        sub: SubModel

    assert Model.model_json_schema() == {
        '$defs': {'SubModel': {'properties': {}, 'title': model_title_generator(SubModel.__name__), 'type': 'object'}},
        'properties': {'sub': {'$ref': '#/$defs/SubModel'}},
        'required': ['sub'],
        'title': 'Model',
        'type': 'object',
    }


@pytest.mark.parametrize('invalid_return_value', (1, 2, 3, tuple(), list(), object()))
def test_model_title_generator_returns_invalid_type(invalid_return_value):
    with pytest.raises(TypeError, match='model_title_generator .* must return str, not .*'):

        class Model(BaseModel):
            model_config = ConfigDict(model_title_generator=lambda m: invalid_return_value)


@pytest.mark.parametrize('model_title_generator', (lambda m: m.lower(),))
def test_dataclass_model_title_generator(model_title_generator):
    @dataclass(config=ConfigDict(model_title_generator=model_title_generator))
    class MyDataclass:
        field_a: int

    assert model_json_schema(MyDataclass) == {}


def test_field_title_generator():
    class Model(BaseModel):
        model_config = ConfigDict(field_title_generator=lambda f: f.replace('_', ''))

        field_a: str
        field_b: int
        field___c: bool

    assert Model.model_json_schema() == {
        'properties': {
            'field_a': {'title': 'fielda', 'type': 'string'},
            'field_b': {'title': 'fieldb', 'type': 'integer'},
            'field___c': {'title': 'fieldc', 'type': 'boolean'},
        },
        'required': ['field_a', 'field_b', 'field___c'],
        'title': 'Model',
        'type': 'object',
    }


def test_field_title_overrides_field_title_generator():
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
