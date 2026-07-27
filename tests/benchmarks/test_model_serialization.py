from typing import Literal

import pytest

from pydantic import BaseModel, Field, JsonValue

from .shared import ComplexModel, NestedModel, OuterModel, SimpleModel


class _UnionStringDataA(BaseModel):
    buffer: str
    encoding: Literal['a']


class _UnionStringDataB(BaseModel):
    buffer: str
    encoding: Literal['b']


class _UnionJsonData(BaseModel):
    buffer: JsonValue
    encoding: Literal['json']


class _DiscriminatedUnionModel(BaseModel):
    data: _UnionStringDataA | _UnionStringDataB | _UnionJsonData = Field(discriminator='encoding')


class _ConcreteUnionModel(BaseModel):
    data: _UnionJsonData


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


@pytest.mark.benchmark(group='model_serialization_union')
def test_model_json_serialization_discriminated_union(benchmark):
    inner = _UnionJsonData.model_construct(buffer=[1.0] * 100_000, encoding='json')
    model = _DiscriminatedUnionModel.model_construct(data=inner)
    benchmark(model.model_dump_json)


@pytest.mark.benchmark(group='model_serialization_union')
def test_model_json_serialization_concrete(benchmark):
    inner = _UnionJsonData.model_construct(buffer=[1.0] * 100_000, encoding='json')
    model = _ConcreteUnionModel.model_construct(data=inner)
    benchmark(model.model_dump_json)
