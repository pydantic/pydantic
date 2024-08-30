from typing import Any, Dict, Generic, List, Literal, Optional, TypeVar, Union, get_origin

import pytest
from typing_extensions import Annotated

from pydantic import (
    BaseModel,
    Discriminator,
    Field,
    ValidationInfo,
    ValidatorFunctionWrapHandler,
    create_model,
    field_validator,
    model_validator,
)
from pydantic.dataclasses import dataclass
from pydantic.functional_validators import WrapValidator


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


@pytest.mark.benchmark
def test_construct_schema():
    @dataclass(frozen=True, kw_only=True)
    class Root:
        data_class: NestedDataClass
        model: NestedModel


@pytest.mark.benchmark
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


@pytest.mark.benchmark(group='model_schema_generation')
def test_custom_field_validator_before(benchmark):
    def schema_gen():
        class ModelWithBeforeValidator(BaseModel):
            field1: int

            @field_validator('field1', mode='before')
            def validate_before(cls, v):
                return v

    benchmark(schema_gen)


@pytest.mark.benchmark(group='model_schema_generation')
def test_custom_field_validator_after(benchmark):
    def schema_gen():
        class ModelWithAfterValidator(BaseModel):
            field2: int

            @field_validator('field2', mode='after')
            def validate_after(cls, v):
                return v

    benchmark(schema_gen)


@pytest.mark.benchmark(group='model_schema_generation')
def test_custom_field_validator_plain(benchmark):
    def schema_gen():
        class ModelWithPlainValidator(BaseModel):
            field3: str

            @field_validator('field3', mode='plain')
            def validate_plain(cls, v):
                if ' ' in v:
                    raise ValueError('field3 must not contain spaces')
                return v

    benchmark(schema_gen)


@pytest.mark.benchmark(group='model_schema_generation')
def test_custom_field_validator_wrap(benchmark):
    def schema_gen():
        def wrap_validator_field4(v: Any, handler: ValidatorFunctionWrapHandler, info: ValidationInfo) -> str:
            if ' ' in v:
                raise ValueError('field4 must not contain spaces')
            return v

        class ModelWithWrapValidator(BaseModel):
            field4: Annotated[str, WrapValidator(wrap_validator_field4)]

    benchmark(schema_gen)


@pytest.mark.benchmark(group='model_schema_generation')
def test_custom_model_validator_before(benchmark):
    def schema_gen():
        class ModelWithBeforeValidator(BaseModel):
            field1: int

            @model_validator(mode='before')
            @classmethod
            def validate_model_before(cls, data):
                if isinstance(data, dict):
                    data['field1'] = data.get('field1', 0) + 1
                return data

    benchmark(schema_gen)


@pytest.mark.benchmark(group='model_schema_generation')
def test_custom_model_validator_after(benchmark):
    def schema_gen():
        class ModelWithAfterValidator(BaseModel):
            field2: str

            @model_validator(mode='after')
            def validate_model_after(self):
                self.field2 = self.field2.upper()
                return self

    benchmark(schema_gen)


@pytest.mark.benchmark(group='model_schema_generation')
def test_custom_model_validator_wrap(benchmark):
    def schema_gen():
        class ModelWithWrapValidator(BaseModel):
            field1: int
            field2: str
            field3: float
            field4: bool

            @model_validator(mode='wrap')
            def validate_model_wrap(cls, values, handler):
                # Perform some validation before the default validation
                if values.get('field4') is True and values.get('field3', 0) < 0:
                    raise ValueError('field3 must be non-negative when field4 is True')

                # Call the default validation
                instance = handler(values)

                # Perform some validation after the default validation
                if instance.field1 > 100:
                    instance.field2 += '!'

                return instance

    benchmark(schema_gen)
