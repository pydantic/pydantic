from typing import (
    Annotated,
    Any,
    Generic,
    Literal,
    Optional,
    TypeVar,
    Union,
    get_origin,
)

import pytest
from typing_extensions import Self

from pydantic import (
    AfterValidator,
    BaseModel,
    BeforeValidator,
    Discriminator,
    Field,
    PlainSerializer,
    PlainValidator,
    Tag,
    WrapSerializer,
    WrapValidator,
    create_model,
    model_serializer,
    model_validator,
)
from pydantic.dataclasses import dataclass, rebuild_dataclass

from .shared import DeferredModel, PydanticTypes, StdLibTypes, rebuild_model


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

    Model = create_model(
        'Model',
        __config__={'defer_build': True},
        **{f'f{i}': (IntStr, ...) for i in range(100)},
    )

    benchmark(rebuild_model, Model)


@pytest.mark.benchmark(group='model_schema_generation')
def test_nested_model_schema_generation(benchmark) -> None:
    class NestedModel(BaseModel):
        field1: str
        field2: list[int]
        field3: dict[str, float]

    class OuterModel(DeferredModel):
        nested: NestedModel
        optional_nested: Optional[NestedModel]

    benchmark(rebuild_model, OuterModel)


@pytest.mark.benchmark(group='model_schema_generation')
def test_complex_model_schema_generation(benchmark) -> None:
    class ComplexModel(DeferredModel):
        field1: Union[str, int, float]
        field2: list[dict[str, Union[int, float]]]
        field3: Optional[list[Union[str, int]]]

    benchmark(rebuild_model, ComplexModel)


@pytest.mark.benchmark(group='model_schema_generation')
def test_recursive_model_schema_generation(benchmark) -> None:
    class RecursiveModel(DeferredModel):
        name: str
        children: Optional[list['RecursiveModel']] = None

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
        children: Optional[list['RecursiveModel']] = None

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
        employees: Annotated[list[Person], Field(min_length=1)]

    class Product(BaseModel):
        id: Annotated[int, Field(ge=1)]
        name: Annotated[str, Field(min_length=1)]
        price: Annotated[float, Field(ge=0)]
        metadata: dict[str, str]

    # Repeat the pattern for other models up to Model_99
    models: list[type[BaseModel]] = []

    for i in range(100):
        model_fields = {}

        field_types = [
            Annotated[int, Field(ge=0, le=1000)],
            Annotated[str, Field(max_length=50)],
            Annotated[list[int], Field(min_length=1, max_length=10)],
            int,
            str,
            list[int],
            dict[str, Union[str, int]],
            GenericModel[int],
            RecursiveModel,
            Address,
            Person,
            Company,
            Product,
            Union[
                int,
                str,
                list[str],
                dict[str, int],
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

    def rebuild_models(models: list[type[BaseModel]]) -> None:
        for model in models:
            rebuild_model(model)

    benchmark(rebuild_models, models)


@pytest.mark.benchmark(group='model_schema_generation')
def test_field_validators_serializers(benchmark) -> None:
    class ModelWithFieldValidatorsSerializers(DeferredModel):
        field1: Annotated[Any, BeforeValidator(lambda v: v)]
        field2: Annotated[Any, AfterValidator(lambda v: v)]
        field3: Annotated[Any, PlainValidator(lambda v: v)]
        field4: Annotated[Any, WrapValidator(lambda v, h: h(v))]
        field5: Annotated[Any, PlainSerializer(lambda x: x, return_type=Any)]
        field6: Annotated[Any, WrapSerializer(lambda x, nxt: nxt(x), when_used='json')]

    benchmark(rebuild_model, ModelWithFieldValidatorsSerializers)


@pytest.mark.benchmark(group='model_schema_generation')
def test_model_validators_serializers(benchmark):
    class ModelWithValidator(DeferredModel):
        field: Any

        @model_validator(mode='before')
        @classmethod
        def validate_model_before(cls, data: Any) -> Any:
            return data

        @model_validator(mode='after')
        def validate_model_after(self) -> Self:
            return self

        @model_serializer
        def serialize_model(self) -> Any:
            return self.field

    benchmark(rebuild_model, ModelWithValidator)


@pytest.mark.benchmark(group='model_schema_generation')
def test_tagged_union_with_str_discriminator_schema_generation(benchmark):
    class Cat(BaseModel):
        pet_type: Literal['cat']
        meows: int

    class Dog(BaseModel):
        pet_type: Literal['dog']
        barks: float

    class Lizard(BaseModel):
        pet_type: Literal['reptile', 'lizard']
        scales: bool

    class Model(DeferredModel):
        pet: Union[Cat, Dog, Lizard] = Field(discriminator='pet_type')
        n: int

    benchmark(rebuild_model, Model)


@pytest.mark.benchmark(group='model_schema_generation')
def test_tagged_union_with_callable_discriminator_schema_generation(benchmark):
    class Pie(BaseModel):
        time_to_cook: int
        num_ingredients: int

    class ApplePie(Pie):
        fruit: Literal['apple'] = 'apple'

    class PumpkinPie(Pie):
        filling: Literal['pumpkin'] = 'pumpkin'

    def get_discriminator_value(v: Any) -> str:
        if isinstance(v, dict):
            return v.get('fruit', v.get('filling'))
        return getattr(v, 'fruit', getattr(v, 'filling', None))

    class ThanksgivingDinner(DeferredModel):
        dessert: Annotated[
            Union[
                Annotated[ApplePie, Tag('apple')],
                Annotated[PumpkinPie, Tag('pumpkin')],
            ],
            Discriminator(get_discriminator_value),
        ]

    benchmark(rebuild_model, ThanksgivingDinner)


@pytest.mark.parametrize('field_type', StdLibTypes)
@pytest.mark.benchmark(group='stdlib_schema_generation')
@pytest.mark.skip('Clutters codspeed CI, but should be enabled on branches where we modify schema building.')
def test_stdlib_type_schema_generation(benchmark, field_type):
    class StdlibTypeModel(DeferredModel):
        field: field_type

    benchmark(rebuild_model, StdlibTypeModel)


@pytest.mark.parametrize('field_type', PydanticTypes)
@pytest.mark.benchmark(group='pydantic_custom_types_schema_generation')
@pytest.mark.skip('Clutters codspeed CI, but should be enabled on branches where we modify schema building.')
def test_pydantic_custom_types_schema_generation(benchmark, field_type):
    class PydanticTypeModel(DeferredModel):
        field: field_type

    benchmark(rebuild_model, PydanticTypeModel)
