from typing import Dict, List, Optional, Union

import pytest

from pydantic import BaseModel


@pytest.mark.benchmark(group='model_schema_generation')
def test_simple_model_schema_generation(benchmark):
    def generate_schema():
        class SimpleModel(BaseModel):
            field1: str
            field2: int
            field3: float

    benchmark(generate_schema)


@pytest.mark.benchmark(group='model_schema_generation')
def test_nested_model_schema_generation(benchmark):
    def generate_schema():
        class NestedModel(BaseModel):
            field1: str
            field2: List[int]
            field3: Dict[str, float]

        class OuterModel(BaseModel):
            nested: NestedModel
            optional_nested: Optional[NestedModel]

    benchmark(generate_schema)


@pytest.mark.benchmark(group='model_schema_generation')
def test_complex_model_schema_generation(benchmark):
    def generate_schema():
        class ComplexModel(BaseModel):
            field1: Union[str, int, float]
            field2: List[Dict[str, Union[int, float]]]
            field3: Optional[List[Union[str, int]]]

    benchmark(generate_schema)


@pytest.mark.benchmark(group='model_schema_generation')
def test_recursive_model_schema_generation(benchmark):
    def generate_schema():
        class RecursiveModel(BaseModel):
            name: str
            children: Optional[List['RecursiveModel']] = None

    benchmark(generate_schema)
