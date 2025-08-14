import pytest

from pydantic import BaseModel

from .shared import ComplexModel, NestedModel, OuterModel, SimpleModel


@pytest.mark.benchmark(group='model_serialization')
def test_simple_model_serialization(benchmark):
    model = SimpleModel(field1='test', field2=42, field3=3.14)
    benchmark(model.model_dump)


@pytest.mark.benchmark(group='model_serialization')
def test_nested_model_serialization(benchmark):
    model = OuterModel(
        nested=NestedModel(field1='test', field2=[1, 2, 3], field3={'a': 1.1, 'b': 2.2}), optional_nested=None
    )
    benchmark(model.model_dump)


@pytest.mark.benchmark(group='model_serialization')
def test_complex_model_serialization(benchmark):
    model = ComplexModel(field1='test', field2=[{'a': 1, 'b': 2.2}, {'c': 3, 'd': 4.4}], field3=['test', 1, 2, 'test2'])
    benchmark(model.model_dump)


@pytest.mark.benchmark(group='model_serialization')
def test_list_of_models_serialization(benchmark):
    class SimpleListModel(BaseModel):
        items: list[SimpleModel]

    model = SimpleListModel(items=[SimpleModel(field1=f'test{i}', field2=i, field3=float(i)) for i in range(10)])
    benchmark(model.model_dump)


@pytest.mark.benchmark(group='model_serialization')
def test_model_json_serialization(benchmark):
    model = ComplexModel(field1='test', field2=[{'a': 1, 'b': 2.2}, {'c': 3, 'd': 4.4}], field3=['test', 1, 2, 'test2'])
    benchmark(model.model_dump_json)
