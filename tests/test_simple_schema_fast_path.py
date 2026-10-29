from typing import Annotated, Any, ForwardRef, Literal, Optional, TypeVar, Union, cast

import pytest
from pydantic_core import core_schema

from pydantic import BaseModel, ConfigDict, Field, TypeAdapter, ValidationError, field_serializer, field_validator
from pydantic._internal import _generate_schema
from pydantic._internal._config import ConfigWrapper
from pydantic._internal._generate_schema import GenerateSchema


@pytest.mark.parametrize(
    'annotation',
    [
        str,
        bytes,
        int,
        float,
        bool,
        complex,
        None,
        type(None),
        Optional[str],  # noqa: UP045 (exercise typing spelling)
        Union[str, None],  # noqa: UP007 (exercise typing spelling)
        str | None,
        int | str,
        Union[int, str],  # noqa: UP007 (exercise typing spelling)
        str | int | float,
        None | int | str,
    ],
    ids=[
        'str',
        'bytes',
        'int',
        'float',
        'bool',
        'complex',
        'none',
        'none-type',
        'optional',
        'typing-union-none',
        'pep604-optional',
        'pep604-union',
        'typing-union',
        'three-types',
        'three-types-none',
    ],
)
def test_simple_schema_matches_general_path(monkeypatch: pytest.MonkeyPatch, annotation: Any) -> None:
    fast = GenerateSchema(ConfigWrapper({})).generate_schema(annotation)
    monkeypatch.setattr(_generate_schema, '_is_simple_schema_type', lambda obj: False)
    normal = GenerateSchema(ConfigWrapper({})).generate_schema(annotation)
    assert fast == normal
    assert fast is not normal


def test_repeated_union_fields_have_independent_schemas() -> None:
    class Model(BaseModel):
        first: int | str
        second: int | str

    fields = Model.__pydantic_core_schema__['schema']['fields']
    first = fields['first']['schema']
    second = fields['second']['schema']
    assert first == second
    assert first is not second
    assert first['choices'][0] is not second['choices'][0]
    first['choices'][0]['metadata'] = {'only_first': True}
    assert 'metadata' not in second['choices'][0]


def test_simple_union_keeps_validation_serialization_and_field_processing() -> None:
    class Model(BaseModel):
        value: Annotated[int | str | None, Field(title='Value')]

        @field_validator('value')
        @classmethod
        def normalize(cls, value: int | str | None) -> int | str | None:
            return value.upper() if isinstance(value, str) else value

        @field_serializer('value')
        def serialize_value(self, value: int | str | None) -> str:
            return str(value)

    assert Model(value='abc').value == 'ABC'
    assert Model(value=None).model_dump() == {'value': 'None'}
    assert Model.model_json_schema()['properties']['value']['title'] == 'Value'


def test_json_encoders_follow_general_path(monkeypatch: pytest.MonkeyPatch) -> None:
    called = False
    original = GenerateSchema._generate_schema_inner

    def spy(self: GenerateSchema, obj: Any, origin: Any = None) -> core_schema.CoreSchema:
        nonlocal called
        called = True
        return original(self, obj, origin)

    monkeypatch.setattr(GenerateSchema, '_generate_schema_inner', spy)
    with pytest.warns(DeprecationWarning):
        adapter = TypeAdapter(int | str, config=ConfigDict(json_encoders={int: lambda value: f'number:{value}'}))
    assert called
    assert adapter.dump_json(7) == b'"number:7"'


def test_strict_configuration_applies_to_simple_union() -> None:
    adapter = TypeAdapter(int | str, config=ConfigDict(strict=True))
    assert adapter.validate_python(7) == 7
    assert adapter.validate_python('7') == '7'
    with pytest.raises(ValidationError):
        adapter.validate_python(b'7')


def test_unsupported_shapes_use_general_path(monkeypatch: pytest.MonkeyPatch) -> None:
    observed: list[Any] = []
    original = GenerateSchema._generate_schema_inner

    def spy(self: GenerateSchema, obj: Any, origin: Any = None) -> core_schema.CoreSchema:
        observed.append(obj)
        return original(self, obj, origin)

    monkeypatch.setattr(GenerateSchema, '_generate_schema_inner', spy)

    class Custom:
        @classmethod
        def __get_pydantic_core_schema__(cls, source: Any, handler: Any) -> core_schema.CoreSchema:
            return core_schema.str_schema()

    for annotation in (Any, Literal['x'], list[int], int | list[int], Custom | int, ForwardRef('int')):
        TypeAdapter(cast(Any, annotation))
        assert any(obj is annotation for obj in observed)
        observed.clear()

    variable = TypeVar('variable')
    TypeAdapter(cast(Any, variable))
    assert variable in observed


def test_identity_gate_rejects_custom_equality() -> None:
    class EqualToEverything:
        def __eq__(self, other: Any) -> bool:
            return True

    assert not _generate_schema._is_simple_schema_type(EqualToEverything())
