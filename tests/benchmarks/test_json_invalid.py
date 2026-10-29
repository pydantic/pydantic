"""Measure JSON syntax errors separately from schema-validation errors.

Like jiter's json_cases_error group, cover both immediate and late parser failures.
The two APIs also measure their distinct Python exception construction paths.
"""

from collections.abc import Callable
from typing import Any

import pytest
from pydantic_core import from_json
from pytest_benchmark.fixture import BenchmarkFixture

from pydantic import TypeAdapter, ValidationError


@pytest.mark.parametrize('failure', ['early', 'late'])
@pytest.mark.parametrize('api', ['from_json', 'validate_json'])
def test_invalid_json(benchmark: BenchmarkFixture, failure: str, api: str) -> None:
    data = b'!' if failure == 'early' else b'[' + b'1,' * 256 + b'!'
    parse: Callable[[bytes], Any]
    error: type[ValueError]
    if api == 'from_json':
        parse, error = from_json, ValueError
    else:
        parse, error = TypeAdapter(list[int]).validate_json, ValidationError

    with pytest.raises(error):
        parse(data)

    def reject() -> None:
        try:
            parse(data)
        except error:
            pass
        else:
            raise AssertionError('Malformed JSON was accepted')

    benchmark(reject)
