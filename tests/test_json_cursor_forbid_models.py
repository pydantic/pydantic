"""Names-only forbidden-extra models share ordinary model error and construction policy."""

from typing import Literal

import pytest
from pydantic_core import SchemaValidator, ValidationError, core_schema

from pydantic import BaseModel, ConfigDict, Field, TypeAdapter


class ForbidModel(BaseModel):
    model_config = ConfigDict(extra='forbid')

    a: int
    b: list[int] = Field(default_factory=list)


@pytest.mark.parametrize('data', ['{"a":1}', '{"a":1,"b":[1,2]}', '{"b":[1,2],"a":1}'])
def test_cursor_forbid_models_match_ordinary_construction(data: str) -> None:
    ordinary = SchemaValidator(
        core_schema.chain_schema([ForbidModel.__pydantic_core_schema__, core_schema.any_schema()])
    )
    expected = ordinary.validate_json(data)
    actual = ForbidModel.model_validate_json(data)
    assert actual.model_dump() == expected.model_dump()
    assert actual.model_fields_set == expected.model_fields_set
    assert actual.__pydantic_extra__ is None


@pytest.mark.parametrize(
    'data',
    [
        '{"a":"bad","b":["bad"],"z":1,"y":2}',
        '{"z":0,"a":1,"z":[1],"y":2,"z":3}',
        '{"a":1,"a":2,"z":3}',
        '{"b":["bad"],"z":3}',
        '{"a":1,"z":1,"z":{"nested":[1,2]}}',
        '{"a":1,"\\u007a":2,"z":3}',
    ],
)
def test_cursor_forbid_model_errors_match_ordinary_order_and_duplicates(data: str) -> None:
    ordinary = SchemaValidator(
        core_schema.chain_schema([ForbidModel.__pydantic_core_schema__, core_schema.any_schema()])
    )
    with pytest.raises(ValidationError) as expected:
        ordinary.validate_json(data)
    with pytest.raises(ValidationError) as actual:
        ForbidModel.model_validate_json(data)
    assert actual.value.errors(include_url=False) == expected.value.errors(include_url=False)


@pytest.mark.parametrize('extra', ['ignore', 'allow', 'forbid'])
def test_cursor_forbid_model_runtime_extra_override(extra: Literal['ignore', 'allow', 'forbid']) -> None:
    data = '{"a":1,"z":2}'
    if extra == 'forbid':
        with pytest.raises(ValidationError) as actual:
            ForbidModel.model_validate_json(data, extra=extra)
        assert [error['loc'] for error in actual.value.errors()] == [('z',)]
    else:
        actual = ForbidModel.model_validate_json(data, extra=extra)
        assert actual.a == 1
        assert actual.b == []
        assert actual.__pydantic_extra__ == ({'z': 2} if extra == 'allow' else None)


def test_cursor_ignored_model_runtime_forbid_preserves_fields_first() -> None:
    class Model(BaseModel):
        a: int

    with pytest.raises(ValidationError) as actual:
        Model.model_validate_json('{"z":1,"a":"bad"}', extra='forbid')
    assert [error['loc'] for error in actual.value.errors()] == [('a',), ('z',)]


@pytest.mark.parametrize('data', [b'{"a":"bad","z":}', b'{"a":1,"z":"\xff"}', b'{"a":1,"z":1} trailing'])
def test_cursor_forbid_model_keeps_json_syntax_priority(data: bytes) -> None:
    with pytest.raises(ValidationError) as actual:
        ForbidModel.model_validate_json(data)
    assert actual.value.errors()[0]['type'] == 'json_invalid'


@pytest.mark.parametrize('in_list', [False, True])
def test_cursor_forbid_extra_keeps_document_depth_budget(in_list: bool) -> None:
    depth = 200 - int(in_list)
    data = b'{"a":1,"z":' + b'[' * depth + b'0' + b']' * depth + b'}'
    if in_list:
        data = b'[' + data + b']'
        validate = TypeAdapter(list[ForbidModel]).validate_json
    else:
        validate = ForbidModel.model_validate_json
    with pytest.raises(ValidationError) as actual:
        validate(data)
    assert actual.value.errors(include_input=False)[0]['type'] == 'json_invalid'
