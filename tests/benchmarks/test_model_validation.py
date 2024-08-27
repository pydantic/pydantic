from typing import Dict, List, Optional, Union

import pytest

from pydantic import BaseModel


class SimpleModel(BaseModel):
    field1: str
    field2: int
    field3: float


class NestedModel(BaseModel):
    field1: str
    field2: List[int]
    field3: Dict[str, float]


class OuterModel(BaseModel):
    nested: NestedModel
    optional_nested: Optional[NestedModel]


class ComplexModel(BaseModel):
    field1: Union[str, int, float]
    field2: List[Dict[str, Union[int, float]]]
    field3: Optional[List[Union[str, int]]]


@pytest.mark.benchmark(group='model_validation')
def test_simple_model_validation(benchmark):
    data = {'field1': 'test', 'field2': 42, 'field3': 3.14}
    benchmark(SimpleModel.model_validate, data)


@pytest.mark.benchmark(group='model_validation')
def test_nested_model_validation(benchmark):
    data = {'nested': {'field1': 'test', 'field2': [1, 2, 3], 'field3': {'a': 1.1, 'b': 2.2}}, 'optional_nested': None}
    benchmark(OuterModel.model_validate, data)


@pytest.mark.benchmark(group='model_validation')
def test_complex_model_validation(benchmark):
    data = {'field1': 'test', 'field2': [{'a': 1, 'b': 2.2}, {'c': 3, 'd': 4.4}], 'field3': ['test', 1, 2, 'test2']}
    benchmark(ComplexModel.model_validate, data)


@pytest.mark.benchmark(group='model_validation')
def test_list_of_models_validation(benchmark):
    class SimpleListModel(BaseModel):
        items: List[SimpleModel]

    data = {'items': [{'field1': f'test{i}', 'field2': i, 'field3': float(i)} for i in range(10)]}
    benchmark(SimpleListModel.model_validate, data)
