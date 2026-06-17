"""Tests for typing.Never / typing.NoReturn support.

Never is the bottom type — no value satisfies it. Pydantic should:
- Always fail validation for a Never-typed field
- Eliminate Never from unions (Never | T → T)
- Produce JSON Schema {"not": {}} (rejects everything)
"""

from typing import Generic, NoReturn, TypeVar

import pytest
from typing_extensions import Never

from pydantic import BaseModel, TypeAdapter, ValidationError

T = TypeVar('T')


class ReadWriteResponse(BaseModel, Generic[T]):
    data: dict
    write_token: T | None = None


def test_generic_knockout_disables_field():
    WriteResponse = ReadWriteResponse[str]
    ReadResponse = ReadWriteResponse[Never]

    assert WriteResponse(data={'id': 1}, write_token='abc').write_token == 'abc'
    assert ReadResponse(data={'id': 1}).write_token is None

    with pytest.raises(ValidationError):
        ReadResponse(data={'id': 1}, write_token='sneaky')


def test_never_field_rejects_all_values():
    class Unconstructable(BaseModel):
        x: Never

    with pytest.raises(ValidationError) as exc_info:
        Unconstructable(x='anything')

    error = exc_info.value.errors()[0]
    assert error['type'] == 'never_type'
    assert error['loc'] == ('x',)


def test_noreturn_is_equivalent_to_never():
    class Model(BaseModel):
        x: NoReturn

    with pytest.raises(ValidationError) as exc_info:
        Model(x='anything')

    assert exc_info.value.errors()[0]['type'] == 'never_type'


def test_never_eliminated_from_union():
    ta = TypeAdapter(Never | int)
    assert ta.validate_python(42) == 42


def test_optional_never_collapses_to_none():
    ta = TypeAdapter(Never | None)
    assert ta.validate_python(None) is None


def test_never_json_schema_rejects_everything():
    ta = TypeAdapter(Never)
    assert ta.json_schema() == {'not': {}}


def test_never_in_union_json_schema():
    ta = TypeAdapter(Never | int)
    assert ta.json_schema() == {'type': 'integer'}
