"""Direct construction preserves the general union schema and field processing."""

from itertools import permutations
from typing import Annotated, Any, ForwardRef, Literal, Optional, TypeVar, Union

import pytest
from pydantic_core import core_schema

from pydantic import BaseModel, ConfigDict, Field, Tag, TypeAdapter, ValidationError, field_serializer, field_validator
from pydantic._internal._config import ConfigWrapper
from pydantic._internal._generate_schema import GenerateSchema

SCALARS = (str, bytes, int, float, bool, complex, type(None))


@pytest.mark.parametrize('members', [*permutations(SCALARS, 2), *permutations(SCALARS, 3)])
def test_direct_schema_matches_general_union(members: tuple[type, ...]) -> None:
    annotation = members[0] | members[1]
    for member in members[2:]:
        annotation |= member
    direct = GenerateSchema(ConfigWrapper({})).generate_schema(annotation)
    general = GenerateSchema(ConfigWrapper({}))._union_schema(annotation)
    assert direct == general
    assert direct is not general


@pytest.mark.parametrize(
    'annotation',
    [Optional[str], Union[int, str], str | None],  # noqa: UP007, UP045
    ids=['optional', 'typing-union', 'pep604-optional'],
)
def test_union_spellings(annotation: Any) -> None:
    assert TypeAdapter(annotation).core_schema == GenerateSchema(ConfigWrapper({}))._union_schema(annotation)


def test_independent_mutable_schemas() -> None:
    first = TypeAdapter(int | str | None).core_schema
    second = TypeAdapter(int | str | None).core_schema
    assert first == second
    assert first is not second
    assert first['schema'] is not second['schema']
    assert first['schema']['choices'] is not second['schema']['choices']
    for a, b in zip(first['schema']['choices'], second['schema']['choices']):
        assert a is not b
    first['schema']['choices'][0]['metadata'] = {'changed': True}
    assert 'metadata' not in second['schema']['choices'][0]


def test_member_order_affects_validation() -> None:
    assert type(TypeAdapter(int | float).validate_python('1')) is int
    assert type(TypeAdapter(float | int).validate_python('1')) is float
    assert TypeAdapter(Annotated[int | str, Field(union_mode='left_to_right')]).validate_python('123') == 123
    assert TypeAdapter(Annotated[str | int, Field(union_mode='left_to_right')]).validate_python('123') == '123'


def test_field_processing() -> None:
    class Model(BaseModel):
        value: Annotated[str | None, Field(min_length=2, title='Value')]
        plain: str | None

        @field_validator('value')
        @classmethod
        def upper(cls, value: str | None) -> str | None:
            return value.upper() if value is not None else None

        @field_serializer('value')
        def serialize_value(self, value: str | None) -> str | None:
            return value.lower() if value is not None else None

    model = Model(value='AB', plain='x')
    assert model.value == 'AB'
    assert model.model_dump() == {'value': 'ab', 'plain': 'x'}
    assert Model.model_json_schema()['properties']['value']['title'] == 'Value'
    with pytest.raises(ValidationError):
        Model(value='a', plain='x')
    assert TypeAdapter(str | None).validate_python('a') == 'a'


def test_strict_config() -> None:
    adapter = TypeAdapter(int | str, config=ConfigDict(strict=True))
    assert adapter.validate_python(1) == 1
    with pytest.raises(ValidationError):
        adapter.validate_python(b'1')


def test_encoders_use_general_path(monkeypatch: pytest.MonkeyPatch) -> None:
    calls = []
    original = GenerateSchema._union_schema

    def spy(self: GenerateSchema, annotation: Any) -> core_schema.CoreSchema:
        calls.append(annotation)
        return original(self, annotation)

    monkeypatch.setattr(GenerateSchema, '_union_schema', spy)
    with pytest.warns(DeprecationWarning, match='json_encoders'):
        adapter = TypeAdapter(int | str, config=ConfigDict(json_encoders={int: lambda value: f'number:{value}'}))
    assert calls == [int | str]
    assert adapter.dump_json(2) == b'"number:2"'
    assert TypeAdapter(int | str).dump_json(2) == b'2'


def test_unsupported_members_use_general_path(monkeypatch: pytest.MonkeyPatch) -> None:
    calls = []
    original = GenerateSchema._union_schema

    def spy(self: GenerateSchema, annotation: Any) -> core_schema.CoreSchema:
        calls.append(annotation)
        return original(self, annotation)

    monkeypatch.setattr(GenerateSchema, '_union_schema', spy)

    class CustomInt(int):
        @classmethod
        def __get_pydantic_core_schema__(cls, source: Any, handler: Any) -> core_schema.CoreSchema:
            return core_schema.str_schema()

    variable = TypeVar('variable')
    for annotation in (int | Any, int | Literal['x'], int | list[int], int | CustomInt, int | variable):
        TypeAdapter(annotation)
        assert any(a is annotation for a in calls)
    assert TypeAdapter(CustomInt | int).validate_python('x') == 'x'
    assert TypeAdapter(Union[int, ForwardRef('str')]).validate_python('x') == 'x'  # noqa: UP007


def test_tags_preserved_by_fallback() -> None:
    annotation = Annotated[int, Tag('int')] | Annotated[str, Tag('str')]
    schema = TypeAdapter(annotation).core_schema
    assert [choice[1] for choice in schema['choices']] == ['int', 'str']
