"""Recovered control flow must not expose a partially consumed child container."""

from typing import Annotated

import pytest
from pydantic_core import PydanticUseDefault, SchemaValidator, ValidationError, core_schema

from pydantic import AfterValidator, BaseModel, Field


@pytest.mark.parametrize(
    'kind, data',
    [
        ('list', b'{"values":[0}'),
        ('list', b'{"values":[0]'),
        ('list', b'{"values":[0,"\xff"]}'),
        ('dict-value', b'{"values":{"a":0}'),
        ('dict-value', b'{"values":{"a":0,"b":}}'),
        ('dict-key', b'{"values":{"use_default":}'),
    ],
)
def test_cursor_use_default_preserves_json_syntax_priority(kind: str, data: bytes) -> None:
    def use_default(value: int | str) -> int | str:
        if value in (0, 'use_default'):
            raise PydanticUseDefault
        return value

    class ListModel(BaseModel):
        values: list[Annotated[int, AfterValidator(use_default)]]

    class DictValueModel(BaseModel):
        values: dict[str, Annotated[int, AfterValidator(use_default)]]

    class DictKeyModel(BaseModel):
        values: dict[Annotated[str, AfterValidator(use_default)], int]

    model = {'list': ListModel, 'dict-value': DictValueModel, 'dict-key': DictKeyModel}[kind]
    ordinary = SchemaValidator(core_schema.chain_schema([model.__pydantic_core_schema__, core_schema.any_schema()]))
    with pytest.raises(ValidationError) as expected:
        ordinary.validate_json(data)
    with pytest.raises(ValidationError) as actual:
        model.model_validate_json(data)
    assert actual.value.errors(include_url=False) == expected.value.errors(include_url=False)
    assert actual.value.errors()[0]['type'] == 'json_invalid'


@pytest.mark.parametrize('kind', ['list', 'dict-value', 'dict-key'])
def test_cursor_use_default_completion_does_not_replay(kind: str) -> None:
    calls: list[int | str] = []

    def use_default(value: int | str) -> int | str:
        calls.append(value)
        if value in (0, 'use_default'):
            raise PydanticUseDefault
        return value

    class ListModel(BaseModel):
        values: list[Annotated[int, AfterValidator(use_default)]]

    class DictValueModel(BaseModel):
        values: dict[str, Annotated[int, AfterValidator(use_default)]]

    class DictKeyModel(BaseModel):
        values: dict[Annotated[str, AfterValidator(use_default)], int]

    model, data, expected_calls = {
        'list': (ListModel, '{"values":[0,2]}', [0]),
        'dict-value': (DictValueModel, '{"values":{"a":0,"b":2}}', [0]),
        'dict-key': (DictKeyModel, '{"values":{"use_default":1,"b":2}}', ['use_default']),
    }[kind]
    ordinary = SchemaValidator(core_schema.chain_schema([model.__pydantic_core_schema__, core_schema.any_schema()]))
    with pytest.raises(ValidationError) as expected:
        ordinary.validate_json(data)
    calls.clear()
    with pytest.raises(ValidationError) as actual:
        model.model_validate_json(data)
    assert actual.value.errors(include_url=False) == expected.value.errors(include_url=False)
    assert calls == expected_calls


def test_cursor_escaped_default_validation_control_keeps_json_priority() -> None:
    def use_default(value: int) -> int:
        raise PydanticUseDefault

    class Inner(BaseModel):
        value: Annotated[int, AfterValidator(use_default)] = Field(default=1, validate_default=True)
        rest: int

    class Outer(BaseModel):
        inner: Inner

    # Although the default itself is misconfigured, malformed JSON must be
    # rejected before validation can escape from the unfinished inner object.
    with pytest.raises(ValidationError) as actual:
        Outer.model_validate_json('{"inner":{"value":1}')
    assert actual.value.errors()[0]['type'] == 'json_invalid'
