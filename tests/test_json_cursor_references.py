"""Cursor delegation through shared and recursive schema definitions."""

import json
from typing import Any

import pytest
from pydantic_core import SchemaValidator, core_schema
from typing_extensions import TypeAliasType

from pydantic import BaseModel, TypeAdapter, ValidationError


def test_shared_integer_definition() -> None:
    schema = core_schema.definitions_schema(
        core_schema.list_schema(core_schema.definition_reference_schema('integer')),
        [core_schema.int_schema(ref='integer')],
    )
    cursor = SchemaValidator(schema)
    ordinary = SchemaValidator(core_schema.chain_schema([schema, core_schema.any_schema()]))
    assert 'Chain' in repr(ordinary)
    assert cursor.validate_json('[1, "2", 9223372036854775808]') == [1, 2, 9223372036854775808]
    for data in ('[1, "bad", null]', '[true, 1.5]', '[1, 2] trailing'):
        with pytest.raises(ValidationError) as expected:
            ordinary.validate_json(data)
        with pytest.raises(ValidationError) as actual:
            cursor.validate_json(data)
        assert actual.value.json(include_url=False) == expected.value.json(include_url=False)


def test_recursive_model_definition() -> None:
    class Node(BaseModel):
        value: int
        children: list['Node']

    schema = Node.__pydantic_core_schema__
    ordinary = SchemaValidator(core_schema.chain_schema([schema, core_schema.any_schema()]))
    assert 'Chain' in repr(ordinary)
    value: dict[str, Any] = {'value': 0, 'children': [{'value': i, 'children': []} for i in range(20)]}
    data = json.dumps(value)
    assert Node.model_validate_json(data) == ordinary.validate_json(data)
    value['children'][13]['value'] = 'bad'
    data = json.dumps(value)
    with pytest.raises(ValidationError) as expected:
        ordinary.validate_json(data)
    with pytest.raises(ValidationError) as actual:
        Node.model_validate_json(data)
    assert actual.value.json(include_url=False) == expected.value.json(include_url=False)
    assert actual.value.errors()[0]['loc'] == ('children', 13, 'value')


def test_recursive_alias_definition() -> None:
    RecursiveList = TypeAliasType('RecursiveList', list['RecursiveList'] | int)
    adapter = TypeAdapter(RecursiveList)
    ordinary = SchemaValidator(core_schema.chain_schema([adapter.core_schema, core_schema.any_schema()]))
    assert adapter.validate_json('[1, [2, [3]], 4]') == [1, [2, [3]], 4]
    with pytest.raises(ValidationError) as expected:
        ordinary.validate_json('[1, ["bad"]]')
    with pytest.raises(ValidationError) as actual:
        adapter.validate_json('[1, ["bad"]]')
    assert actual.value.json(include_url=False) == expected.value.json(include_url=False)
