"""Benchmark JSON model validation on direct and fallback streaming paths.

These cases use a model root, which is eligible for the cursor path in #14123.
Keep the input shape fixed so CodSpeed can compare changes to that path.
"""

import pytest
from pytest_benchmark.fixture import BenchmarkFixture

from pydantic import BaseModel, ValidationError


class ScalarModel(BaseModel):
    count: int
    name: str
    ratio: float


class NumbersModel(BaseModel):
    numbers: list[int]


@pytest.mark.benchmark(group='model_json_streaming')
@pytest.mark.parametrize(
    'case',
    ['scalar', 'list', 'coerce-last', 'invalid-last', 'syntax-last'],
    ids=['scalar', 'list-10000', 'coerce-last-10000', 'invalid-last-10000', 'syntax-last-10000'],
)
def test_model_json_streaming(benchmark: BenchmarkFixture, case: str) -> None:
    """Measure successful validation and late fallback/error costs separately."""
    if case == 'scalar':
        model = ScalarModel
        data = b'{"count":123,"name":"hello","ratio":1.5}'
    else:
        model = NumbersModel
        prefix = b'{"numbers":[' + b','.join(str(i).encode() for i in range(9999)) + b','
        if case == 'list':
            data = prefix + b'9999]}'
        elif case == 'coerce-last':
            data = prefix + b'"9999"]}'
        elif case == 'invalid-last':
            data = prefix + b'"oops"]}'
        else:
            data = prefix + b'9999]} trailing'

    if case in ('invalid-last', 'syntax-last'):
        with pytest.raises(ValidationError):
            model.model_validate_json(data)

        def reject() -> None:
            try:
                model.model_validate_json(data)
            except ValidationError:
                pass
            else:
                raise AssertionError('Invalid JSON or model value was accepted')

        benchmark(reject)
    else:
        result = model.model_validate_json(data)
        if case == 'scalar':
            assert result == ScalarModel(count=123, name='hello', ratio=1.5)
        else:
            assert result.numbers == list(range(10000))
        benchmark(model.model_validate_json, data)
