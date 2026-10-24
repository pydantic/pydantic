from typing import Annotated, Literal

import pytest

from pydantic import BaseModel, Field, JsonValue, StrictStr, create_model

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


@pytest.mark.benchmark(group='union_json_serialization')
@pytest.mark.parametrize('union_mode', ['none', 'plain', 'discriminated'])
@pytest.mark.parametrize('size', [10_000, 100_000])
@pytest.mark.parametrize('item', [1.0, 1], ids=['float', 'int'])
def test_union_json_serialization(benchmark, union_mode, size, item):
    """Track the intermediate conversion cost from issue #12912 against a concrete model."""

    class StrDataA(BaseModel):
        buffer: StrictStr
        encoding: Literal['a']

    class StrDataB(BaseModel):
        buffer: StrictStr
        encoding: Literal['b']

    class JsonData(BaseModel):
        buffer: JsonValue
        encoding: Literal['json']

    data_type = {
        'none': JsonData,
        'plain': StrDataA | StrDataB | JsonData,
        'discriminated': Annotated[StrDataA | StrDataB | JsonData, Field(discriminator='encoding')],
    }[union_mode]
    model_type = create_model('Payload', data=(data_type, ...))
    inner = JsonData.model_construct(buffer=[item] * size, encoding='json')
    model = model_type.model_construct(data=inner)
    expected = create_model('Baseline', data=(JsonData, ...)).model_construct(data=inner).model_dump_json()

    assert benchmark(model.model_dump_json) == expected
