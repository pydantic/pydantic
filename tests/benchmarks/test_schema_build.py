from typing import Dict, Generic, List, Literal, Optional, TypeVar, Union, get_origin

import pytest
from typing_extensions import Annotated

from pydantic import BaseModel, Discriminator, Field, create_model
from pydantic.dataclasses import dataclass


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
