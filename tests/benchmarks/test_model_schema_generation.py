from typing import Any, Callable, Dict, Generic, List, Literal, Optional, TypeVar, Union, get_origin

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
from pydantic.dataclasses import dataclass
from pydantic.functional_validators import ModelWrapValidatorHandler


@pytest.mark.benchmark(group='model_schema_generation')
def test_simple_model_schema_generation(benchmark) -> None:
    def generate_schema():
        class SimpleModel(BaseModel):
            field1: str
            field2: int
            field3: float

    benchmark(generate_schema)


@pytest.mark.benchmark(group='model_schema_generation')
def test_nested_model_schema_generation(benchmark) -> None:
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
def test_complex_model_schema_generation(benchmark) -> None:
    def generate_schema():
        class ComplexModel(BaseModel):
            field1: Union[str, int, float]
            field2: List[Dict[str, Union[int, float]]]
            field3: Optional[List[Union[str, int]]]

    benchmark(generate_schema)


@pytest.mark.benchmark(group='model_schema_generation')
def test_recursive_model_schema_generation(benchmark) -> None:
    def generate_schema():
        class RecursiveModel(BaseModel):
            name: str
            children: Optional[List['RecursiveModel']] = None

    benchmark(generate_schema)


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


@pytest.mark.benchmark(group='model_schema_generation')
def test_construct_schema():
    @dataclass(frozen=True, kw_only=True)
    class Root:
        data_class: NestedDataClass
        model: NestedModel


@pytest.mark.benchmark(group='model_schema_generation')
def test_lots_of_models_with_lots_of_fields():
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
        model = create_model(model_name, **model_fields)
        globals()[model_name] = model


@pytest.mark.parametrize('validator_mode', ['before', 'after', 'plain'])
@pytest.mark.benchmark(group='model_schema_generation')
def test_custom_field_validator_via_decorator(benchmark, validator_mode) -> None:
    def schema_gen() -> None:
        class ModelWithFieldValidator(BaseModel):
            field: Any

            @field_validator('field', mode=validator_mode)
            @classmethod
            def validate_field(cls, v: Any):
                return v

    benchmark(schema_gen)


@pytest.mark.benchmark(group='model_schema_generation')
def test_custom_wrap_field_validator_via_decorator(benchmark) -> None:
    def schema_gen() -> None:
        class ModelWithWrapFieldValidator(BaseModel):
            field: Any

            @field_validator('field', mode='wrap')
            @classmethod
            def validate_field(cls, v: Any, handler: ValidatorFunctionWrapHandler) -> Any:
                return handler(v)

    benchmark(schema_gen)


@pytest.mark.parametrize('validator_constructor', [BeforeValidator, AfterValidator, PlainValidator])
@pytest.mark.benchmark(group='model_schema_generation')
def test_custom_field_validator_via_annotation(benchmark, validator_constructor) -> None:
    def validate_field(v: Any) -> Any:
        return v

    def schema_gen(validation_func) -> None:
        class ModelWithFieldValidator(BaseModel):
            field: Annotated[Any, validator_constructor(validation_func)]

    benchmark(schema_gen, validate_field)


@pytest.mark.benchmark(group='model_schema_generation')
def test_custom_wrap_field_validator_via_annotation(benchmark) -> None:
    def validate_field(v: Any, handler: ValidatorFunctionWrapHandler) -> Any:
        return handler(v)

    def schema_gen(validator_func: Callable) -> None:
        class ModelWithWrapFieldValidator(BaseModel):
            field: Annotated[Any, WrapValidator(validator_func)]

    benchmark(schema_gen, validate_field)


@pytest.mark.benchmark(group='model_schema_generation')
def test_custom_model_validator_before(benchmark):
    def schema_gen() -> None:
        class ModelWithBeforeValidator(BaseModel):
            field: Any

            @model_validator(mode='before')
            @classmethod
            def validate_model_before(cls, data: Any) -> Any:
                return data

    benchmark(schema_gen)


@pytest.mark.benchmark(group='model_schema_generation')
def test_custom_model_validator_after(benchmark) -> None:
    def schema_gen() -> None:
        class ModelWithAfterValidator(BaseModel):
            field: Any

            @model_validator(mode='after')
            def validate_model_after(self: 'ModelWithAfterValidator') -> 'ModelWithAfterValidator':
                return self

    benchmark(schema_gen)


@pytest.mark.benchmark(group='model_schema_generation')
def test_custom_model_validator_wrap(benchmark) -> None:
    def schema_gen() -> None:
        class ModelWithWrapValidator(BaseModel):
            field: Any

            @model_validator(mode='wrap')
            @classmethod
            def validate_model_wrap(cls, values: Any, handler: ModelWrapValidatorHandler[Self]) -> Any:
                return handler(values)

    benchmark(schema_gen)


@pytest.mark.benchmark(group='model_schema_generation')
def test_custom_field_serializer_plain(benchmark) -> None:
    def schema_gen() -> None:
        class ModelWithFieldSerializer(BaseModel):
            field1: int

            @field_serializer('field1', mode='plain')
            def serialize_field(cls, v: int) -> str:
                return str(v)

    benchmark(schema_gen)


@pytest.mark.benchmark(group='model_schema_generation')
def test_custom_field_serializer_wrap(benchmark) -> None:
    def schema_gen() -> None:
        class ModelWithFieldSerializer(BaseModel):
            field1: int

            @field_serializer('field1', mode='wrap')
            def serialize_field(cls, v: int, nxt: SerializerFunctionWrapHandler) -> str:
                return nxt(v)

    benchmark(schema_gen)


@pytest.mark.benchmark(group='model_schema_generation')
def test_custom_model_serializer_decorator(benchmark) -> None:
    def schema_gen() -> None:
        class ModelWithModelSerializer(BaseModel):
            field1: Any

            @model_serializer
            def serialize_model(self) -> Any:
                return self.field1

    benchmark(schema_gen)


@pytest.mark.benchmark(group='model_schema_generation')
def test_custom_serializer_plain_annotated(benchmark) -> None:
    def schema_gen() -> None:
        def serialize_idempotent(x: Any) -> Any:
            return x

        class ModelWithAnnotatedSerializer(BaseModel):
            field: Annotated[List, PlainSerializer(serialize_idempotent, return_type=Any)]

    benchmark(schema_gen)


@pytest.mark.benchmark(group='model_schema_generation')
def test_custom_serializer_wrap_annotated(benchmark) -> None:
    def schema_gen() -> None:
        def serialize_idempotent(x: Any, nxt: SerializerFunctionWrapHandler) -> Any:
            return nxt(x)

        class ModelWithAnnotatedSerializer(BaseModel):
            field: Annotated[List, WrapSerializer(serialize_idempotent, when_used='json')]

    benchmark(schema_gen)
