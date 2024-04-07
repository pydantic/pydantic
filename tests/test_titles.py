import re
from typing import Annotated, Any, Callable, List

import pytest

import pydantic
from pydantic import BaseModel, ConfigDict, Field, TypeAdapter, computed_field
from pydantic.alias_generators import to_camel, to_pascal, to_snake
from pydantic.json_schema import model_json_schema

from .test_types_typeddict import fixture_typed_dict_all  # noqa


def make_title(name: str):
    def _capitalize(v: str):
        return v[0].upper() + v[1:]

    return re.sub(r'(?<=[a-z])([A-Z])', r' \1', _capitalize(name))


TITLE_GENERATORS: List[Callable[[str], str]] = [
    lambda t: t.lower(),
    lambda t: t * 2,
    lambda t: 'My Title',
    make_title,
    to_camel,
    to_snake,
    to_pascal,
]


@pytest.mark.parametrize('class_title_generator', TITLE_GENERATORS)
def test_model_class_title_generator(class_title_generator):
    class Model(BaseModel):
        model_config = ConfigDict(class_title_generator=class_title_generator)

    assert Model.model_json_schema() == {
        'properties': {},
        'title': class_title_generator(Model.__name__),
        'type': 'object',
    }


@pytest.mark.parametrize('class_title_generator', TITLE_GENERATORS)
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


@pytest.mark.parametrize('field_title_generator', TITLE_GENERATORS)
def test_field_title_generator_in_model_fields(field_title_generator):
    class Model(BaseModel):
        field_a: str = Field(field_title_generator=field_title_generator)
        field_b: int = Field(field_title_generator=field_title_generator)

        @computed_field(field_title_generator=field_title_generator)
        def field_c(self) -> str:
            return self.field_a

    assert Model.model_json_schema(mode='serialization') == {
        'properties': {
            'field_a': {'title': field_title_generator('field_a'), 'type': 'string'},
            'field_b': {'title': field_title_generator('field_b'), 'type': 'integer'},
            'field_c': {'readOnly': True, 'title': field_title_generator('field_c'), 'type': 'string'},
        },
        'required': ['field_a', 'field_b', 'field_c'],
        'title': 'Model',
        'type': 'object',
    }


@pytest.mark.parametrize('field_title_generator', TITLE_GENERATORS)
def test_model_config_field_title_generator(field_title_generator):
    class Model(BaseModel):
        model_config = ConfigDict(field_title_generator=field_title_generator)

        field_a: str
        field_b: int
        field___c: bool

        @computed_field
        def field_d(self) -> str:
            return self.field_a

    assert Model.model_json_schema(mode='serialization') == {
        'properties': {
            'field_a': {'title': field_title_generator('field_a'), 'type': 'string'},
            'field_b': {'title': field_title_generator('field_b'), 'type': 'integer'},
            'field___c': {'title': field_title_generator('field___c'), 'type': 'boolean'},
            'field_d': {'readOnly': True, 'title': field_title_generator('field_d'), 'type': 'string'},
        },
        'required': ['field_a', 'field_b', 'field___c', 'field_d'],
        'title': 'Model',
        'type': 'object',
    }


def test_field_title_priority_over_config_field_title_generator():
    class Model(BaseModel):
        model_config = ConfigDict(field_title_generator=lambda f: f.replace('_', ''))

        field_a: str = Field(title='Field A', title_priority=2)
        field_b: int = Field(title='Field B', title_priority=1)
        field___c: bool = Field(title='Field C', title_priority=10)

        @computed_field(title='Field D', title_priority=2)
        def field_d(self) -> str:
            return self.field_a

    assert Model.model_json_schema(mode='serialization') == {
        'properties': {
            'field_a': {'title': 'Field A', 'type': 'string'},
            'field_b': {'title': 'fieldb', 'type': 'integer'},
            'field___c': {'title': 'Field C', 'type': 'boolean'},
            'field_d': {'readOnly': True, 'title': 'Field D', 'type': 'string'},
        },
        'required': ['field_a', 'field_b', 'field___c', 'field_d'],
        'title': 'Model',
        'type': 'object',
    }


def test_field_title_priority_over_field_title_generator():
    class Model(BaseModel):
        model_config = ConfigDict()

        field_a: str = Field(title='Field A', title_priority=2, field_title_generator=lambda f: f.replace('_', ''))
        field_b: int = Field(title='Field B', title_priority=1, field_title_generator=lambda f: f.replace('_', ''))
        field___c: bool = Field(title='Field C', title_priority=10, field_title_generator=lambda f: f.replace('_', ''))

        @computed_field(title='Field D', title_priority=1, field_title_generator=lambda f: f.replace('_', ''))
        def field_d(self) -> str:
            return self.field_a

    assert Model.model_json_schema(mode='serialization') == {
        'properties': {
            'field_a': {'title': 'Field A', 'type': 'string'},
            'field_b': {'title': 'fieldb', 'type': 'integer'},
            'field___c': {'title': 'Field C', 'type': 'boolean'},
            'field_d': {'readOnly': True, 'title': 'fieldd', 'type': 'string'},
        },
        'required': ['field_a', 'field_b', 'field___c', 'field_d'],
        'title': 'Model',
        'type': 'object',
    }


@pytest.mark.parametrize('class_title_generator', TITLE_GENERATORS)
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


@pytest.mark.parametrize('field_title_generator', TITLE_GENERATORS)
def test_field_title_generator_in_dataclass_fields(field_title_generator):
    @pydantic.dataclasses.dataclass
    class MyDataclass:
        field_a: str = Field(field_title_generator=field_title_generator)
        field_b: int = Field(field_title_generator=field_title_generator)

    assert model_json_schema(MyDataclass) == {
        'properties': {
            'field_a': {'title': field_title_generator('field_a'), 'type': 'string'},
            'field_b': {'title': field_title_generator('field_b'), 'type': 'integer'},
        },
        'required': ['field_a', 'field_b'],
        'title': 'MyDataclass',
        'type': 'object',
    }


@pytest.mark.parametrize('field_title_generator', TITLE_GENERATORS)
def test_dataclass_config_field_title_generator(field_title_generator):
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


@pytest.mark.parametrize('class_title_generator', TITLE_GENERATORS)
def test_typeddict_class_title_generator(class_title_generator, TypedDictAll):
    class MyTypedDict(TypedDictAll):
        __pydantic_config__ = ConfigDict(class_title_generator=class_title_generator)
        pass

    assert TypeAdapter(MyTypedDict).json_schema() == {
        'properties': {},
        'title': class_title_generator(MyTypedDict.__name__),
        'type': 'object',
    }


@pytest.mark.parametrize('field_title_generator', TITLE_GENERATORS)
def test_field_title_generator_in_typeddict_fields(field_title_generator, TypedDictAll):
    class MyTypedDict(TypedDictAll):
        field_a: Annotated[str, Field(field_title_generator=field_title_generator)]
        field_b: Annotated[int, Field(field_title_generator=field_title_generator)]

    assert TypeAdapter(MyTypedDict).json_schema() == {
        'properties': {
            'field_a': {'title': field_title_generator('field_a'), 'type': 'string'},
            'field_b': {'title': field_title_generator('field_b'), 'type': 'integer'},
        },
        'required': ['field_a', 'field_b'],
        'title': 'MyTypedDict',
        'type': 'object',
    }


@pytest.mark.parametrize('field_title_generator', TITLE_GENERATORS)
def test_typeddict_config_field_title_generator(field_title_generator, TypedDictAll):
    class MyTypedDict(TypedDictAll):
        __pydantic_config__ = ConfigDict(field_title_generator=field_title_generator)
        field_a: str
        field_b: int
        field___c: bool

    assert TypeAdapter(MyTypedDict).json_schema() == {
        'properties': {
            'field_a': {'title': field_title_generator('field_a'), 'type': 'string'},
            'field_b': {'title': field_title_generator('field_b'), 'type': 'integer'},
            'field___c': {'title': field_title_generator('field___c'), 'type': 'boolean'},
        },
        'required': ['field_a', 'field_b', 'field___c'],
        'title': 'MyTypedDict',
        'type': 'object',
    }


@pytest.mark.parametrize(
    'field_level_title_generator,config_level_title_generator',
    ((lambda f: f.lower(), lambda f: f.upper()), (lambda f: f, make_title)),
)
def test_field_level_field_title_generator_precedence_over_config_level(
    field_level_title_generator, config_level_title_generator, TypedDictAll
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

    class MyTypedDict(TypedDictAll):
        __pydantic_config__ = ConfigDict(field_title_generator=field_level_title_generator)
        field_a: Annotated[str, Field(field_title_generator=field_level_title_generator)]

    assert TypeAdapter(MyTypedDict).json_schema() == {
        'properties': {'field_a': {'title': field_level_title_generator('field_a'), 'type': 'string'}},
        'required': ['field_a'],
        'title': 'MyTypedDict',
        'type': 'object',
    }


def test_field_title_precedence_over_generators(TypedDictAll):
    class Model(BaseModel):
        model_config = ConfigDict(field_title_generator=lambda f: f.upper())

        field_a: str = Field(title='MyFieldA', field_title_generator=lambda f: f.upper())

        @computed_field(title='MyFieldB', field_title_generator=lambda f: f.upper())
        def field_b(self) -> str:
            return self.field_a

    assert Model.model_json_schema(mode='serialization') == {
        'properties': {
            'field_a': {'title': 'MyFieldA', 'type': 'string'},
            'field_b': {'readOnly': True, 'title': 'MyFieldB', 'type': 'string'},
        },
        'required': ['field_a', 'field_b'],
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

    class MyTypedDict(TypedDictAll):
        __pydantic_config__ = ConfigDict(field_title_generator=lambda f: f.upper())
        field_a: Annotated[str, Field(title='MyTitle', field_title_generator=lambda f: f.upper())]

    assert TypeAdapter(MyTypedDict).json_schema() == {
        'properties': {'field_a': {'title': 'MyTitle', 'type': 'string'}},
        'required': ['field_a'],
        'title': 'MyTypedDict',
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


@pytest.mark.parametrize('invalid_return_value', (1, 2, 3, tuple(), list(), object()))
def test_class_title_generator_returns_invalid_type(invalid_return_value, TypedDictAll):
    with pytest.raises(
        TypeError, match=f'class_title_generator .* must return str, not {invalid_return_value.__class__}'
    ):

        class Model(BaseModel):
            model_config = ConfigDict(class_title_generator=lambda m: invalid_return_value)

    with pytest.raises(
        TypeError, match=f'class_title_generator .* must return str, not {invalid_return_value.__class__}'
    ):

        @pydantic.dataclasses.dataclass(config=ConfigDict(class_title_generator=lambda m: invalid_return_value))
        class MyDataclass:
            pass

    with pytest.raises(
        TypeError, match=f'class_title_generator .* must return str, not {invalid_return_value.__class__}'
    ):

        class MyTypedDict(TypedDictAll):
            __pydantic_config__ = ConfigDict(class_title_generator=lambda m: invalid_return_value)
            pass

        TypeAdapter(MyTypedDict)


@pytest.mark.parametrize('invalid_return_value', (1, 2, 3, tuple(), list(), object()))
def test_config_field_title_generator_returns_invalid_type(invalid_return_value, TypedDictAll):
    with pytest.raises(
        TypeError, match=f'field_title_generator .* must return str, not {invalid_return_value.__class__}'
    ):

        class Model(BaseModel):
            model_config = ConfigDict(field_title_generator=lambda f: invalid_return_value)

            field_a: str

    with pytest.raises(
        TypeError, match=f'field_title_generator .* must return str, not {invalid_return_value.__class__}'
    ):

        @pydantic.dataclasses.dataclass(config=ConfigDict(field_title_generator=lambda f: invalid_return_value))
        class MyDataclass:
            field_a: str

    with pytest.raises(
        TypeError, match=f'field_title_generator .* must return str, not {invalid_return_value.__class__}'
    ):

        class MyTypedDict(TypedDictAll):
            __pydantic_config__ = ConfigDict(field_title_generator=lambda f: invalid_return_value)
            field_a: str

        TypeAdapter(MyTypedDict)


@pytest.mark.parametrize('invalid_return_value', (1, 2, 3, tuple(), list(), object()))
def test_field_title_generator_returns_invalid_type(invalid_return_value, TypedDictAll):
    with pytest.raises(
        TypeError, match=f'field_title_generator .* must return str, not {invalid_return_value.__class__}'
    ):

        class Model(BaseModel):
            field_a: Any = Field(field_title_generator=lambda f: invalid_return_value)

        Model(field_a=invalid_return_value).model_json_schema()

    with pytest.raises(
        TypeError, match=f'field_title_generator .* must return str, not {invalid_return_value.__class__}'
    ):

        @pydantic.dataclasses.dataclass
        class MyDataclass:
            field_a: Any = Field(field_title_generator=lambda f: invalid_return_value)

        model_json_schema(MyDataclass)

    with pytest.raises(
        TypeError, match=f'field_title_generator .* must return str, not {invalid_return_value.__class__}'
    ):

        class MyTypedDict(TypedDictAll):
            field_a: Annotated[str, Field(field_title_generator=lambda f: invalid_return_value)]

        TypeAdapter(MyTypedDict)
