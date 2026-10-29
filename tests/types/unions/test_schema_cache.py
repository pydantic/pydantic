"""Regression tests for the narrow scalar and flat-union schema cache."""

from typing import Annotated, Any, Literal, Optional, Union

import pytest

from pydantic import BaseModel, ConfigDict, Field, TypeAdapter, field_serializer, field_validator
from pydantic._internal._generate_schema import GenerateSchema, _simple_schema_cache_key


@pytest.mark.parametrize(
    ('annotation', 'expected'),
    [
        (Optional[str], ['str']),  # noqa: UP045
        (int | str, ['int', 'str']),
        (Union[int, str], ['int', 'str']),  # noqa: UP007
        (int | str | float, ['int', 'str', 'float']),
        (str | int | float, ['str', 'int', 'float']),
    ],
)
def test_union_cache_preserves_choices_and_isolation(annotation: Any, expected: list[str]) -> None:
    first = TypeAdapter(annotation).core_schema
    inner = first['schema'] if first['type'] == 'nullable' else first
    choices = inner['choices'] if inner['type'] == 'union' else [inner]
    assert [choice['type'] for choice in choices] == expected
    choices[0]['type'] = 'any'

    second = TypeAdapter(annotation)
    inner = second.core_schema['schema'] if second.core_schema['type'] == 'nullable' else second.core_schema
    choices = inner['choices'] if inner['type'] == 'union' else [inner]
    assert [choice['type'] for choice in choices] == expected


def test_cache_reuses_only_supported_shapes(monkeypatch: pytest.MonkeyPatch) -> None:
    GenerateSchema._simple_schema_cache.clear()
    original = GenerateSchema._union_schema
    calls = 0

    def counted(self: GenerateSchema, annotation: Any) -> Any:
        nonlocal calls
        calls += 1
        return original(self, annotation)

    monkeypatch.setattr(GenerateSchema, '_union_schema', counted)
    TypeAdapter(int | str | float)
    TypeAdapter(int | str | float)
    assert calls == 1

    class Custom:
        @classmethod
        def __get_pydantic_core_schema__(cls, source: Any, handler: Any) -> Any:
            return handler(str)

    for annotation in (int | Custom, int | Any, int | Literal['x'], list[int] | str):
        TypeAdapter(annotation)
    assert calls == 5


def test_cache_key_rejects_custom_types_without_equality(monkeypatch: pytest.MonkeyPatch) -> None:
    class TrickyMeta(type):
        def __eq__(cls, other: object) -> bool:
            raise AssertionError('equality must not be checked')

    class Tricky(metaclass=TrickyMeta):
        pass

    assert _simple_schema_cache_key(Tricky, None) is None
    assert _simple_schema_cache_key(int | str, Union) == (int, str)
    assert _simple_schema_cache_key(str | int, Union) == (str, int)
    monkeypatch.setattr('pydantic._internal._generate_schema.get_args', lambda obj: (int, Tricky))
    assert _simple_schema_cache_key(object(), Union) is None


def test_field_customization_stays_independent() -> None:
    class Model(BaseModel):
        value: Annotated[str | None, Field(min_length=2)]
        other: str | None

        @field_validator('value')
        @classmethod
        def upper(cls, value: str | None) -> str | None:
            return value.upper() if value is not None else None

        @field_serializer('value')
        def serialize_value(self, value: str | None) -> str | None:
            return value.lower() if value is not None else None

    model = Model(value='AB', other='x')
    assert model.value == 'AB'
    assert model.model_dump() == {'value': 'ab', 'other': 'x'}
    with pytest.raises(ValueError):
        Model(value='a', other='x')
    assert TypeAdapter(str | None).validate_python('a') == 'a'


def test_union_configured_encoders_do_not_reuse_cached_schema() -> None:
    TypeAdapter(int | str)
    with pytest.warns(DeprecationWarning, match='json_encoders'):
        adapter = TypeAdapter(int | str, config=ConfigDict(json_encoders={int: lambda value: f'number:{value}'}))
    assert adapter.dump_python(2, mode='json') == 'number:2'
    assert TypeAdapter(int | str).dump_python(2, mode='json') == 2


def test_cache_is_bounded() -> None:
    GenerateSchema._simple_schema_cache.clear()
    scalars = (str, bytes, int, float, bool, complex, type(None))
    for first in scalars:
        for second in scalars:
            for third in scalars:
                if first is not second and first is not third and second is not third:
                    TypeAdapter(first | second | third)
    assert len(GenerateSchema._simple_schema_cache) == GenerateSchema._simple_schema_cache_maxsize
