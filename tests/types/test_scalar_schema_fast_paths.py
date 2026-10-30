"""Scalar shortcuts preserve normal schema and field processing."""

import datetime
import re
import sys
from decimal import Decimal
from types import EllipsisType
from typing import Annotated, Any
from zoneinfo import ZoneInfo

import pytest
from pydantic_core import SchemaSerializer, SchemaValidator, core_schema

from pydantic import BaseModel, ConfigDict, Field, TypeAdapter, ValidationError, field_serializer, field_validator
from pydantic._internal import _generate_schema
from pydantic._internal._config import ConfigWrapper
from pydantic._internal._generate_schema import GenerateSchema
from pydantic.json_schema import GenerateJsonSchema

SPECIAL_TYPES = [datetime.date, datetime.datetime, datetime.time, datetime.timedelta, Decimal, ZoneInfo]


@pytest.mark.parametrize(
    'annotation',
    [str, bytes, int, float, bool, complex, None, type(None), object, EllipsisType, type, *SPECIAL_TYPES[:-1]],
)
@pytest.mark.parametrize('field_path', [False, True], ids=['generate', 'field'])
def test_matches_general_path(monkeypatch: pytest.MonkeyPatch, annotation: Any, field_path: bool) -> None:
    def build() -> core_schema.CoreSchema:
        generator = GenerateSchema(ConfigWrapper({}))
        return generator._apply_annotations(annotation, []) if field_path else generator.generate_schema(annotation)

    direct = build()
    monkeypatch.setattr(_generate_schema, '_is_simple_schema_type', lambda obj: False)
    normal = build()
    assert direct == normal
    assert direct is not normal
    direct['metadata'] = {'changed': True}
    assert 'metadata' not in normal


def test_field_processing() -> None:
    class Model(BaseModel):
        constrained: str = Field(min_length=2, title='Constrained')
        plain: str

        @field_validator('constrained')
        @classmethod
        def uppercase(cls, value: str) -> str:
            return value.upper()

        @field_serializer('constrained')
        def serialize_value(self, value: str) -> str:
            return value.lower()

    model = Model(constrained='ab', plain='x')
    assert model.constrained == 'AB'
    assert model.model_dump() == {'constrained': 'ab', 'plain': 'x'}
    assert Model.model_json_schema()['properties']['constrained']['title'] == 'Constrained'
    with pytest.raises(ValidationError):
        Model(constrained='a', plain='x')
    assert TypeAdapter(str).validate_python('a') == 'a'


def test_annotation_hook() -> None:
    class Metadata:
        @classmethod
        def __get_pydantic_core_schema__(cls, source: Any, handler: Any) -> core_schema.CoreSchema:
            schema = handler(source)
            schema['min_length'] = 2
            return schema

    adapter = TypeAdapter(Annotated[str, Metadata])
    with pytest.raises(ValidationError):
        adapter.validate_python('a')
    assert TypeAdapter(str).validate_python('a') == 'a'


@pytest.mark.parametrize('field_path', [False, True], ids=['adapter', 'model'])
def test_json_encoders(field_path: bool) -> None:
    config = ConfigDict(json_encoders={int: lambda value: f'number:{value}'})
    with pytest.warns(DeprecationWarning, match='json_encoders'):
        if field_path:

            class Model(BaseModel):
                model_config = config
                value: int

            result = Model(value=2).model_dump_json()
        else:
            result = TypeAdapter(int, config=config).dump_json(2).decode()
    assert result == ('{"value":"number:2"}' if field_path else '"number:2"')
    assert TypeAdapter(int).dump_json(2) == b'2'


def test_strict_config() -> None:
    adapter = TypeAdapter(int, config=ConfigDict(strict=True))
    with pytest.raises(ValidationError):
        adapter.validate_python('1')
    assert adapter.validate_python(1) == 1


def test_subclass_hooks() -> None:
    class CustomStr(str):
        @classmethod
        def __get_pydantic_core_schema__(cls, source: Any, handler: Any) -> core_schema.CoreSchema:
            return core_schema.int_schema()

    assert not _generate_schema._is_simple_schema_type(CustomStr)
    assert TypeAdapter(CustomStr).validate_python('12') == 12

    class Model(BaseModel):
        value: CustomStr

    assert Model.model_validate({'value': '12'}).value == 12


def test_identity_gate() -> None:
    class TrickyMeta(type):
        def __eq__(cls, other: object) -> bool:
            raise AssertionError('must not compare types by equality')

        def __hash__(cls) -> int:
            raise AssertionError('must not hash arbitrary types')

    class Tricky(metaclass=TrickyMeta):
        pass

    assert not _generate_schema._is_simple_schema_type(Tricky)


@pytest.mark.parametrize('annotation', [object, EllipsisType, type, re.Pattern, *SPECIAL_TYPES])
def test_additional_type_eligibility(annotation: Any) -> None:
    expected = annotation not in SPECIAL_TYPES or sys.implementation.name == 'cpython'
    assert _generate_schema._is_simple_schema_type(annotation) is expected


@pytest.mark.skipif(sys.implementation.name != 'pypy', reason='These classes are mutable on PyPy')
@pytest.mark.parametrize('annotation', SPECIAL_TYPES)
@pytest.mark.parametrize('field_path', [False, True], ids=['generate', 'field'])
def test_mutable_classes_preserve_hooks(monkeypatch: pytest.MonkeyPatch, annotation: Any, field_path: bool) -> None:
    def custom_schema(source: Any, handler: Any) -> core_schema.CoreSchema:
        return core_schema.str_schema(min_length=3)

    monkeypatch.setattr(annotation, '__get_pydantic_core_schema__', custom_schema, raising=False)
    generator = GenerateSchema(ConfigWrapper({}))
    schema = generator._apply_annotations(annotation, []) if field_path else generator.generate_schema(annotation)
    assert schema == core_schema.str_schema(min_length=3)


@pytest.mark.parametrize('annotation,value', [(re.Pattern, 'x+'), (ZoneInfo, 'UTC')])
@pytest.mark.parametrize('field_path', [False, True], ids=['generate', 'field'])
def test_function_schemas_match_general_path(
    monkeypatch: pytest.MonkeyPatch, annotation: Any, value: str, field_path: bool
) -> None:
    def build() -> core_schema.CoreSchema:
        generator = GenerateSchema(ConfigWrapper({}))
        return generator._apply_annotations(annotation, []) if field_path else generator.generate_schema(annotation)

    direct = build()
    monkeypatch.setattr(_generate_schema, '_is_simple_schema_type', lambda obj: False)
    normal = build()
    assert GenerateJsonSchema().generate(direct) == GenerateJsonSchema().generate(normal)
    result = SchemaValidator(direct).validate_python(value)
    assert result == SchemaValidator(normal).validate_python(value)
    assert SchemaSerializer(direct).to_json(result) == SchemaSerializer(normal).to_json(result)
