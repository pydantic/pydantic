"""Container cursor coverage through transparent validator wrappers."""

from typing import Annotated, Any

import pytest
from pydantic_core import SchemaValidator, core_schema

from pydantic import AfterValidator, BaseModel, TypeAdapter, ValidationError, ValidationInfo


@pytest.mark.parametrize('with_info', [False, True])
def test_after_container_root(with_info: bool) -> None:
    seen: list[tuple[list[int], str]] = []

    def with_context(value: list[int], info: ValidationInfo) -> list[int]:
        seen.append((value.copy(), info.mode))
        return list(reversed(value))

    def without_context(value: list[int]) -> list[int]:
        seen.append((value.copy(), 'no-info'))
        return list(reversed(value))

    adapter = TypeAdapter(Annotated[list[int], AfterValidator(with_context if with_info else without_context)])
    assert adapter.validate_json('["1", 2]') == [2, 1]
    assert seen == [([1, 2], 'json' if with_info else 'no-info')]
    seen.clear()
    assert adapter.validate_python(['1', 2]) == [2, 1]
    assert seen == [([1, 2], 'python' if with_info else 'no-info')]
    seen.clear()
    with pytest.raises(ValidationError):
        adapter.validate_json('["bad", 2]')
    assert seen == []


@pytest.mark.parametrize('nested', [False, True])
def test_after_container_error_input(nested: bool) -> None:
    observed: list[tuple[str, str | None, Any]] = []

    def reject(value: list[int], info: ValidationInfo) -> list[int]:
        observed.append((info.mode, info.field_name, info.data))
        raise ValueError('rejected')

    value_type = Annotated[list[int], AfterValidator(reject)]

    class Model(BaseModel):
        first: int
        values: value_type

    adapter = TypeAdapter(Model if nested else value_type)
    document = '{"first": 3, "values": ["1", 2]}' if nested else '["1", 2]'
    with pytest.raises(ValidationError) as exc_info:
        adapter.validate_json(document)
    error = exc_info.value.errors(include_url=False)[0]
    assert error['type'] == 'value_error'
    assert error['loc'] == (('values',) if nested else ())
    assert error['input'] == ['1', 2]
    assert observed[-1] == ('json', 'values' if nested else None, {'first': 3} if nested else None)


def test_after_container_invalid_skipped_utf8() -> None:
    calls: list[int] = []

    class Model(BaseModel):
        value: int

    def record(value: Model) -> Model:
        calls.append(value.value)
        return value

    adapter = TypeAdapter(Annotated[Model, AfterValidator(record)])
    with pytest.raises(ValidationError) as exc_info:
        adapter.validate_json(b'{"value": 1, "ignored": "\xff"}')
    assert exc_info.value.errors()[0]['type'] == 'json_invalid'
    assert calls == []


def test_json_or_python_container_branch() -> None:
    schema = core_schema.json_or_python_schema(
        core_schema.list_schema(core_schema.int_schema()),
        core_schema.list_schema(core_schema.str_schema()),
    )
    validator = SchemaValidator(schema)
    assert validator.validate_json('["1", 2]') == [1, 2]
    assert validator.validate_python(['1', '2']) == ['1', '2']
    with pytest.raises(ValidationError) as caught:
        validator.validate_json('["bad"]')
    assert caught.value.errors()[0]['loc'] == (0,)
    assert caught.value.errors()[0]['input'] == 'bad'


@pytest.mark.parametrize('default_strict', [False, True])
def test_lax_or_strict_container_branch(default_strict: bool) -> None:
    schema = core_schema.lax_or_strict_schema(
        core_schema.list_schema(core_schema.int_schema()),
        core_schema.list_schema(core_schema.str_schema()),
        strict=default_strict,
    )
    validator = SchemaValidator(schema)
    assert validator.validate_json('["1"]') == (['1'] if default_strict else [1])
    assert validator.validate_json('["1"]', strict=False) == [1]
    assert validator.validate_json('["1"]', strict=True) == ['1']
    with pytest.raises(ValidationError) as caught:
        validator.validate_json('[1]', strict=True)
    assert caught.value.errors()[0]['type'] == 'string_type'


def test_lax_or_strict_container_smart_union_exactness() -> None:
    branch = core_schema.lax_or_strict_schema(
        core_schema.list_schema(core_schema.str_schema()),
        core_schema.list_schema(core_schema.int_schema(strict=True)),
    )
    labeled = core_schema.no_info_after_validator_function(lambda value: ('wrapped', value), branch)
    validator = SchemaValidator(
        core_schema.list_schema(core_schema.union_schema([labeled, core_schema.list_schema(core_schema.str_schema())]))
    )
    assert validator.validate_json('[["1"], [2]]') == [['1'], ('wrapped', [2])]
