"""Container union workloads for JSON validation and PGO training."""

import json
from typing import Literal

import pytest
from pytest_benchmark.fixture import BenchmarkFixture

from pydantic_core import SchemaValidator, core_schema


class _TaggedPayload:
    __slots__ = '__dict__', '__pydantic_extra__', '__pydantic_fields_set__', '__pydantic_private__'

    kind: str
    values: list[int]


@pytest.mark.benchmark(group='json-union-containers')
@pytest.mark.parametrize('case', ['smart-int', 'smart-coerce', 'tag-first', 'tag-last'])
def test_json_union_containers_core(
    benchmark: BenchmarkFixture, case: Literal['smart-int', 'smart-coerce', 'tag-first', 'tag-last']
) -> None:
    values = list(range(1_000))
    if case in ('smart-int', 'smart-coerce'):
        validator = SchemaValidator(
            core_schema.union_schema(
                [core_schema.list_schema(core_schema.int_schema()), core_schema.list_schema(core_schema.str_schema())]
            )
        )
        expected = values if case == 'smart-int' else [str(value) for value in values]
        data = json.dumps(expected).encode()
        result = validator.validate_json(data)
        assert result == expected
        assert type(result[0]) is (int if case == 'smart-int' else str)
    else:
        choices = {
            tag: core_schema.model_schema(
                _TaggedPayload,
                core_schema.model_fields_schema(
                    {
                        'kind': core_schema.model_field(core_schema.literal_schema([tag])),
                        'values': core_schema.model_field(core_schema.list_schema(core_schema.int_schema())),
                    }
                ),
            )
            for tag in ('a', 'b')
        }
        validator = SchemaValidator(core_schema.tagged_union_schema(choices, discriminator='kind'))
        payload = {'values': values, 'kind': 'a'} if case == 'tag-last' else {'kind': 'a', 'values': values}
        data = json.dumps(payload).encode()
        result = validator.validate_json(data)
        assert isinstance(result, _TaggedPayload)
        assert result.kind == 'a'
        assert result.values == values

    benchmark(validator.validate_json, data)
