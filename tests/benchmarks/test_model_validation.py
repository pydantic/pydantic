import pytest

from pydantic import BaseModel

from .shared import ComplexModel, OuterModel, SimpleModel

pytestmark = [
    pytest.mark.benchmark(group='model_validation'),
    pytest.mark.parametrize('method', ['model_validate', '__init__']),
]


def test_simple_model_validation(method: str, benchmark):
    data = {'field1': 'test', 'field2': 42, 'field3': 3.14}
    if method == '__init__':
        benchmark(lambda data: SimpleModel(**data), data)
    else:
        benchmark(SimpleModel.model_validate, data)


def test_nested_model_validation(method: str, benchmark):
    data = {'nested': {'field1': 'test', 'field2': [1, 2, 3], 'field3': {'a': 1.1, 'b': 2.2}}, 'optional_nested': None}
    if method == '__init__':
        benchmark(lambda data: OuterModel(**data), data)
    else:
        benchmark(OuterModel.model_validate, data)


def test_complex_model_validation(method: str, benchmark):
    data = {'field1': 'test', 'field2': [{'a': 1, 'b': 2.2}, {'c': 3, 'd': 4.4}], 'field3': ['test', 1, 2, 'test2']}
    if method == '__init__':
        benchmark(lambda data: ComplexModel(**data), data)
    else:
        benchmark(ComplexModel.model_validate, data)


def test_list_of_models_validation(method: str, benchmark):
    class SimpleListModel(BaseModel):
        items: list[SimpleModel]

    data = {'items': [{'field1': f'test{i}', 'field2': i, 'field3': float(i)} for i in range(10)]}
    if method == '__init__':
        benchmark(lambda data: SimpleListModel(**data), data)
    else:
        benchmark(SimpleListModel.model_validate, data)
