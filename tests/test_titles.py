import re
import typing
from typing import Any, Callable, List

import pytest
import typing_extensions

import pydantic
from pydantic import BaseModel, ConfigDict, Field, TypeAdapter, computed_field
from pydantic.fields import FieldInfo
from pydantic.json_schema import model_json_schema

from .test_types_typeddict import fixture_typed_dict, fixture_typed_dict_all  # noqa


@pytest.fixture(
    name='Annotated',
    params=[
        pytest.param(typing, id='typing.Annotated'),
        pytest.param(typing_extensions, id='t_e.Annotated'),
    ],
)
def fixture_annotated(request):
    try:
        return request.param.Annotated
    except AttributeError:
        pytest.skip(f'Annotated is not available from {request.param}')


def make_title(name: str, _):
    def _capitalize(v: str):
        return v[0].upper() + v[1:]

    return re.sub(r'(?<=[a-z])([A-Z])', r' \1', _capitalize(name))


FIELD_TITLE_GENERATORS: List[Callable[[str, Any], str]] = [
    lambda t, _: t.lower(),
    lambda t, _: t * 2,
    lambda t, _: 'My Title',
    make_title,
]

MODEL_TITLE_GENERATORS: List[Callable[[Any], str]] = [
    lambda m: m.__name__.upper(),
    lambda m: m.__name__ * 2,
    lambda m: 'My Model',
]


@pytest.mark.parametrize('model_title_generator', MODEL_TITLE_GENERATORS)
def test_model_model_title_generator(model_title_generator):
    class Model(BaseModel):
        model_config = ConfigDict(model_title_generator=model_title_generator)

    assert Model.model_json_schema() == {
        'properties': {},
        'title': model_title_generator(Model),
        'type': 'object',
    }


@pytest.mark.parametrize('model_title_generator', MODEL_TITLE_GENERATORS)
def test_model_title_generator_in_submodel(model_title_generator):
    class SubModel(BaseModel):
        model_config = ConfigDict(model_title_generator=model_title_generator)

    class Model(BaseModel):
        sub: SubModel

    assert Model.model_json_schema() == {
        '$defs': {'SubModel': {'properties': {}, 'title': model_title_generator(SubModel), 'type': 'object'}},
        'properties': {'sub': {'$ref': '#/$defs/SubModel'}},
        'required': ['sub'],
        'title': 'Model',
        'type': 'object',
    }


@pytest.mark.parametrize('field_title_generator', FIELD_TITLE_GENERATORS)
def test_field_title_generator_in_model_fields(field_title_generator):
    class Model(BaseModel):
        field_a: str = Field(field_title_generator=field_title_generator)
        field_b: int = Field(field_title_generator=field_title_generator)

        @computed_field(field_title_generator=field_title_generator)
        def field_c(self) -> str:
            return self.field_a

    assert Model.model_json_schema(mode='serialization') == {
        'properties': {
            'field_a': {'title': field_title_generator('field_a', Model.model_fields['field_a']), 'type': 'string'},
            'field_b': {'title': field_title_generator('field_b', Model.model_fields['field_b']), 'type': 'integer'},
            'field_c': {
                'readOnly': True,
                'title': field_title_generator('field_c', Model.model_computed_fields['field_c']),
                'type': 'string',
            },
        },
        'required': ['field_a', 'field_b', 'field_c'],
        'title': 'Model',
        'type': 'object',
    }


@pytest.mark.parametrize('field_title_generator', FIELD_TITLE_GENERATORS)
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
            'field_a': {'title': field_title_generator('field_a', Model.model_fields['field_a']), 'type': 'string'},
            'field_b': {'title': field_title_generator('field_b', Model.model_fields['field_b']), 'type': 'integer'},
            'field___c': {
                'title': field_title_generator('field___c', Model.model_fields['field___c']),
                'type': 'boolean',
            },
            'field_d': {
                'readOnly': True,
                'title': field_title_generator('field_d', Model.model_computed_fields['field_d']),
                'type': 'string',
            },
        },
        'required': ['field_a', 'field_b', 'field___c', 'field_d'],
        'title': 'Model',
        'type': 'object',
    }


@pytest.mark.parametrize('model_title_generator', MODEL_TITLE_GENERATORS)
def test_dataclass_model_title_generator(model_title_generator):
    @pydantic.dataclasses.dataclass(config=ConfigDict(model_title_generator=model_title_generator))
    class MyDataclass:
        field_a: int

    assert model_json_schema(MyDataclass) == {
        'properties': {'field_a': {'title': 'Field A', 'type': 'integer'}},
        'required': ['field_a'],
        'title': model_title_generator(MyDataclass),
        'type': 'object',
    }


@pytest.mark.parametrize('field_title_generator', FIELD_TITLE_GENERATORS)
def test_field_title_generator_in_dataclass_fields(field_title_generator):
    @pydantic.dataclasses.dataclass
    class MyDataclass:
        field_a: str = Field(field_title_generator=field_title_generator)
        field_b: int = Field(field_title_generator=field_title_generator)

    assert model_json_schema(MyDataclass) == {
        'properties': {
            'field_a': {
                'title': field_title_generator('field_a', MyDataclass.__pydantic_fields__['field_a']),
                'type': 'string',
            },
            'field_b': {
                'title': field_title_generator('field_b', MyDataclass.__pydantic_fields__['field_b']),
                'type': 'integer',
            },
        },
        'required': ['field_a', 'field_b'],
        'title': 'MyDataclass',
        'type': 'object',
    }


@pytest.mark.parametrize('field_title_generator', FIELD_TITLE_GENERATORS)
def test_dataclass_config_field_title_generator(field_title_generator):
    @pydantic.dataclasses.dataclass(config=ConfigDict(field_title_generator=field_title_generator))
    class MyDataclass:
        field_a: str
        field_b: int
        field___c: bool

    assert model_json_schema(MyDataclass) == {
        'properties': {
            'field_a': {
                'title': field_title_generator('field_a', MyDataclass.__pydantic_fields__['field_a']),
                'type': 'string',
            },
            'field_b': {
                'title': field_title_generator('field_b', MyDataclass.__pydantic_fields__['field_b']),
                'type': 'integer',
            },
            'field___c': {
                'title': field_title_generator('field___c', MyDataclass.__pydantic_fields__['field___c']),
                'type': 'boolean',
            },
        },
        'required': ['field_a', 'field_b', 'field___c'],
        'title': 'MyDataclass',
        'type': 'object',
    }


@pytest.mark.parametrize('model_title_generator', MODEL_TITLE_GENERATORS)
def test_typeddict_model_title_generator(model_title_generator, TypedDict):
    class MyTypedDict(TypedDict):
        __pydantic_config__ = ConfigDict(model_title_generator=model_title_generator)
        pass

    assert TypeAdapter(MyTypedDict).json_schema() == {
        'properties': {},
        'title': model_title_generator(MyTypedDict),
        'type': 'object',
    }


@pytest.mark.parametrize('field_title_generator', FIELD_TITLE_GENERATORS)
def test_field_title_generator_in_typeddict_fields(field_title_generator, TypedDict, Annotated):
    class MyTypedDict(TypedDict):
        field_a: Annotated[str, Field(field_title_generator=field_title_generator)]
        field_b: Annotated[int, Field(field_title_generator=field_title_generator)]

    assert TypeAdapter(MyTypedDict).json_schema() == {
        'properties': {
            'field_a': {
                'title': field_title_generator(
                    'field_a', FieldInfo.from_annotation(MyTypedDict.__annotations__['field_a'])
                ),
                'type': 'string',
            },
            'field_b': {
                'title': field_title_generator(
                    'field_b', FieldInfo.from_annotation(MyTypedDict.__annotations__['field_a'])
                ),
                'type': 'integer',
            },
        },
        'required': ['field_a', 'field_b'],
        'title': 'MyTypedDict',
        'type': 'object',
    }


@pytest.mark.parametrize('field_title_generator', FIELD_TITLE_GENERATORS)
def test_typeddict_config_field_title_generator(field_title_generator, TypedDict):
    class MyTypedDict(TypedDict):
        __pydantic_config__ = ConfigDict(field_title_generator=field_title_generator)
        field_a: str
        field_b: int
        field___c: bool

    assert TypeAdapter(MyTypedDict).json_schema() == {
        'properties': {
            'field_a': {
                'title': field_title_generator(
                    'field_a', FieldInfo.from_annotation(MyTypedDict.__annotations__['field_a'])
                ),
                'type': 'string',
            },
            'field_b': {
                'title': field_title_generator(
                    'field_b', FieldInfo.from_annotation(MyTypedDict.__annotations__['field_b'])
                ),
                'type': 'integer',
            },
            'field___c': {
                'title': field_title_generator(
                    'field___c', FieldInfo.from_annotation(MyTypedDict.__annotations__['field___c'])
                ),
                'type': 'boolean',
            },
        },
        'required': ['field_a', 'field_b', 'field___c'],
        'title': 'MyTypedDict',
        'type': 'object',
    }


@pytest.mark.parametrize(
    'field_level_title_generator,config_level_title_generator',
    ((lambda f, _: f.lower(), lambda f, _: f.upper()), (lambda f, _: f, make_title)),
)
def test_field_level_field_title_generator_precedence_over_config_level(
    field_level_title_generator, config_level_title_generator, TypedDict, Annotated
):
    class MyModel(BaseModel):
        model_config = ConfigDict(field_title_generator=field_level_title_generator)
        field_a: str = Field(field_title_generator=field_level_title_generator)

    assert MyModel.model_json_schema() == {
        'properties': {
            'field_a': {
                'title': field_level_title_generator('field_a', MyModel.model_fields['field_a']),
                'type': 'string',
            }
        },
        'required': ['field_a'],
        'title': 'MyModel',
        'type': 'object',
    }

    @pydantic.dataclasses.dataclass(config=ConfigDict(field_title_generator=field_level_title_generator))
    class MyDataclass:
        field_a: str = Field(field_title_generator=field_level_title_generator)

    assert model_json_schema(MyDataclass) == {
        'properties': {
            'field_a': {
                'title': field_level_title_generator('field_a', MyDataclass.__pydantic_fields__['field_a']),
                'type': 'string',
            }
        },
        'required': ['field_a'],
        'title': 'MyDataclass',
        'type': 'object',
    }

    class MyTypedDict(TypedDict):
        __pydantic_config__ = ConfigDict(field_title_generator=field_level_title_generator)
        field_a: Annotated[str, Field(field_title_generator=field_level_title_generator)]

    assert TypeAdapter(MyTypedDict).json_schema() == {
        'properties': {
            'field_a': {
                'title': field_level_title_generator(
                    'field_a', FieldInfo.from_annotation(MyTypedDict.__annotations__['field_a'])
                ),
                'type': 'string',
            }
        },
        'required': ['field_a'],
        'title': 'MyTypedDict',
        'type': 'object',
    }


def test_field_title_precedence_over_generators(TypedDict, Annotated):
    class Model(BaseModel):
        model_config = ConfigDict(field_title_generator=lambda f, _: f.upper())

        field_a: str = Field(title='MyFieldA', field_title_generator=lambda f, _: f.upper())

        @computed_field(title='MyFieldB', field_title_generator=lambda f, _: f.upper())
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

    @pydantic.dataclasses.dataclass(config=ConfigDict(field_title_generator=lambda f, _: f.upper()))
    class MyDataclass:
        field_a: str = Field(title='MyTitle', field_title_generator=lambda f, _: f.upper())

    assert model_json_schema(MyDataclass) == {
        'properties': {'field_a': {'title': 'MyTitle', 'type': 'string'}},
        'required': ['field_a'],
        'title': 'MyDataclass',
        'type': 'object',
    }

    class MyTypedDict(TypedDict):
        __pydantic_config__ = ConfigDict(field_title_generator=lambda f, _: f.upper())
        field_a: Annotated[str, Field(title='MyTitle', field_title_generator=lambda f, _: f.upper())]

    assert TypeAdapter(MyTypedDict).json_schema() == {
        'properties': {'field_a': {'title': 'MyTitle', 'type': 'string'}},
        'required': ['field_a'],
        'title': 'MyTypedDict',
        'type': 'object',
    }


def test_class_title_precedence_over_generator():
    class Model(BaseModel):
        model_config = ConfigDict(title='MyTitle', model_title_generator=lambda m: m.__name__.upper())

    assert Model.model_json_schema() == {
        'properties': {},
        'title': 'MyTitle',
        'type': 'object',
    }

    @pydantic.dataclasses.dataclass(
        config=ConfigDict(title='MyTitle', model_title_generator=lambda m: m.__name__.upper())
    )
    class MyDataclass:
        pass

    assert model_json_schema(MyDataclass) == {
        'properties': {},
        'title': 'MyTitle',
        'type': 'object',
    }


@pytest.mark.parametrize('invalid_return_value', (1, 2, 3, tuple(), list(), object()))
def test_model_title_generator_returns_invalid_type(invalid_return_value, TypedDict):
    with pytest.raises(
        TypeError, match=f'model_title_generator .* must return str, not {invalid_return_value.__class__}'
    ):

        class Model(BaseModel):
            model_config = ConfigDict(model_title_generator=lambda m: invalid_return_value)

    with pytest.raises(
        TypeError, match=f'model_title_generator .* must return str, not {invalid_return_value.__class__}'
    ):

        @pydantic.dataclasses.dataclass(config=ConfigDict(model_title_generator=lambda m: invalid_return_value))
        class MyDataclass:
            pass

    with pytest.raises(
        TypeError, match=f'model_title_generator .* must return str, not {invalid_return_value.__class__}'
    ):

        class MyTypedDict(TypedDict):
            __pydantic_config__ = ConfigDict(model_title_generator=lambda m: invalid_return_value)
            pass

        TypeAdapter(MyTypedDict)


@pytest.mark.parametrize('invalid_return_value', (1, 2, 3, tuple(), list(), object()))
def test_config_field_title_generator_returns_invalid_type(invalid_return_value, TypedDict):
    with pytest.raises(
        TypeError, match=f'field_title_generator .* must return str, not {invalid_return_value.__class__}'
    ):

        class Model(BaseModel):
            model_config = ConfigDict(field_title_generator=lambda f, _: invalid_return_value)

            field_a: str

    with pytest.raises(
        TypeError, match=f'field_title_generator .* must return str, not {invalid_return_value.__class__}'
    ):

        @pydantic.dataclasses.dataclass(config=ConfigDict(field_title_generator=lambda f, _: invalid_return_value))
        class MyDataclass:
            field_a: str

    with pytest.raises(
        TypeError, match=f'field_title_generator .* must return str, not {invalid_return_value.__class__}'
    ):

        class MyTypedDict(TypedDict):
            __pydantic_config__ = ConfigDict(field_title_generator=lambda f, _: invalid_return_value)
            field_a: str

        TypeAdapter(MyTypedDict)


@pytest.mark.parametrize('invalid_return_value', (1, 2, 3, tuple(), list(), object()))
def test_field_title_generator_returns_invalid_type(invalid_return_value, TypedDict, Annotated):
    with pytest.raises(
        TypeError, match=f'field_title_generator .* must return str, not {invalid_return_value.__class__}'
    ):

        class Model(BaseModel):
            field_a: Any = Field(field_title_generator=lambda f, _: invalid_return_value)

        Model(field_a=invalid_return_value).model_json_schema()

    with pytest.raises(
        TypeError, match=f'field_title_generator .* must return str, not {invalid_return_value.__class__}'
    ):

        @pydantic.dataclasses.dataclass
        class MyDataclass:
            field_a: Any = Field(field_title_generator=lambda f, _: invalid_return_value)

        model_json_schema(MyDataclass)

    with pytest.raises(
        TypeError, match=f'field_title_generator .* must return str, not {invalid_return_value.__class__}'
    ):

        class MyTypedDict(TypedDict):
            field_a: Annotated[str, Field(field_title_generator=lambda f, _: invalid_return_value)]

        TypeAdapter(MyTypedDict)
