"""Builtin scalar schemas remain independent after template copying."""

from typing import Any

import pytest

from pydantic import BaseModel, Field, TypeAdapter


@pytest.mark.parametrize(
    ('annotation', 'schema_type'),
    [
        (str, 'str'),
        (bytes, 'bytes'),
        (int, 'int'),
        (float, 'float'),
        (bool, 'bool'),
        (complex, 'complex'),
        (None, 'none'),
        (type(None), 'none'),
    ],
)
def test_scalar_schemas_are_independent(annotation: Any, schema_type: str) -> None:
    first = TypeAdapter(annotation).core_schema
    first['metadata'] = {'changed': True}

    second = TypeAdapter(annotation).core_schema
    assert second == {'type': schema_type}
    assert first is not second


def test_field_constraints_do_not_change_plain_scalar_schema() -> None:
    class Model(BaseModel):
        constrained: str = Field(min_length=2)
        plain: str

    assert Model(constrained='ab', plain='x').model_dump() == {'constrained': 'ab', 'plain': 'x'}
    with pytest.raises(ValueError):
        Model(constrained='a', plain='x')
    assert TypeAdapter(str).validate_python('a') == 'a'
