"""Container-valued selectors and schema definition references."""

import json

import pytest
from pydantic_core import SchemaValidator, core_schema
from pytest_benchmark.fixture import BenchmarkFixture

from pydantic import BaseModel


class Node(BaseModel):
    value: int
    children: list['Node']


@pytest.mark.parametrize('case', ['json-python', 'lax-strict', 'scalar-reference', 'recursive-model'])
def test_json_graph_selectors(benchmark: BenchmarkFixture, case: str) -> None:
    if case == 'recursive-model':
        value = {'value': 0, 'children': [{'value': i, 'children': []} for i in range(1000)]}
        data = json.dumps(value).encode()
        result = Node.model_validate_json(data)
        assert len(result.children) == 1000
        benchmark(Node.model_validate_json, data)
        return
    if case == 'scalar-reference':
        schema = core_schema.definitions_schema(
            core_schema.definition_reference_schema('value'), [core_schema.int_schema(ref='value')]
        )
        data = b'1'
        expected = 1
    else:
        inner = core_schema.list_schema(core_schema.int_schema())
        schema = (
            core_schema.json_or_python_schema(inner, inner)
            if case == 'json-python'
            else core_schema.lax_or_strict_schema(inner, inner)
        )
        expected = list(range(10000))
        data = json.dumps(expected).encode()
    validator = SchemaValidator(schema)
    assert validator.validate_json(data) == expected
    benchmark(validator.validate_json, data)
