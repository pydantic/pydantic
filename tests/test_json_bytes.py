"""Public-API coverage for byte-backed JSON validation."""

from typing import Annotated, Any

import pytest

from pydantic import BaseModel, Field, TypeAdapter, ValidationError, ValidationInfo, field_validator


def test_json_bytes_validated_defaults_and_nested_order() -> None:
    """https://github.com/pydantic/pydantic/pull/13884"""
    calls: list[str] = []

    class Child(BaseModel):
        name: str = Field(default=' Alice ', validate_default=True)

        @field_validator('name')
        @classmethod
        def normalize(cls, value: str, info: ValidationInfo) -> str:
            assert info.field_name == 'name'
            calls.append(value)
            return value.strip().lower()

    class OtherChild(Child):
        pass

    class Parent(BaseModel):
        first: Child
        second: OtherChild
        numbers: list[int]

    result = Parent.model_validate_json('{"second":{},"numbers":[1,"2"],"first":{"name":" Bob "}}')
    assert result.model_dump() == {'first': {'name': 'bob'}, 'second': {'name': 'alice'}, 'numbers': [1, 2]}
    assert calls == [' Bob ', ' Alice ']


@pytest.mark.parametrize('document', ['{"value":1}', '[{"value":1}]'])
def test_json_bytes_does_not_replay_rejected_callback(document: str) -> None:
    """https://github.com/pydantic/pydantic/pull/13884"""
    calls: list[int] = []

    class Model(BaseModel):
        value: int

        @field_validator('value')
        @classmethod
        def reject(cls, value: int) -> int:
            calls.append(value)
            if len(calls) == 1:
                raise ValueError('rejected')
            return value

    adapter: TypeAdapter[Any] = TypeAdapter(list[Model] if document.startswith('[') else Model)
    with pytest.raises(ValidationError):
        adapter.validate_json(document)
    assert calls == [1]


@pytest.mark.parametrize('document', [b'{"value":1} trailing', b'{"value":1,"ignored":"\xff"}'])
def test_json_bytes_checks_document_before_callbacks(document: bytes) -> None:
    """https://github.com/pydantic/pydantic/pull/13884"""
    calls: list[int] = []

    class Model(BaseModel):
        value: int

        @field_validator('value')
        @classmethod
        def record(cls, value: int) -> int:
            calls.append(value)
            return value

    with pytest.raises(ValidationError, check=lambda error: error.errors()[0]['type'] == 'json_invalid'):
        Model.model_validate_json(document)
    assert calls == []


def test_json_bytes_bounds_and_scalar_errors() -> None:
    """https://github.com/pydantic/pydantic/pull/13884"""
    adapter = TypeAdapter(Annotated[list[int], Field(max_length=1)])
    with pytest.raises(ValidationError, check=lambda error: error.errors()[0]['ctx']['actual_length'] == 3):
        adapter.validate_json('[1,2,3]')
    with pytest.raises(ValidationError, check=lambda error: error.errors()[0]['loc'] == (0,)):
        adapter.validate_json('["invalid"]')


def test_json_bytes_duplicate_dictionary_values_are_validated() -> None:
    """https://github.com/pydantic/pydantic/pull/14123"""
    adapter = TypeAdapter(dict[str, int])
    with pytest.raises(ValidationError):
        adapter.validate_json('{"a":"invalid","a":2}')
    assert adapter.validate_json('{"a":1,"a":2}') == {'a': 2}
