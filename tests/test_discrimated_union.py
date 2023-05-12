import re
from enum import Enum
from typing import Generic, TypeVar, Union

import pytest
from typing_extensions import Annotated, Literal

from pydantic import BaseModel, Field, ValidationError
from pydantic.errors import ConfigError
from pydantic.generics import GenericModel


def test_discriminated_union_only_union():
    with pytest.raises(
        TypeError, match='`discriminator` can only be used with `Union` type with more than one variant'
    ):

        class Model(BaseModel):
            x: str = Field(..., discriminator='qwe')


def test_discriminated_union_single_variant():
    with pytest.raises(
        TypeError, match='`discriminator` can only be used with `Union` type with more than one variant'
    ):

        class Model(BaseModel):
            x: Union[str] = Field(..., discriminator='qwe')


def test_discriminated_union_invalid_type():
    with pytest.raises(TypeError, match="Type 'str' is not a valid `BaseModel` or `dataclass`"):

        class Model(BaseModel):
            x: Union[str, int] = Field(..., discriminator='qwe')


def test_discriminated_union_defined_discriminator():
    class Cat(BaseModel):
        c: str

    class Dog(BaseModel):
        pet_type: Literal['dog']
        d: str

    with pytest.raises(ConfigError, match="Model 'Cat' needs a discriminator field for key 'pet_type'"):

        class Model(BaseModel):
            pet: Union[Cat, Dog] = Field(..., discriminator='pet_type')
            number: int


def test_discriminated_union_literal_discriminator():
    class Cat(BaseModel):
        pet_type: int
        c: str

    class Dog(BaseModel):
        pet_type: Literal['dog']
        d: str

    with pytest.raises(ConfigError, match="Field 'pet_type' of model 'Cat' needs to be a `Literal`"):

        class Model(BaseModel):
            pet: Union[Cat, Dog] = Field(..., discriminator='pet_type')
            number: int


def test_discriminated_union_root_same_discriminator():
    class BlackCat(BaseModel):
        pet_type: Literal['blackcat']

    class WhiteCat(BaseModel):
        pet_type: Literal['whitecat']

    class Cat(BaseModel):
        __root__: Union[BlackCat, WhiteCat]

    class Dog(BaseModel):
        pet_type: Literal['dog']

    with pytest.raises(ConfigError, match="Field 'pet_type' is not the same for all submodels of 'Cat'"):

        class Pet(BaseModel):
            __root__: Union[Cat, Dog] = Field(..., discriminator='pet_type')


def test_discriminated_union_validation():
    class BlackCat(BaseModel):
        pet_type: Literal['cat']
        color: Literal['black']
        black_infos: str

    class WhiteCat(BaseModel):
        pet_type: Literal['cat']
        color: Literal['white']
        white_infos: str

    class Cat(BaseModel):
        __root__: Annotated[Union[BlackCat, WhiteCat], Field(discriminator='color')]

    class Dog(BaseModel):
        pet_type: Literal['dog']
        d: str

    class Lizard(BaseModel):
        pet_type: Literal['reptile', 'lizard']
        l: str

    class Model(BaseModel):
        pet: Annotated[Union[Cat, Dog, Lizard], Field(discriminator='pet_type')]
        number: int

    with pytest.raises(ValidationError) as exc_info:
        Model.parse_obj({'pet': {'pet_typ': 'cat'}, 'number': 'x'})
    assert exc_info.value.errors() == [
        {
            'loc': ('pet',),
            'msg': "Discriminator 'pet_type' is missing in value",
            'type': 'value_error.discriminated_union.missing_discriminator',
            'ctx': {'discriminator_key': 'pet_type'},
        },
        {'loc': ('number',), 'msg': 'value is not a valid integer', 'type': 'type_error.integer'},
    ]

    with pytest.raises(ValidationError) as exc_info:
        Model.parse_obj({'pet': 'fish', 'number': 2})
    assert exc_info.value.errors() == [
        {
            'loc': ('pet',),
            'msg': "Discriminator 'pet_type' is missing in value",
            'type': 'value_error.discriminated_union.missing_discriminator',
            'ctx': {'discriminator_key': 'pet_type'},
        },
    ]

    with pytest.raises(ValidationError) as exc_info:
        Model.parse_obj({'pet': {'pet_type': 'fish'}, 'number': 2})
    assert exc_info.value.errors() == [
        {
            'loc': ('pet',),
            'msg': (
                "No match for discriminator 'pet_type' and value 'fish' "
                "(allowed values: 'cat', 'dog', 'reptile', 'lizard')"
            ),
            'type': 'value_error.discriminated_union.invalid_discriminator',
            'ctx': {
                'discriminator_key': 'pet_type',
                'discriminator_value': 'fish',
                'allowed_values': "'cat', 'dog', 'reptile', 'lizard'",
            },
        },
    ]

    with pytest.raises(ValidationError) as exc_info:
        Model.parse_obj({'pet': {'pet_type': 'lizard'}, 'number': 2})
    assert exc_info.value.errors() == [
        {'loc': ('pet', 'Lizard', 'l'), 'msg': 'field required', 'type': 'value_error.missing'},
    ]

    m = Model.parse_obj({'pet': {'pet_type': 'lizard', 'l': 'pika'}, 'number': 2})
    assert isinstance(m.pet, Lizard)
    assert m.dict() == {'pet': {'pet_type': 'lizard', 'l': 'pika'}, 'number': 2}

    with pytest.raises(ValidationError) as exc_info:
        Model.parse_obj({'pet': {'pet_type': 'cat', 'color': 'white'}, 'number': 2})
    assert exc_info.value.errors() == [
        {
            'loc': ('pet', 'Cat', '__root__', 'WhiteCat', 'white_infos'),
            'msg': 'field required',
            'type': 'value_error.missing',
        }
    ]
    m = Model.parse_obj({'pet': {'pet_type': 'cat', 'color': 'white', 'white_infos': 'pika'}, 'number': 2})
    assert isinstance(m.pet.__root__, WhiteCat)


def test_discriminated_annotated_union():
    class BlackCat(BaseModel):
        pet_type: Literal['cat']
        color: Literal['black']
        black_infos: str

    class WhiteCat(BaseModel):
        pet_type: Literal['cat']
        color: Literal['white']
        white_infos: str

    Cat = Annotated[Union[BlackCat, WhiteCat], Field(discriminator='color')]

    class Dog(BaseModel):
        pet_type: Literal['dog']
        dog_name: str

    Pet = Annotated[Union[Cat, Dog], Field(discriminator='pet_type')]

    class Model(BaseModel):
        pet: Pet
        number: int

    with pytest.raises(ValidationError) as exc_info:
        Model.parse_obj({'pet': {'pet_typ': 'cat'}, 'number': 'x'})
    assert exc_info.value.errors() == [
        {
            'loc': ('pet',),
            'msg': "Discriminator 'pet_type' is missing in value",
            'type': 'value_error.discriminated_union.missing_discriminator',
            'ctx': {'discriminator_key': 'pet_type'},
        },
        {'loc': ('number',), 'msg': 'value is not a valid integer', 'type': 'type_error.integer'},
    ]

    with pytest.raises(ValidationError) as exc_info:
        Model.parse_obj({'pet': {'pet_type': 'fish'}, 'number': 2})
    assert exc_info.value.errors() == [
        {
            'loc': ('pet',),
            'msg': "No match for discriminator 'pet_type' and value 'fish' " "(allowed values: 'cat', 'dog')",
            'type': 'value_error.discriminated_union.invalid_discriminator',
            'ctx': {'discriminator_key': 'pet_type', 'discriminator_value': 'fish', 'allowed_values': "'cat', 'dog'"},
        },
    ]

    with pytest.raises(ValidationError) as exc_info:
        Model.parse_obj({'pet': {'pet_type': 'dog'}, 'number': 2})
    assert exc_info.value.errors() == [
        {'loc': ('pet', 'Dog', 'dog_name'), 'msg': 'field required', 'type': 'value_error.missing'},
    ]
    m = Model.parse_obj({'pet': {'pet_type': 'dog', 'dog_name': 'milou'}, 'number': 2})
    assert isinstance(m.pet, Dog)

    with pytest.raises(ValidationError) as exc_info:
        Model.parse_obj({'pet': {'pet_type': 'cat', 'color': 'red'}, 'number': 2})
    assert exc_info.value.errors() == [
        {
            'loc': ('pet', 'Union[BlackCat, WhiteCat]'),
            'msg': "No match for discriminator 'color' and value 'red' " "(allowed values: 'black', 'white')",
            'type': 'value_error.discriminated_union.invalid_discriminator',
            'ctx': {'discriminator_key': 'color', 'discriminator_value': 'red', 'allowed_values': "'black', 'white'"},
        }
    ]

    with pytest.raises(ValidationError) as exc_info:
        Model.parse_obj({'pet': {'pet_type': 'cat', 'color': 'white'}, 'number': 2})
    assert exc_info.value.errors() == [
        {
            'loc': ('pet', 'Union[BlackCat, WhiteCat]', 'WhiteCat', 'white_infos'),
            'msg': 'field required',
            'type': 'value_error.missing',
        }
    ]
    m = Model.parse_obj({'pet': {'pet_type': 'cat', 'color': 'white', 'white_infos': 'pika'}, 'number': 2})
    assert isinstance(m.pet, WhiteCat)


def test_discriminated_union_basemodel_instance_value():
    class A(BaseModel):
        l: Literal['a']

    class B(BaseModel):
        l: Literal['b']

    class Top(BaseModel):
        sub: Union[A, B] = Field(..., discriminator='l')

    t = Top(sub=A(l='a'))
    assert isinstance(t, Top)


def test_discriminated_union_basemodel_instance_value_with_alias():
    class A(BaseModel):
        literal: Literal['a'] = Field(alias='lit')

    class B(BaseModel):
        literal: Literal['b'] = Field(alias='lit')

        class Config:
            allow_population_by_field_name = True

    class Top(BaseModel):
        sub: Union[A, B] = Field(..., discriminator='literal')

    assert Top(sub=A(lit='a')).sub.literal == 'a'
    assert Top(sub=B(lit='b')).sub.literal == 'b'
    assert Top(sub=B(literal='b')).sub.literal == 'b'


def test_discriminated_union_model_with_alias():
    class A(BaseModel):
        literal: Literal['a'] = Field(alias='lit')

    class B(BaseModel):
        literal: Literal['b'] = Field(alias='lit')

        class Config:
            allow_population_by_field_name = True

    class TopDisallow(BaseModel):
        sub: Union[A, B] = Field(..., discriminator='literal', alias='s')

    class TopAllow(BaseModel):
        sub: Union[A, B] = Field(..., discriminator='literal', alias='s')

        class Config:
            allow_population_by_field_name = True

    assert TopDisallow.parse_obj({'s': {'lit': 'a'}}).sub.literal == 'a'

    with pytest.raises(ValidationError) as exc_info:
        TopDisallow.parse_obj({'s': {'literal': 'b'}})

    assert exc_info.value.errors() == [
        {
            'ctx': {'discriminator_key': 'literal'},
            'loc': ('s',),
            'msg': "Discriminator 'literal' is missing in value",
            'type': 'value_error.discriminated_union.missing_discriminator',
        },
    ]

    with pytest.raises(ValidationError) as exc_info:
        TopDisallow.parse_obj({'s': {'literal': 'a'}})

    assert exc_info.value.errors() == [
        {
            'ctx': {'discriminator_key': 'literal'},
            'loc': ('s',),
            'msg': "Discriminator 'literal' is missing in value",
            'type': 'value_error.discriminated_union.missing_discriminator',
        }
    ]

    with pytest.raises(ValidationError) as exc_info:
        TopDisallow.parse_obj({'sub': {'lit': 'a'}})

    assert exc_info.value.errors() == [
        {'loc': ('s',), 'msg': 'field required', 'type': 'value_error.missing'},
    ]

    assert TopAllow.parse_obj({'s': {'lit': 'a'}}).sub.literal == 'a'
    assert TopAllow.parse_obj({'s': {'lit': 'b'}}).sub.literal == 'b'
    assert TopAllow.parse_obj({'s': {'literal': 'b'}}).sub.literal == 'b'
    assert TopAllow.parse_obj({'sub': {'lit': 'a'}}).sub.literal == 'a'
    assert TopAllow.parse_obj({'sub': {'lit': 'b'}}).sub.literal == 'b'
    assert TopAllow.parse_obj({'sub': {'literal': 'b'}}).sub.literal == 'b'

    with pytest.raises(ValidationError) as exc_info:
        TopAllow.parse_obj({'s': {'literal': 'a'}})

    assert exc_info.value.errors() == [
        {'loc': ('s', 'A', 'lit'), 'msg': 'field required', 'type': 'value_error.missing'},
    ]

    with pytest.raises(ValidationError) as exc_info:
        TopAllow.parse_obj({'sub': {'literal': 'a'}})

    assert exc_info.value.errors() == [
        {'loc': ('s', 'A', 'lit'), 'msg': 'field required', 'type': 'value_error.missing'},
    ]


def test_discriminated_union_int():
    class A(BaseModel):
        l: Literal[1]

    class B(BaseModel):
        l: Literal[2]

    class Top(BaseModel):
        sub: Union[A, B] = Field(..., discriminator='l')

    assert isinstance(Top.parse_obj({'sub': {'l': 2}}).sub, B)
    with pytest.raises(ValidationError) as exc_info:
        Top.parse_obj({'sub': {'l': 3}})
    assert exc_info.value.errors() == [
        {
            'loc': ('sub',),
            'msg': "No match for discriminator 'l' and value 3 (allowed values: 1, 2)",
            'type': 'value_error.discriminated_union.invalid_discriminator',
            'ctx': {'discriminator_key': 'l', 'discriminator_value': 3, 'allowed_values': '1, 2'},
        }
    ]


def test_discriminated_union_enum():
    class EnumValue(Enum):
        a = 1
        b = 2

    class A(BaseModel):
        l: Literal[EnumValue.a]

    class B(BaseModel):
        l: Literal[EnumValue.b]

    class Top(BaseModel):
        sub: Union[A, B] = Field(..., discriminator='l')

    assert isinstance(Top.parse_obj({'sub': {'l': EnumValue.b}}).sub, B)
    with pytest.raises(ValidationError) as exc_info:
        Top.parse_obj({'sub': {'l': 3}})
    assert exc_info.value.errors() == [
        {
            'loc': ('sub',),
            'msg': "No match for discriminator 'l' and value 3 (allowed values: <EnumValue.a: 1>, <EnumValue.b: 2>)",
            'type': 'value_error.discriminated_union.invalid_discriminator',
            'ctx': {
                'discriminator_key': 'l',
                'discriminator_value': 3,
                'allowed_values': '<EnumValue.a: 1>, <EnumValue.b: 2>',
            },
        }
    ]


def test_alias_different():
    class Cat(BaseModel):
        pet_type: Literal['cat'] = Field(alias='U')
        c: str

    class Dog(BaseModel):
        pet_type: Literal['dog'] = Field(alias='T')
        d: str

    with pytest.raises(
        ConfigError, match=re.escape("Aliases for discriminator 'pet_type' must be the same (got T, U)")
    ):

        class Model(BaseModel):
            pet: Union[Cat, Dog] = Field(discriminator='pet_type')


def test_alias_same():
    class Cat(BaseModel):
        pet_type: Literal['cat'] = Field(alias='typeOfPet')
        c: str

    class Dog(BaseModel):
        pet_type: Literal['dog'] = Field(alias='typeOfPet')
        d: str

    class Model(BaseModel):
        pet: Union[Cat, Dog] = Field(discriminator='pet_type')

    assert Model(**{'pet': {'typeOfPet': 'dog', 'd': 'milou'}}).pet.pet_type == 'dog'


def test_nested():
    class Cat(BaseModel):
        pet_type: Literal['cat']
        name: str

    class Dog(BaseModel):
        pet_type: Literal['dog']
        name: str

    CommonPet = Annotated[Union[Cat, Dog], Field(discriminator='pet_type')]

    class Lizard(BaseModel):
        pet_type: Literal['reptile', 'lizard']
        name: str

    class Model(BaseModel):
        pet: Union[CommonPet, Lizard] = Field(..., discriminator='pet_type')
        n: int

    assert isinstance(Model(**{'pet': {'pet_type': 'dog', 'name': 'Milou'}, 'n': 5}).pet, Dog)


def test_generic():
    T = TypeVar('T')

    class Success(GenericModel, Generic[T]):
        type: Literal['Success'] = 'Success'
        data: T

    class Failure(BaseModel):
        type: Literal['Failure'] = 'Failure'
        error_message: str

    class Container(GenericModel, Generic[T]):
        result: Union[Success[T], Failure] = Field(discriminator='type')

    with pytest.raises(ValidationError, match="Discriminator 'type' is missing in value"):
        Container[str].parse_obj({'result': {}})

    with pytest.raises(
        ValidationError,
        match=re.escape("No match for discriminator 'type' and value 'Other' (allowed values: 'Success', 'Failure')"),
    ):
        Container[str].parse_obj({'result': {'type': 'Other'}})

    with pytest.raises(
        ValidationError, match=re.escape('Container[str]\nresult -> Success[str] -> data\n  field required')
    ):
        Container[str].parse_obj({'result': {'type': 'Success'}})

    # coercion is done properly
    assert Container[str].parse_obj({'result': {'type': 'Success', 'data': 1}}).result.data == '1'


def test_discriminator_with_unhashable_type():
    """Verify an unhashable discriminator value raises a ValidationError."""

    class Model1(BaseModel):
        target: Literal['t1']
        a: int

    class Model2(BaseModel):
        target: Literal['t2']
        b: int

    class Foo(BaseModel):
        foo: Union[Model1, Model2] = Field(discriminator='target')

    with pytest.raises(ValidationError, match=re.escape("No match for discriminator 'target' and value {}")):
        Foo(**{'foo': {'target': {}}})
