"""
Benchmarks for nested / recursive schemas using definitions.
"""

from typing import Callable

from pydantic_core import SchemaValidator

from .nested_schema import inlined_schema, input_data_valid, schema_using_defs


def test_nested_schema_using_defs(benchmark: Callable[..., None]) -> None:
    v = SchemaValidator(schema_using_defs())
    data = input_data_valid()
    v.validate_python(data)
    benchmark(v.validate_python, data)


def test_nested_schema_inlined(benchmark: Callable[..., None]) -> None:
    v = SchemaValidator(inlined_schema())
    data = input_data_valid()
    v.validate_python(data)
    benchmark(v.validate_python, data)
