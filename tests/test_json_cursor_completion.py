"""Completed root controls preserve ordinary errors without replaying validation."""

from typing import Any

import pytest
from pydantic_core import PydanticOmit, PydanticUseDefault, SchemaError, SchemaValidator, ValidationError, core_schema


@pytest.mark.parametrize('signal', [PydanticOmit, PydanticUseDefault])
def test_completed_root_control_does_not_replay(signal: type[Exception]) -> None:
    calls = 0

    def stop(value: Any) -> Any:
        nonlocal calls
        calls += 1
        raise signal()

    schema = core_schema.no_info_after_validator_function(stop, core_schema.list_schema(core_schema.int_schema()))
    ordinary = SchemaValidator(core_schema.chain_schema([schema, core_schema.any_schema()]))
    assert 'ChainValidator' in repr(ordinary)
    with pytest.raises(SchemaError) as expected:
        ordinary.validate_json('[1,2]')
    assert calls == 1
    calls = 0
    with pytest.raises(SchemaError) as actual:
        SchemaValidator(schema).validate_json('[1,2]')
    assert str(actual.value) == str(expected.value)
    assert calls == 1


@pytest.mark.parametrize('signal', [PydanticOmit, PydanticUseDefault])
@pytest.mark.parametrize('data', [b'[1,2] trailing', b'[1,2', b'[1,"\xff"]'])
def test_root_control_does_not_hide_invalid_json(signal: type[Exception], data: bytes) -> None:
    def stop(value: Any) -> Any:
        raise signal()

    schema = core_schema.no_info_after_validator_function(stop, core_schema.list_schema(core_schema.int_schema()))
    ordinary = SchemaValidator(core_schema.chain_schema([schema, core_schema.any_schema()]))
    assert 'ChainValidator' in repr(ordinary)
    with pytest.raises(ValidationError) as expected:
        ordinary.validate_json(data)
    with pytest.raises(ValidationError) as actual:
        SchemaValidator(schema).validate_json(data)
    assert actual.value.errors(include_url=False) == expected.value.errors(include_url=False)
    assert actual.value.errors()[0]['type'] == 'json_invalid'


def test_completed_root_item_default_signal_does_not_replay() -> None:
    calls = 0

    def stop(value: int) -> int:
        nonlocal calls
        if value == 1:
            calls += 1
            raise PydanticUseDefault()
        return value

    schema = core_schema.list_schema(core_schema.no_info_after_validator_function(stop, core_schema.int_schema()))
    ordinary = SchemaValidator(core_schema.chain_schema([schema, core_schema.any_schema()]))
    assert 'ChainValidator' in repr(ordinary)
    with pytest.raises(SchemaError) as expected:
        ordinary.validate_json('[1,2]')
    assert calls == 1
    calls = 0
    with pytest.raises(SchemaError) as actual:
        SchemaValidator(schema).validate_json('[1,2]')
    assert str(actual.value) == str(expected.value)
    assert calls == 1
