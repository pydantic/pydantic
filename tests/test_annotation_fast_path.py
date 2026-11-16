"""Bypassing empty annotation processing preserves generation and references."""

from enum import Enum
from typing import Any, Literal

import pytest
from pydantic_core import CoreSchema, SchemaSerializer, SchemaValidator, core_schema

from pydantic import BaseModel, Field, GetCoreSchemaHandler, GetJsonSchemaHandler, TypeAdapter
from pydantic._internal import _generate_schema
from pydantic._internal._config import ConfigWrapper
from pydantic._internal._generate_schema import GenerateSchema
from pydantic.json_schema import JsonSchemaValue


@pytest.mark.parametrize(
    'annotation',
    [int, str | None, int | str, list[int], dict[str, list[int | str]], Literal['a', 'b']],
    ids=['scalar', 'optional', 'union', 'list', 'nested', 'literal'],
)
def test_matches_annotation_handler_path(annotation: Any) -> None:
    direct = GenerateSchema(ConfigWrapper({}))._apply_annotations(annotation, [])
    normal = GenerateSchema(ConfigWrapper({}))._apply_annotations(annotation, [None])
    assert direct == normal
    assert direct is not normal


def test_enum_references() -> None:
    class Colour(Enum):
        red = 'red'

    generator = GenerateSchema(ConfigWrapper({}))
    schema = generator._apply_annotations(Colour, [])
    assert schema['type'] == 'definition-ref'
    assert SchemaValidator(generator.clean_schema(schema)).validate_python('red') is Colour.red

    class Model(BaseModel):
        first: Colour
        second: Colour

    json_schema = Model.model_json_schema()
    assert list(json_schema['$defs']) == ['Colour']
    assert json_schema['properties']['first'] == json_schema['properties']['second'] == {'$ref': '#/$defs/Colour'}


def test_custom_hooks_and_field_context() -> None:
    names: list[str | None] = []

    class Custom:
        @classmethod
        def __get_pydantic_core_schema__(cls, source: Any, handler: GetCoreSchemaHandler) -> CoreSchema:
            assert source is cls
            names.append(handler.field_name)
            return core_schema.int_schema(ref='Custom')

        @classmethod
        def __get_pydantic_json_schema__(cls, schema: CoreSchema, handler: GetJsonSchemaHandler) -> JsonSchemaValue:
            return {**handler(schema), 'title': 'Custom integer'}

    class Model(BaseModel):
        first: Custom
        second: Custom

    assert names == ['first', 'second']
    assert Model.model_validate({'first': '1', 'second': '2'}).model_dump() == {'first': 1, 'second': 2}
    json_schema = Model.model_json_schema()
    assert json_schema['$defs']['Custom'] == {'type': 'integer', 'title': 'Custom integer'}
    assert json_schema['properties']['first'] == json_schema['properties']['second'] == {'$ref': '#/$defs/Custom'}


def test_recursive_model() -> None:
    class Node(BaseModel):
        value: int
        children: list['Node'] = Field(default_factory=list)

    class Pair(BaseModel):
        first: Node
        second: Node

    model = Pair.model_validate({'first': {'value': '1', 'children': [{'value': '2'}]}, 'second': {'value': '3'}})
    assert model.first.children[0].value == 2
    assert model.second.value == 3
    json_schema = Pair.model_json_schema()
    assert list(json_schema['$defs']) == ['Node']
    assert json_schema['$defs']['Node']['properties']['children']['items'] == {'$ref': '#/$defs/Node'}


@pytest.mark.parametrize('annotation', [str, list[str]])
def test_explicit_transform(annotation: Any) -> None:
    generator = GenerateSchema(ConfigWrapper({}))
    schema = generator._apply_annotations(annotation, [], transform_inner_schema=core_schema.nullable_schema)
    assert schema['type'] == 'nullable'
    assert SchemaValidator(schema).validate_python(None) is None


def test_annotations_are_applied() -> None:
    generator = GenerateSchema(ConfigWrapper({}))
    schema = generator._apply_annotations(str, [Field(min_length=2)])
    validator = SchemaValidator(schema)
    assert validator.validate_python('ab') == 'ab'
    with pytest.raises(ValueError, match='at least 2 characters'):
        validator.validate_python('a')


def test_json_encoders_with_references() -> None:
    class Colour(Enum):
        red = 'red'

    with pytest.warns(DeprecationWarning, match='json_encoders'):

        class Model(BaseModel):
            model_config = {'json_encoders': {Colour: lambda value: value.name.upper()}}
            colour: Colour

    assert Model(colour=Colour.red).model_dump_json() == '{"colour":"RED"}'
    assert TypeAdapter(Colour).dump_json(Colour.red) == b'"red"'


def test_transform_reference_encoder_order(monkeypatch: pytest.MonkeyPatch) -> None:
    class Colour(Enum):
        red = 'red'

    generator = GenerateSchema(ConfigWrapper({'json_encoders': {Colour: lambda value: value.name.upper()}}))
    events: list[str] = []

    def transform(schema: CoreSchema) -> CoreSchema:
        assert schema['type'] == 'enum'
        assert 'serialization' not in schema
        schema.setdefault('metadata', {})['transformed'] = True
        events.append('transform')
        return schema

    original = _generate_schema._add_custom_serialization_from_json_encoders

    def add_encoder(encoders: Any, source: Any, schema: CoreSchema) -> CoreSchema:
        assert schema['type'] == 'definition-ref'
        definition = generator.defs.get_schema_from_ref(schema['schema_ref'])
        assert definition is not None
        assert definition.get('metadata', {})['transformed'] is True
        events.append('encoder')
        return original(encoders, source, schema)

    monkeypatch.setattr(_generate_schema, '_add_custom_serialization_from_json_encoders', add_encoder)
    with pytest.warns(DeprecationWarning, match='json_encoders'):
        schema = generator._apply_annotations(Colour, [], transform_inner_schema=transform)
    assert events == ['transform', 'encoder']
    assert SchemaSerializer(generator.clean_schema(schema)).to_json(Colour.red) == b'"RED"'
