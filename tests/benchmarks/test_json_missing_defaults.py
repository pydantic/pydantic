from typing import Annotated

import pytest
from pytest_benchmark.fixture import BenchmarkFixture

from pydantic import AfterValidator, Field, TypeAdapter, ValidationInfo, create_model


@pytest.mark.benchmark(group='JSON missing defaults')
@pytest.mark.parametrize('kind', ['plain', 'validated', 'callback'])
def test_json_missing_defaults(benchmark: BenchmarkFixture, kind: str) -> None:
    def normalize(value: str, _info: ValidationInfo) -> str:
        return value.strip()

    annotation = Annotated[str, AfterValidator(normalize)] if kind == 'callback' else str
    model = create_model('DefaultValue', value=(annotation, Field(default=' Alice ', validate_default=kind != 'plain')))
    adapter = TypeAdapter(list[model])
    data = b'[' + b','.join([b'{}'] * 1000) + b']'
    expected = 'Alice' if kind == 'callback' else ' Alice '
    assert adapter.validate_json(data)[-1].value == expected
    benchmark(adapter.validate_json, data)
