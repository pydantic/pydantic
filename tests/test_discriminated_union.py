import re
import sys
from enum import Enum, IntEnum
from typing import Generic, Optional, TypeVar, Union

import pytest
from dirty_equals import HasRepr, IsStr
from pydantic_core import SchemaValidator, core_schema
from typing_extensions import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field, TypeAdapter, ValidationError
from pydantic._internal._discriminated_union import apply_discriminator
from pydantic.errors import PydanticUserError


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
    with pytest.raises(
        TypeError, match="'str' is not a valid discriminated union variant; should be a `BaseModel` or `dataclass`"
    ):

        class Model(BaseModel):
            x: Union[str, int] = Field(..., discriminator='qwe')


def test_discriminated_union_defined_discriminator():
    class Cat(BaseModel):
        c: str

    class Dog(BaseModel):
        pet_type: Literal['dog']
        d: str

    with pytest.raises(PydanticUserError, match="Model 'Cat' needs a discriminator field for key 'pet_type'"):

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

    with pytest.raises(PydanticUserError, match="Model 'Cat' needs field 'pet_type' to be of type `Literal`"):

        class Model(BaseModel):
            pet: Union[Cat, Dog] = Field(..., discriminator='pet_type')
            number: int


def test_discriminated_union_root_same_discriminator():
    class BlackCat(BaseModel):
        pet_type: Literal['blackcat']

    class WhiteCat(BaseModel):
        pet_type: Literal['whitecat']

    Cat = Union[BlackCat, WhiteCat]

    class Dog(BaseModel):
        pet_type: Literal['dog']

    CatDog = TypeAdapter(Annotated[Union[Cat, Dog], Field(..., discriminator='pet_type')]).validate_python
    CatDog({'pet_type': 'blackcat'})
    CatDog({'pet_type': 'whitecat'})
    CatDog({'pet_type': 'dog'})
    with pytest.raises(ValidationError) as exc_info:
        CatDog({'pet_type': 'llama'})
    assert exc_info.value.errors(include_url=False) == [
        {
            'ctx': {'discriminator': "'pet_type'", 'expected_tags': "'blackcat', 'whitecat', 'dog'", 'tag': 'llama'},
            'input': {'pet_type': 'llama'},
            'loc': (),
            'msg': "Input tag 'llama' found using 'pet_type' does not match any of the "
            "expected tags: 'blackcat', 'whitecat', 'dog'",
            'type': 'union_tag_invalid',
        }
    ]


def test_discriminated_union_validation():
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
        d: str

    class Lizard(BaseModel):
        pet_type: Literal['reptile', 'lizard']
        m: str

    class Model(BaseModel):
        pet: Annotated[Union[Cat, Dog, Lizard], Field(discriminator='pet_type')]
        number: int

    with pytest.raises(ValidationError) as exc_info:
        Model.model_validate({'pet': {'pet_typ': 'cat'}, 'number': 'x'})
    assert exc_info.value.errors(include_url=False) == [
        {
            'ctx': {'discriminator': "'pet_type'"},
            'input': {'pet_typ': 'cat'},
            'loc': ('pet',),
            'msg': "Unable to extract tag using discriminator 'pet_type'",
            'type': 'union_tag_not_found',
        },
        {
            'input': 'x',
            'loc': ('number',),
            'msg': 'Input should be a valid integer, unable to parse string as an ' 'integer',
            'type': 'int_parsing',
        },
    ]

    with pytest.raises(ValidationError) as exc_info:
        Model.model_validate({'pet': 'fish', 'number': 2})
    assert exc_info.value.errors(include_url=False) == [
        {
            'input': 'fish',
            'loc': ('pet',),
            'msg': 'Input should be a valid dictionary or instance to extract fields ' 'from',
            'type': 'dict_attributes_type',
        }
    ]

    with pytest.raises(ValidationError) as exc_info:
        Model.model_validate({'pet': {'pet_type': 'fish'}, 'number': 2})
    assert exc_info.value.errors(include_url=False) == [
        {
            'ctx': {'discriminator': "'pet_type'", 'expected_tags': "'cat', 'dog', 'reptile', 'lizard'", 'tag': 'fish'},
            'input': {'pet_type': 'fish'},
            'loc': ('pet',),
            'msg': "Input tag 'fish' found using 'pet_type' does not match any of the "
            "expected tags: 'cat', 'dog', 'reptile', 'lizard'",
            'type': 'union_tag_invalid',
        }
    ]

    with pytest.raises(ValidationError) as exc_info:
        Model.model_validate({'pet': {'pet_type': 'lizard'}, 'number': 2})
    assert exc_info.value.errors(include_url=False) == [
        {'input': {'pet_type': 'lizard'}, 'loc': ('pet', 'lizard', 'm'), 'msg': 'Field required', 'type': 'missing'}
    ]

    m = Model.model_validate({'pet': {'pet_type': 'lizard', 'm': 'pika'}, 'number': 2})
    assert isinstance(m.pet, Lizard)
    assert m.model_dump() == {'pet': {'pet_type': 'lizard', 'm': 'pika'}, 'number': 2}

    with pytest.raises(ValidationError) as exc_info:
        Model.model_validate({'pet': {'pet_type': 'cat', 'color': 'white'}, 'number': 2})
    assert exc_info.value.errors(include_url=False) == [
        {
            'input': {'color': 'white', 'pet_type': 'cat'},
            'loc': ('pet', 'cat', 'white', 'white_infos'),
            'msg': 'Field required',
            'type': 'missing',
        }
    ]
    m = Model.model_validate({'pet': {'pet_type': 'cat', 'color': 'white', 'white_infos': 'pika'}, 'number': 2})
    assert isinstance(m.pet, WhiteCat)


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
        Model.model_validate({'pet': {'pet_typ': 'cat'}, 'number': 'x'})
    assert exc_info.value.errors(include_url=False) == [
        {
            'ctx': {'discriminator': "'pet_type'"},
            'input': {'pet_typ': 'cat'},
            'loc': ('pet',),
            'msg': "Unable to extract tag using discriminator 'pet_type'",
            'type': 'union_tag_not_found',
        },
        {
            'input': 'x',
            'loc': ('number',),
            'msg': 'Input should be a valid integer, unable to parse string as an ' 'integer',
            'type': 'int_parsing',
        },
    ]

    with pytest.raises(ValidationError) as exc_info:
        Model.model_validate({'pet': {'pet_type': 'fish'}, 'number': 2})
    assert exc_info.value.errors(include_url=False) == [
        {
            'ctx': {'discriminator': "'pet_type'", 'expected_tags': "'cat', 'dog'", 'tag': 'fish'},
            'input': {'pet_type': 'fish'},
            'loc': ('pet',),
            'msg': "Input tag 'fish' found using 'pet_type' does not match any of the " "expected tags: 'cat', 'dog'",
            'type': 'union_tag_invalid',
        }
    ]

    with pytest.raises(ValidationError) as exc_info:
        Model.model_validate({'pet': {'pet_type': 'dog'}, 'number': 2})
    assert exc_info.value.errors(include_url=False) == [
        {'input': {'pet_type': 'dog'}, 'loc': ('pet', 'dog', 'dog_name'), 'msg': 'Field required', 'type': 'missing'}
    ]
    m = Model.model_validate({'pet': {'pet_type': 'dog', 'dog_name': 'milou'}, 'number': 2})
    assert isinstance(m.pet, Dog)

    with pytest.raises(ValidationError) as exc_info:
        Model.model_validate({'pet': {'pet_type': 'cat', 'color': 'red'}, 'number': 2})
    assert exc_info.value.errors(include_url=False) == [
        {
            'ctx': {'discriminator': "'color'", 'expected_tags': "'black', 'white'", 'tag': 'red'},
            'input': {'color': 'red', 'pet_type': 'cat'},
            'loc': ('pet', 'cat'),
            'msg': "Input tag 'red' found using 'color' does not match any of the " "expected tags: 'black', 'white'",
            'type': 'union_tag_invalid',
        }
    ]

    with pytest.raises(ValidationError) as exc_info:
        Model.model_validate({'pet': {'pet_type': 'cat', 'color': 'white'}, 'number': 2})
    assert exc_info.value.errors(include_url=False) == [
        {
            'input': {'color': 'white', 'pet_type': 'cat'},
            'loc': ('pet', 'cat', 'white', 'white_infos'),
            'msg': 'Field required',
            'type': 'missing',
        }
    ]
    m = Model.model_validate({'pet': {'pet_type': 'cat', 'color': 'white', 'white_infos': 'pika'}, 'number': 2})
    assert isinstance(m.pet, WhiteCat)


def test_discriminated_union_basemodel_instance_value():
    class A(BaseModel):
        foo: Literal['a']

    class B(BaseModel):
        foo: Literal['b']

    class Top(BaseModel):
        sub: Union[A, B] = Field(..., discriminator='foo')

    t = Top(sub=A(foo='a'))
    assert isinstance(t, Top)


def test_discriminated_union_basemodel_instance_value_with_alias():
    class A(BaseModel):
        literal: Literal['a'] = Field(alias='lit')

    class B(BaseModel):
        model_config = ConfigDict(populate_by_name=True)
        literal: Literal['b'] = Field(alias='lit')

    class Top(BaseModel):
        sub: Union[A, B] = Field(..., discriminator='literal')

    with pytest.raises(ValidationError) as exc_info:
        Top(sub=A(literal='a'))
    # TODO: Adding this note here that we should make sure the produced error messages for DiscriminatedUnion
    #   have the same behavior as elsewhere when aliases are involved.
    #   (I.e., possibly using the alias value as the 'loc')
    assert exc_info.value.errors(include_url=False) == [
        {'input': {'literal': 'a'}, 'loc': ('lit',), 'msg': 'Field required', 'type': 'missing'}
    ]
    assert Top(sub=A(lit='a')).sub.literal == 'a'
    assert Top(sub=B(lit='b')).sub.literal == 'b'
    assert Top(sub=B(literal='b')).sub.literal == 'b'


def test_discriminated_union_int():
    class A(BaseModel):
        m: Literal[1]

    class B(BaseModel):
        m: Literal[2]

    class Top(BaseModel):
        sub: Union[A, B] = Field(..., discriminator='m')

    assert isinstance(Top.model_validate({'sub': {'m': 2}}).sub, B)
    with pytest.raises(ValidationError) as exc_info:
        Top.model_validate({'sub': {'m': 3}})
    assert exc_info.value.errors(include_url=False) == [
        {
            'ctx': {'discriminator': "'m'", 'expected_tags': '1, 2', 'tag': '3'},
            'input': {'m': 3},
            'loc': ('sub',),
            'msg': "Input tag '3' found using 'm' does not match any of the expected " "tags: 1, 2",
            'type': 'union_tag_invalid',
        }
    ]


class FooIntEnum(int, Enum):
    pass


class FooStrEnum(str, Enum):
    pass


ENUM_TEST_CASES = [
    pytest.param(Enum, {'a': 1, 'b': 2}, marks=pytest.mark.xfail(reason='Plain Enum discriminator not yet supported')),
    pytest.param(
        Enum, {'a': 'v_a', 'b': 'v_b'}, marks=pytest.mark.xfail(reason='Plain Enum discriminator not yet supported')
    ),
    (FooIntEnum, {'a': 1, 'b': 2}),
    (IntEnum, {'a': 1, 'b': 2}),
    (FooStrEnum, {'a': 'v_a', 'b': 'v_b'}),
]
if sys.version_info >= (3, 11):
    from enum import StrEnum

    ENUM_TEST_CASES.append((StrEnum, {'a': 'v_a', 'b': 'v_b'}))


@pytest.mark.xfail(
    sys.version_info[:2] == (3, 8), reason='https://github.com/python/cpython/issues/103592', strict=False
)
@pytest.mark.parametrize('base_class,choices', ENUM_TEST_CASES)
def test_discriminated_union_enum(base_class, choices):
    EnumValue = base_class('EnumValue', choices)

    class A(BaseModel):
        m: Literal[EnumValue.a]

    class B(BaseModel):
        m: Literal[EnumValue.b]

    class Top(BaseModel):
        sub: Union[A, B] = Field(..., discriminator='m')

    assert isinstance(Top.model_validate({'sub': {'m': EnumValue.b}}).sub, B)
    assert isinstance(Top.model_validate({'sub': {'m': EnumValue.b.value}}).sub, B)
    with pytest.raises(ValidationError) as exc_info:
        Top.model_validate({'sub': {'m': 3}})

    expected_tags = f'{EnumValue.a.value!r}, {EnumValue.b.value!r}'
    assert exc_info.value.errors(include_url=False) == [
        {
            'ctx': {'discriminator': "'m'", 'expected_tags': expected_tags, 'tag': '3'},
            'input': {'m': 3},
            'loc': ('sub',),
            'msg': f"Input tag '3' found using 'm' does not match any of the expected tags: {expected_tags}",
            'type': 'union_tag_invalid',
        }
    ]


def test_alias_different():
    class Cat(BaseModel):
        pet_type: Literal['cat'] = Field(alias='U')
        c: str

    class Dog(BaseModel):
        pet_type: Literal['dog'] = Field(alias='T')
        d: str

    with pytest.raises(TypeError, match=re.escape("Aliases for discriminator 'pet_type' must be the same (got T, U)")):

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

    class Success(BaseModel, Generic[T]):
        type: Literal['Success'] = 'Success'
        data: T

    class Failure(BaseModel):
        type: Literal['Failure'] = 'Failure'
        error_message: str

    class Container(BaseModel, Generic[T]):
        result: Union[Success[T], Failure] = Field(discriminator='type')

    with pytest.raises(ValidationError, match="Unable to extract tag using discriminator 'type'"):
        Container[str].model_validate({'result': {}})

    with pytest.raises(
        ValidationError,
        match=re.escape(
            "Input tag 'Other' found using 'type' does not match any of the expected tags: 'Success', 'Failure'"
        ),
    ):
        Container[str].model_validate({'result': {'type': 'Other'}})

    with pytest.raises(ValidationError, match=r'Container\[str\]\nresult\.Success\.data') as exc_info:
        Container[str].model_validate({'result': {'type': 'Success'}})
    assert exc_info.value.errors(include_url=False) == [
        {'input': {'type': 'Success'}, 'loc': ('result', 'Success', 'data'), 'msg': 'Field required', 'type': 'missing'}
    ]

    # invalid types error
    with pytest.raises(ValidationError) as exc_info:
        Container[str].model_validate({'result': {'type': 'Success', 'data': 1}})
    assert exc_info.value.errors(include_url=False) == [
        {
            'input': 1,
            'loc': ('result', 'Success', 'data'),
            'msg': 'Input should be a valid string',
            'type': 'string_type',
        }
    ]

    assert Container[str].model_validate({'result': {'type': 'Success', 'data': '1'}}).result.data == '1'


def test_optional_union():
    class Cat(BaseModel):
        pet_type: Literal['cat']
        name: str

    class Dog(BaseModel):
        pet_type: Literal['dog']
        name: str

    class Pet(BaseModel):
        pet: Optional[Union[Cat, Dog]] = Field(discriminator='pet_type')

    assert Pet(pet={'pet_type': 'cat', 'name': 'Milo'}).model_dump() == {'pet': {'name': 'Milo', 'pet_type': 'cat'}}
    assert Pet(pet={'pet_type': 'dog', 'name': 'Otis'}).model_dump() == {'pet': {'name': 'Otis', 'pet_type': 'dog'}}
    assert Pet(pet=None).model_dump() == {'pet': None}

    with pytest.raises(ValidationError) as exc_info:
        Pet()
    assert exc_info.value.errors(include_url=False) == [
        {'input': {}, 'loc': ('pet',), 'msg': 'Field required', 'type': 'missing'}
    ]

    with pytest.raises(ValidationError) as exc_info:
        Pet(pet={'name': 'Benji'})
    assert exc_info.value.errors(include_url=False) == [
        {
            'ctx': {'discriminator': "'pet_type'"},
            'input': {'name': 'Benji'},
            'loc': ('pet',),
            'msg': "Unable to extract tag using discriminator 'pet_type'",
            'type': 'union_tag_not_found',
        }
    ]

    with pytest.raises(ValidationError) as exc_info:
        Pet(pet={'pet_type': 'lizard'})
    assert exc_info.value.errors(include_url=False) == [
        {
            'ctx': {'discriminator': "'pet_type'", 'expected_tags': "'cat', 'dog'", 'tag': 'lizard'},
            'input': {'pet_type': 'lizard'},
            'loc': ('pet',),
            'msg': "Input tag 'lizard' found using 'pet_type' does not match any of the " "expected tags: 'cat', 'dog'",
            'type': 'union_tag_invalid',
        }
    ]


def test_optional_union_with_defaults():
    class Cat(BaseModel):
        pet_type: Literal['cat'] = 'cat'
        name: str

    class Dog(BaseModel):
        pet_type: Literal['dog'] = 'dog'
        name: str

    class Pet(BaseModel):
        pet: Optional[Union[Cat, Dog]] = Field(default=None, discriminator='pet_type')

    assert Pet(pet={'pet_type': 'cat', 'name': 'Milo'}).model_dump() == {'pet': {'name': 'Milo', 'pet_type': 'cat'}}
    assert Pet(pet={'pet_type': 'dog', 'name': 'Otis'}).model_dump() == {'pet': {'name': 'Otis', 'pet_type': 'dog'}}
    assert Pet(pet=None).model_dump() == {'pet': None}
    assert Pet().model_dump() == {'pet': None}

    with pytest.raises(ValidationError) as exc_info:
        Pet(pet={'name': 'Benji'})
    assert exc_info.value.errors(include_url=False) == [
        {
            'ctx': {'discriminator': "'pet_type'"},
            'input': {'name': 'Benji'},
            'loc': ('pet',),
            'msg': "Unable to extract tag using discriminator 'pet_type'",
            'type': 'union_tag_not_found',
        }
    ]

    with pytest.raises(ValidationError) as exc_info:
        Pet(pet={'pet_type': 'lizard'})
    assert exc_info.value.errors(include_url=False) == [
        {
            'ctx': {'discriminator': "'pet_type'", 'expected_tags': "'cat', 'dog'", 'tag': 'lizard'},
            'input': {'pet_type': 'lizard'},
            'loc': ('pet',),
            'msg': "Input tag 'lizard' found using 'pet_type' does not match any of the " "expected tags: 'cat', 'dog'",
            'type': 'union_tag_invalid',
        }
    ]


def test_aliases_matching_is_not_sufficient() -> None:
    class Case1(BaseModel):
        kind_one: Literal['1'] = Field(alias='kind')

    class Case2(BaseModel):
        kind_two: Literal['2'] = Field(alias='kind')

    with pytest.raises(PydanticUserError, match="Model 'Case1' needs a discriminator field for key 'kind'"):

        class TaggedParent(BaseModel):
            tagged: Union[Case1, Case2] = Field(discriminator='kind')


def test_nested_optional_unions() -> None:
    class Cat(BaseModel):
        pet_type: Literal['cat'] = 'cat'

    class Dog(BaseModel):
        pet_type: Literal['dog'] = 'dog'

    class Lizard(BaseModel):
        pet_type: Literal['lizard', 'reptile'] = 'lizard'

    MaybeCatDog = Annotated[Optional[Union[Cat, Dog]], Field(discriminator='pet_type')]
    MaybeDogLizard = Annotated[Union[Dog, Lizard, None], Field(discriminator='pet_type')]

    class Pet(BaseModel):
        pet: Union[MaybeCatDog, MaybeDogLizard] = Field(discriminator='pet_type')

    Pet.model_validate({'pet': {'pet_type': 'dog'}})
    Pet.model_validate({'pet': {'pet_type': 'cat'}})
    Pet.model_validate({'pet': {'pet_type': 'lizard'}})
    Pet.model_validate({'pet': {'pet_type': 'reptile'}})
    Pet.model_validate({'pet': None})

    with pytest.raises(ValidationError) as exc_info:
        Pet.model_validate({'pet': {'pet_type': None}})
    assert exc_info.value.errors(include_url=False) == [
        {'input': None, 'loc': ('pet',), 'msg': 'Input should be a valid string', 'type': 'string_type'}
    ]

    with pytest.raises(ValidationError) as exc_info:
        Pet.model_validate({'pet': {'pet_type': 'fox'}})
    assert exc_info.value.errors(include_url=False) == [
        {
            'ctx': {'discriminator': "'pet_type'", 'expected_tags': "'cat', 'dog', 'lizard', 'reptile'", 'tag': 'fox'},
            'input': {'pet_type': 'fox'},
            'loc': ('pet',),
            'msg': "Input tag 'fox' found using 'pet_type' does not match any of the "
            "expected tags: 'cat', 'dog', 'lizard', 'reptile'",
            'type': 'union_tag_invalid',
        }
    ]


def test_nested_discriminated_union() -> None:
    class Cat(BaseModel):
        pet_type: Literal['cat', 'CAT']

    class Dog(BaseModel):
        pet_type: Literal['dog', 'DOG']

    class Lizard(BaseModel):
        pet_type: Literal['lizard', 'LIZARD']

    CatDog = Annotated[Union[Cat, Dog], Field(discriminator='pet_type')]
    CatDogLizard = Annotated[Union[CatDog, Lizard], Field(discriminator='pet_type')]

    class Pet(BaseModel):
        pet: CatDogLizard

    Pet.model_validate({'pet': {'pet_type': 'dog'}})
    Pet.model_validate({'pet': {'pet_type': 'cat'}})
    Pet.model_validate({'pet': {'pet_type': 'lizard'}})

    with pytest.raises(ValidationError) as exc_info:
        Pet.model_validate({'pet': {'pet_type': 'reptile'}})
    assert exc_info.value.errors(include_url=False) == [
        {
            'ctx': {
                'discriminator': "'pet_type'",
                'expected_tags': "'cat', 'dog', 'lizard', 'CAT', 'DOG', 'LIZARD'",
                'tag': 'reptile',
            },
            'input': {'pet_type': 'reptile'},
            'loc': ('pet',),
            'msg': "Input tag 'reptile' found using 'pet_type' does not match any of the "
            "expected tags: 'cat', 'dog', 'lizard', 'CAT', 'DOG', 'LIZARD'",
            'type': 'union_tag_invalid',
        }
    ]


def test_unions_of_optionals() -> None:
    class Cat(BaseModel):
        pet_type: Literal['cat'] = Field(alias='typeOfPet')
        c: str

    class Dog(BaseModel):
        pet_type: Literal['dog'] = Field(alias='typeOfPet')
        d: str

    class Lizard(BaseModel):
        pet_type: Literal['lizard'] = Field(alias='typeOfPet')

    MaybeCat = Annotated[Union[Cat, None], 'some annotation']
    MaybeDogLizard = Annotated[Optional[Union[Dog, Lizard]], 'some other annotation']

    class Model(BaseModel):
        maybe_pet: Union[MaybeCat, MaybeDogLizard] = Field(discriminator='pet_type')

    assert Model(**{'maybe_pet': None}).maybe_pet is None
    assert Model(**{'maybe_pet': {'typeOfPet': 'dog', 'd': 'milou'}}).maybe_pet.pet_type == 'dog'
    assert Model(**{'maybe_pet': {'typeOfPet': 'lizard'}}).maybe_pet.pet_type == 'lizard'


def test_union_discriminator_literals() -> None:
    class Cat(BaseModel):
        pet_type: Union[Literal['cat'], Literal['CAT']] = Field(alias='typeOfPet')

    class Dog(BaseModel):
        pet_type: Literal['dog'] = Field(alias='typeOfPet')

    class Model(BaseModel):
        pet: Union[Cat, Dog] = Field(discriminator='pet_type')

    assert Model(**{'pet': {'typeOfPet': 'dog'}}).pet.pet_type == 'dog'
    assert Model(**{'pet': {'typeOfPet': 'cat'}}).pet.pet_type == 'cat'
    assert Model(**{'pet': {'typeOfPet': 'CAT'}}).pet.pet_type == 'CAT'
    with pytest.raises(ValidationError) as exc_info:
        Model(**{'pet': {'typeOfPet': 'Cat'}})
    assert exc_info.value.errors(include_url=False) == [
        {
            'ctx': {'discriminator': "'pet_type' | 'typeOfPet'", 'expected_tags': "'cat', 'dog', 'CAT'", 'tag': 'Cat'},
            'input': {'typeOfPet': 'Cat'},
            'loc': ('pet',),
            'msg': "Input tag 'Cat' found using 'pet_type' | 'typeOfPet' does not match "
            "any of the expected tags: 'cat', 'dog', 'CAT'",
            'type': 'union_tag_invalid',
        }
    ]


def test_none_schema() -> None:
    cat_fields = {'kind': core_schema.typed_dict_field(core_schema.literal_schema(['cat']))}
    dog_fields = {'kind': core_schema.typed_dict_field(core_schema.literal_schema(['dog']))}
    cat = core_schema.typed_dict_schema(cat_fields)
    dog = core_schema.typed_dict_schema(dog_fields)
    schema = core_schema.union_schema([cat, dog, core_schema.none_schema()])
    schema = apply_discriminator(schema, 'kind')
    validator = SchemaValidator(schema)
    assert validator.validate_python({'kind': 'cat'})['kind'] == 'cat'
    assert validator.validate_python({'kind': 'dog'})['kind'] == 'dog'
    assert validator.validate_python(None) is None
    with pytest.raises(ValidationError) as exc_info:
        validator.validate_python({'kind': 'lizard'})
    assert exc_info.value.errors(include_url=False) == [
        {
            'ctx': {'discriminator': "'kind'", 'expected_tags': "'cat', 'dog'", 'tag': 'lizard'},
            'input': {'kind': 'lizard'},
            'loc': (),
            'msg': "Input tag 'lizard' found using 'kind' does not match any of the " "expected tags: 'cat', 'dog'",
            'type': 'union_tag_invalid',
        }
    ]


def test_nested_unwrapping() -> None:
    cat_fields = {'kind': core_schema.typed_dict_field(core_schema.literal_schema(['cat']))}
    dog_fields = {'kind': core_schema.typed_dict_field(core_schema.literal_schema(['dog']))}
    cat = core_schema.typed_dict_schema(cat_fields)
    dog = core_schema.typed_dict_schema(dog_fields)
    schema = core_schema.union_schema([cat, dog])
    for _ in range(3):
        schema = core_schema.nullable_schema(schema)
        schema = core_schema.nullable_schema(schema)
        schema = core_schema.definitions_schema(schema, [])
        schema = core_schema.definitions_schema(schema, [])

    schema = apply_discriminator(schema, 'kind')

    validator = SchemaValidator(schema)
    assert validator.validate_python({'kind': 'cat'})['kind'] == 'cat'
    assert validator.validate_python({'kind': 'dog'})['kind'] == 'dog'
    assert validator.validate_python(None) is None
    with pytest.raises(ValidationError) as exc_info:
        validator.validate_python({'kind': 'lizard'})
    assert exc_info.value.errors(include_url=False) == [
        {
            'ctx': {'discriminator': "'kind'", 'expected_tags': "'cat', 'dog'", 'tag': 'lizard'},
            'input': {'kind': 'lizard'},
            'loc': (),
            'msg': "Input tag 'lizard' found using 'kind' does not match any of the " "expected tags: 'cat', 'dog'",
            'type': 'union_tag_invalid',
        }
    ]


def test_distinct_choices() -> None:
    class Cat(BaseModel):
        pet_type: Literal['cat', 'dog'] = Field(alias='typeOfPet')

    class Dog(BaseModel):
        pet_type: Literal['dog'] = Field(alias='typeOfPet')

    with pytest.raises(TypeError, match="Value 'dog' for discriminator 'pet_type' mapped to multiple choices"):

        class Model(BaseModel):
            pet: Union[Cat, Dog] = Field(discriminator='pet_type')


def test_invalid_discriminated_union_type() -> None:
    class Cat(BaseModel):
        pet_type: Literal['cat'] = Field(alias='typeOfPet')

    class Dog(BaseModel):
        pet_type: Literal['dog'] = Field(alias='typeOfPet')

    with pytest.raises(
        TypeError, match="'str' is not a valid discriminated union variant; should be a `BaseModel` or `dataclass`"
    ):

        class Model(BaseModel):
            pet: Union[Cat, Dog, str] = Field(discriminator='pet_type')


def test_single_item_union_error() -> None:
    fields = {'kind': core_schema.typed_dict_field(core_schema.literal_schema(['only_choice']))}
    schema = core_schema.union_schema([core_schema.typed_dict_schema(fields=fields)])
    with pytest.raises(
        TypeError, match='`discriminator` can only be used with `Union` type with more than one variant'
    ):
        apply_discriminator(schema, 'kind')


def test_invalid_alias() -> None:
    cat_fields = {
        'kind': core_schema.typed_dict_field(core_schema.literal_schema(['cat']), validation_alias=['cat', 'CAT'])
    }
    dog_fields = {'kind': core_schema.typed_dict_field(core_schema.literal_schema(['dog']))}
    cat = core_schema.typed_dict_schema(cat_fields)
    dog = core_schema.typed_dict_schema(dog_fields)
    schema = core_schema.union_schema([cat, dog])

    with pytest.raises(TypeError, match=re.escape("Alias ['cat', 'CAT'] is not supported in a discriminated union")):
        apply_discriminator(schema, 'kind')


def test_invalid_discriminator_type() -> None:
    cat_fields = {'kind': core_schema.typed_dict_field(core_schema.int_schema())}
    dog_fields = {'kind': core_schema.typed_dict_field(core_schema.str_schema())}
    cat = core_schema.typed_dict_schema(cat_fields)
    dog = core_schema.typed_dict_schema(dog_fields)

    with pytest.raises(TypeError, match=re.escape("TypedDict needs field 'kind' to be of type `Literal`")):
        apply_discriminator(core_schema.union_schema([cat, dog]), 'kind')


def test_missing_discriminator_field() -> None:
    cat_fields = {'kind': core_schema.typed_dict_field(core_schema.int_schema())}
    dog_fields = {}
    cat = core_schema.typed_dict_schema(cat_fields)
    dog = core_schema.typed_dict_schema(dog_fields)

    with pytest.raises(TypeError, match=re.escape("TypedDict needs a discriminator field for key 'kind'")):
        apply_discriminator(core_schema.union_schema([dog, cat]), 'kind')


def test_invalid_discriminator_value() -> None:
    cat_fields = {'kind': core_schema.typed_dict_field(core_schema.literal_schema([None]))}
    dog_fields = {'kind': core_schema.typed_dict_field(core_schema.literal_schema([1.5]))}
    cat = core_schema.typed_dict_schema(cat_fields)
    dog = core_schema.typed_dict_schema(dog_fields)

    with pytest.raises(TypeError, match=re.escape('Unsupported value for discriminator field: None')):
        apply_discriminator(core_schema.union_schema([cat, dog]), 'kind')

    with pytest.raises(TypeError, match=re.escape('Unsupported value for discriminator field: 1.5')):
        apply_discriminator(core_schema.union_schema([dog, cat]), 'kind')


def test_wrap_function_schema() -> None:
    cat_fields = {'kind': core_schema.typed_dict_field(core_schema.literal_schema(['cat']))}
    dog_fields = {'kind': core_schema.typed_dict_field(core_schema.literal_schema(['dog']))}
    cat = core_schema.general_wrap_validator_function(lambda x, y, z: None, core_schema.typed_dict_schema(cat_fields))
    dog = core_schema.typed_dict_schema(dog_fields)
    schema = core_schema.union_schema([cat, dog])

    assert apply_discriminator(schema, 'kind') == {
        'choices': {
            'cat': {
                'function': {
                    'type': 'general',
                    'function': HasRepr(IsStr(regex=r'<function [a-z_]*\.<locals>\.<lambda> at 0x[0-9a-fA-F]+>')),
                },
                'schema': {
                    'fields': {
                        'kind': {'schema': {'expected': ['cat'], 'type': 'literal'}, 'type': 'typed-dict-field'}
                    },
                    'type': 'typed-dict',
                },
                'type': 'function-wrap',
            },
            'dog': {
                'fields': {'kind': {'schema': {'expected': ['dog'], 'type': 'literal'}, 'type': 'typed-dict-field'}},
                'type': 'typed-dict',
            },
        },
        'discriminator': 'kind',
        'from_attributes': True,
        'strict': False,
        'type': 'tagged-union',
    }


def test_plain_function_schema_is_invalid() -> None:
    with pytest.raises(
        TypeError,
        match="'function-plain' is not a valid discriminated union variant; " "should be a `BaseModel` or `dataclass`",
    ):
        apply_discriminator(
            core_schema.union_schema(
                [core_schema.general_plain_validator_function(lambda x, y: None), core_schema.int_schema()]
            ),
            'kind',
        )


def test_invalid_str_choice_discriminator_values() -> None:
    cat = core_schema.typed_dict_schema({'kind': core_schema.typed_dict_field(core_schema.literal_schema(['cat']))})
    dog = core_schema.str_schema()

    schema = core_schema.union_schema(
        [
            cat,
            # NOTE: Wrapping the union with a validator results in failure to more thoroughly decompose the tagged
            # union. I think this would be difficult to avoid in the general case, and I would suggest that we not
            # attempt to do more than this until presented with scenarios where it is helpful/necessary.
            core_schema.general_wrap_validator_function(lambda x, y, z: x, dog),
        ]
    )

    with pytest.raises(
        TypeError, match="'str' is not a valid discriminated union variant; should be a `BaseModel` or `dataclass`"
    ):
        apply_discriminator(schema, 'kind')


def test_lax_or_strict_definitions() -> None:
    cat = core_schema.typed_dict_schema({'kind': core_schema.typed_dict_field(core_schema.literal_schema(['cat']))})
    lax_dog = core_schema.typed_dict_schema({'kind': core_schema.typed_dict_field(core_schema.literal_schema(['DOG']))})
    strict_dog = core_schema.definitions_schema(
        core_schema.typed_dict_schema({'kind': core_schema.typed_dict_field(core_schema.literal_schema(['dog']))}),
        [core_schema.int_schema(ref='my-int-definition')],
    )
    dog = core_schema.definitions_schema(
        core_schema.lax_or_strict_schema(lax_schema=lax_dog, strict_schema=strict_dog),
        [core_schema.str_schema(ref='my-str-definition')],
    )
    discriminated_schema = apply_discriminator(core_schema.union_schema([cat, dog]), 'kind')
    assert discriminated_schema == {
        'definitions': [{'ref': 'my-str-definition', 'type': 'str'}],
        'schema': {
            'choices': {
                'DOG': {
                    'lax_schema': {
                        'fields': {
                            'kind': {'schema': {'expected': ['DOG'], 'type': 'literal'}, 'type': 'typed-dict-field'}
                        },
                        'type': 'typed-dict',
                    },
                    'strict_schema': {
                        'definitions': [{'ref': 'my-int-definition', 'type': 'int'}],
                        'schema': {
                            'fields': {
                                'kind': {'schema': {'expected': ['dog'], 'type': 'literal'}, 'type': 'typed-dict-field'}
                            },
                            'type': 'typed-dict',
                        },
                        'type': 'definitions',
                    },
                    'type': 'lax-or-strict',
                },
                'cat': {
                    'fields': {
                        'kind': {'schema': {'expected': ['cat'], 'type': 'literal'}, 'type': 'typed-dict-field'}
                    },
                    'type': 'typed-dict',
                },
                'dog': 'DOG',
            },
            'discriminator': 'kind',
            'from_attributes': True,
            'strict': False,
            'type': 'tagged-union',
        },
        'type': 'definitions',
    }


def test_wrapped_nullable_union() -> None:
    cat = core_schema.typed_dict_schema({'kind': core_schema.typed_dict_field(core_schema.literal_schema(['cat']))})
    dog = core_schema.typed_dict_schema({'kind': core_schema.typed_dict_field(core_schema.literal_schema(['dog']))})
    ant = core_schema.typed_dict_schema({'kind': core_schema.typed_dict_field(core_schema.literal_schema(['ant']))})

    schema = core_schema.union_schema(
        [
            ant,
            # NOTE: Wrapping the union with a validator results in failure to more thoroughly decompose the tagged
            # union. I think this would be difficult to avoid in the general case, and I would suggest that we not
            # attempt to do more than this until presented with scenarios where it is helpful/necessary.
            core_schema.general_wrap_validator_function(
                lambda x, y, z: x, core_schema.nullable_schema(core_schema.union_schema([cat, dog]))
            ),
        ]
    )
    discriminated_schema = apply_discriminator(schema, 'kind')
    validator = SchemaValidator(discriminated_schema)
    assert validator.validate_python({'kind': 'ant'})['kind'] == 'ant'
    assert validator.validate_python({'kind': 'cat'})['kind'] == 'cat'
    assert validator.validate_python(None) is None
    with pytest.raises(ValidationError) as exc_info:
        validator.validate_python({'kind': 'armadillo'})
    assert exc_info.value.errors(include_url=False) == [
        {
            'ctx': {'discriminator': "'kind'", 'expected_tags': "'ant', 'cat', 'dog'", 'tag': 'armadillo'},
            'input': {'kind': 'armadillo'},
            'loc': (),
            'msg': "Input tag 'armadillo' found using 'kind' does not match any of the "
            "expected tags: 'ant', 'cat', 'dog'",
            'type': 'union_tag_invalid',
        }
    ]

    assert discriminated_schema == {
        'schema': {
            'choices': {
                'ant': {
                    'fields': {
                        'kind': {'schema': {'expected': ['ant'], 'type': 'literal'}, 'type': 'typed-dict-field'}
                    },
                    'type': 'typed-dict',
                },
                'cat': {
                    'function': {
                        'function': HasRepr(IsStr(regex=r'<function [a-z_]*\.<locals>\.<lambda> at 0x[0-9a-fA-F]+>')),
                        'type': 'general',
                    },
                    'schema': {
                        'schema': {
                            'choices': [
                                {
                                    'fields': {
                                        'kind': {
                                            'schema': {'expected': ['cat'], 'type': 'literal'},
                                            'type': 'typed-dict-field',
                                        }
                                    },
                                    'type': 'typed-dict',
                                },
                                {
                                    'fields': {
                                        'kind': {
                                            'schema': {'expected': ['dog'], 'type': 'literal'},
                                            'type': 'typed-dict-field',
                                        }
                                    },
                                    'type': 'typed-dict',
                                },
                            ],
                            'type': 'union',
                        },
                        'type': 'nullable',
                    },
                    'type': 'function-wrap',
                },
                'dog': 'cat',
            },
            'discriminator': 'kind',
            'from_attributes': True,
            'strict': False,
            'type': 'tagged-union',
        },
        'type': 'nullable',
    }
