from typing import List

import pytest

from pydantic import BaseModel

from .shared import ComplexModel, OuterModel, SimpleModel


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
