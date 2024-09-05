from typing import Any, Dict, Generic, List, Literal, Optional, Type, TypeVar, Union, get_origin

import pytest
from typing_extensions import Annotated, Self

from pydantic import (
    AfterValidator,
    BaseModel,
    BeforeValidator,
    Discriminator,
    Field,
    PlainSerializer,
    PlainValidator,
    SerializerFunctionWrapHandler,
    ValidatorFunctionWrapHandler,
    WrapSerializer,
    WrapValidator,
    create_model,
    field_serializer,
    field_validator,
    model_serializer,
    model_validator,
)
from pydantic.dataclasses import dataclass, rebuild_dataclass
from pydantic.functional_validators import ModelWrapValidatorHandler


class DeferredModel(BaseModel):
    model_config = {'defer_build': True}


def rebuild_model(model: Type[BaseModel]) -> None:
    model.model_rebuild(force=True, _types_namespace={})


@pytest.mark.benchmark(group='model_schema_generation')
def test_simple_model_schema_generation(benchmark) -> None:
    class SimpleModel(DeferredModel):
        field1: str
        field2: int
        field3: float

    benchmark(rebuild_model, SimpleModel)


@pytest.mark.benchmark(group='model_schema_generation')
def test_simple_model_schema_lots_of_fields_generation(benchmark) -> None:
    IntStr = Union[int, str]

    Model = create_model('Model', __config__={'defer_build': True}, **{f'f{i}': (IntStr, ...) for i in range(100)})

    benchmark(rebuild_model, Model)


@pytest.mark.benchmark(group='model_schema_generation')
def test_nested_model_schema_generation(benchmark) -> None:
    class NestedModel(BaseModel):
        field1: str
        field2: List[int]
        field3: Dict[str, float]

    class OuterModel(DeferredModel):
        nested: NestedModel
        optional_nested: Optional[NestedModel]

    benchmark(rebuild_model, OuterModel)


@pytest.mark.benchmark(group='model_schema_generation')
def test_complex_model_schema_generation(benchmark) -> None:
    class ComplexModel(DeferredModel):
        field1: Union[str, int, float]
        field2: List[Dict[str, Union[int, float]]]
        field3: Optional[List[Union[str, int]]]

    benchmark(rebuild_model, ComplexModel)


@pytest.mark.benchmark(group='model_schema_generation')
def test_recursive_model_schema_generation(benchmark) -> None:
    class RecursiveModel(DeferredModel):
        name: str
        children: Optional[List['RecursiveModel']] = None

    benchmark(rebuild_model, RecursiveModel)


@pytest.mark.benchmark(group='model_schema_generation')
def test_construct_dataclass_schema(benchmark):
    @dataclass(frozen=True, kw_only=True)
    class Cat:
        type: Literal['cat'] = 'cat'

    @dataclass(frozen=True, kw_only=True)
    class Dog:
        type: Literal['dog'] = 'dog'

    @dataclass(frozen=True, kw_only=True)
    class NestedDataClass:
        animal: Annotated[Union[Cat, Dog], Discriminator('type')]

    class NestedModel(BaseModel):
        animal: Annotated[Union[Cat, Dog], Discriminator('type')]

    @dataclass(frozen=True, kw_only=True, config={'defer_build': True})
    class Root:
        data_class: NestedDataClass
        model: NestedModel

    benchmark(lambda: rebuild_dataclass(Root, force=True, _types_namespace={}))


@pytest.mark.benchmark(group='model_schema_generation')
def test_lots_of_models_with_lots_of_fields(benchmark):
    T = TypeVar('T')

    class GenericModel(BaseModel, Generic[T]):
        value: T

    class RecursiveModel(BaseModel):
        name: str
        children: Optional[List['RecursiveModel']] = None

    class Address(BaseModel):
        street: Annotated[str, Field(max_length=100)]
        city: Annotated[str, Field(min_length=2)]
        zipcode: Annotated[str, Field(pattern=r'^\d{5}$')]

    class Person(BaseModel):
        name: Annotated[str, Field(min_length=1)]
        age: Annotated[int, Field(ge=0, le=120)]
        address: Address

    class Company(BaseModel):
        name: Annotated[str, Field(min_length=1)]
        employees: Annotated[List[Person], Field(min_length=1)]

    class Product(BaseModel):
        id: Annotated[int, Field(ge=1)]
        name: Annotated[str, Field(min_length=1)]
        price: Annotated[float, Field(ge=0)]
        metadata: Dict[str, str]

    # Repeat the pattern for other models up to Model_99
    models: list[type[BaseModel]] = []

    for i in range(100):
        model_fields = {}

        field_types = [
            Annotated[int, Field(ge=0, le=1000)],
            Annotated[str, Field(max_length=50)],
            Annotated[List[int], Field(min_length=1, max_length=10)],
            int,
            str,
            List[int],
            Dict[str, Union[str, int]],
            GenericModel[int],
            RecursiveModel,
            Address,
            Person,
            Company,
            Product,
            Union[
                int,
                str,
                List[str],
                Dict[str, int],
                GenericModel[str],
                RecursiveModel,
                Address,
                Person,
                Company,
                Product,
            ],
        ]

        for j in range(100):
            field_type = field_types[j % len(field_types)]
            if get_origin(field_type) is Annotated:
                model_fields[f'field_{j}'] = field_type
            else:
                model_fields[f'field_{j}'] = (field_type, ...)

        model_name = f'Model_{i}'
        models.append(create_model(model_name, __config__={'defer_build': True}, **model_fields))

    def rebuild_models(models: List[Type[BaseModel]]) -> None:
        for model in models:
            rebuild_model(model)

    benchmark(rebuild_models, models)


@pytest.mark.parametrize('validator_mode', ['before', 'after', 'plain'])
@pytest.mark.benchmark(group='model_schema_generation')
def test_custom_field_validator_via_decorator(benchmark, validator_mode) -> None:
    class ModelWithFieldValidator(DeferredModel):
        field: Any

        @field_validator('field', mode=validator_mode)
        @classmethod
        def validate_field(cls, v: Any):
            return v

    benchmark(rebuild_model, ModelWithFieldValidator)


@pytest.mark.benchmark(group='model_schema_generation')
def test_custom_wrap_field_validator_via_decorator(benchmark) -> None:
    class ModelWithWrapFieldValidator(DeferredModel):
        field: Any

        @field_validator('field', mode='wrap')
        @classmethod
        def validate_field(cls, v: Any, handler: ValidatorFunctionWrapHandler) -> Any:
            return handler(v)

    benchmark(rebuild_model, ModelWithWrapFieldValidator)


@pytest.mark.parametrize('validator_constructor', [BeforeValidator, AfterValidator, PlainValidator])
@pytest.mark.benchmark(group='model_schema_generation')
def test_custom_field_validator_via_annotation(benchmark, validator_constructor) -> None:
    def validate_field(v: Any) -> Any:
        return v

    class ModelWithFieldValidator(DeferredModel):
        field: Annotated[Any, validator_constructor(validate_field)]

    benchmark(rebuild_model, ModelWithFieldValidator)


@pytest.mark.benchmark(group='model_schema_generation')
def test_custom_wrap_field_validator_via_annotation(benchmark) -> None:
    def validate_field(v: Any, handler: ValidatorFunctionWrapHandler) -> Any:
        return handler(v)

    class ModelWithWrapFieldValidator(DeferredModel):
        field: Annotated[Any, WrapValidator(validate_field)]

    benchmark(rebuild_model, ModelWithWrapFieldValidator)


@pytest.mark.benchmark(group='model_schema_generation')
def test_custom_model_validator_before(benchmark):
    class ModelWithBeforeValidator(DeferredModel):
        field: Any

        @model_validator(mode='before')
        @classmethod
        def validate_model_before(cls, data: Any) -> Any:
            return data

    benchmark(rebuild_model, ModelWithBeforeValidator)


@pytest.mark.benchmark(group='model_schema_generation')
def test_custom_model_validator_after(benchmark) -> None:
    class ModelWithAfterValidator(DeferredModel):
        field: Any

        @model_validator(mode='after')
        def validate_model_after(self) -> Self:
            return self

    benchmark(rebuild_model, ModelWithAfterValidator)


@pytest.mark.benchmark(group='model_schema_generation')
def test_custom_model_validator_wrap(benchmark) -> None:
    class ModelWithWrapValidator(DeferredModel):
        field: Any

        @model_validator(mode='wrap')
        @classmethod
        def validate_model_wrap(cls, values: Any, handler: ModelWrapValidatorHandler[Self]) -> Any:
            return handler(values)

    benchmark(rebuild_model, ModelWithWrapValidator)


@pytest.mark.benchmark(group='model_schema_generation')
def test_custom_field_serializer_plain(benchmark) -> None:
    class ModelWithFieldSerializer(DeferredModel):
        field1: int

        @field_serializer('field1', mode='plain')
        def serialize_field(cls, v: int) -> str:
            return str(v)

    benchmark(rebuild_model, ModelWithFieldSerializer)


@pytest.mark.benchmark(group='model_schema_generation')
def test_custom_field_serializer_wrap(benchmark) -> None:
    class ModelWithFieldSerializer(DeferredModel):
        field1: int

        @field_serializer('field1', mode='wrap')
        def serialize_field(cls, v: int, nxt: SerializerFunctionWrapHandler) -> str:
            return nxt(v)

    benchmark(rebuild_model, ModelWithFieldSerializer)


@pytest.mark.benchmark(group='model_schema_generation')
def test_custom_model_serializer_decorator(benchmark) -> None:
    class ModelWithModelSerializer(DeferredModel):
        field1: Any

        @model_serializer
        def serialize_model(self) -> Any:
            return self.field1

    benchmark(rebuild_model, ModelWithModelSerializer)


@pytest.mark.benchmark(group='model_schema_generation')
def test_custom_serializer_plain_annotated(benchmark) -> None:
    class ModelWithAnnotatedSerializer(DeferredModel):
        field: Annotated[List, PlainSerializer(lambda x: x, return_type=Any)]

    benchmark(rebuild_model, ModelWithAnnotatedSerializer)


@pytest.mark.benchmark(group='model_schema_generation')
def test_custom_serializer_wrap_annotated(benchmark) -> None:
    class ModelWithAnnotatedSerializer(DeferredModel):
        field: Annotated[List, WrapSerializer(lambda x, nxt: nxt(x), when_used='json')]

    benchmark(rebuild_model, ModelWithAnnotatedSerializer)
