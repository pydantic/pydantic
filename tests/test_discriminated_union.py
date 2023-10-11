import re
import sys
from enum import Enum, IntEnum
from typing import Generic, Optional, Sequence, TypeVar, Union

import pytest
from dirty_equals import HasRepr, IsStr
from pydantic_core import SchemaValidator, core_schema
from typing_extensions import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field, TypeAdapter, ValidationError, field_validator
from pydantic._internal._discriminated_union import apply_discriminator
from pydantic.errors import PydanticUserError


def test_discriminated_union_type():
    with pytest.raises(
        TypeError, match="'str' is not a valid discriminated union variant; should be a `BaseModel` or `dataclass`"
    ):

        class Model(BaseModel):
            x: str = Field(..., discriminator='qwe')


@pytest.mark.parametrize('union', [True, False])
def test_discriminated_single_variant(union):
    class InnerModel(BaseModel):
        qwe: Literal['qwe']
        y: int

    class Model(BaseModel):
        if union:
            x: Union[InnerModel] = Field(..., discriminator='qwe')
        else:
            x: InnerModel = Field(..., discriminator='qwe')

    assert Model(x={'qwe': 'qwe', 'y': 1}).x.qwe == 'qwe'
    with pytest.raises(ValidationError) as exc_info:
        Model(x={'qwe': 'asd', 'y': 'a'})  # note: incorrect type of "y" is not reported due to discriminator failure
    assert exc_info.value.errors(include_url=False) == [
        {
            'ctx': {'discriminator': "'qwe'", 'expected_tags': "'qwe'", 'tag': 'asd'},
            'input': {'qwe': 'asd', 'y': 'a'},
            'loc': ('x',),
            'msg': "Input tag 'asd' found using 'qwe' does not match any of the expected " "tags: 'qwe'",
            'type': 'union_tag_invalid',
        }
    ]


def test_discriminated_union_single_variant():
    class InnerModel(BaseModel):
        qwe: Literal['qwe']

    class Model(BaseModel):
        x: Union[InnerModel] = Field(..., discriminator='qwe')

    assert Model(x={'qwe': 'qwe'}).x.qwe == 'qwe'


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
    # insert_assert(exc_info.value.errors(include_url=False))
    assert exc_info.value.errors(include_url=False) == [
        {
            'type': 'model_attributes_type',
            'loc': ('pet',),
            'msg': 'Input should be a valid dictionary or object to extract fields from',
            'input': 'fish',
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
    pytest.param(Enum, {'a': 1, 'b': 2}),
    pytest.param(Enum, {'a': 'v_a', 'b': 'v_b'}),
    (FooIntEnum, {'a': 1, 'b': 2}),
    (IntEnum, {'a': 1, 'b': 2}),
    (FooStrEnum, {'a': 'v_a', 'b': 'v_b'}),
]
if sys.version_info >= (3, 11):
    from enum import StrEnum

    ENUM_TEST_CASES.append((StrEnum, {'a': 'v_a', 'b': 'v_b'}))


@pytest.mark.skipif(sys.version_info[:2] == (3, 8), reason='https://github.com/python/cpython/issues/103592')
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
    if isinstance(EnumValue.b, (int, str)):
        assert isinstance(Top.model_validate({'sub': {'m': EnumValue.b.value}}).sub, B)
    with pytest.raises(ValidationError) as exc_info:
        Top.model_validate({'sub': {'m': 3}})

    expected_tags = f'{EnumValue.a!r}, {EnumValue.b!r}'
    # insert_assert(exc_info.value.errors(include_url=False))
    assert exc_info.value.errors(include_url=False) == [
        {
            'type': 'union_tag_invalid',
            'loc': ('sub',),
            'msg': f"Input tag '3' found using 'm' does not match any of the expected tags: {expected_tags}",
            'input': {'m': 3},
            'ctx': {'discriminator': "'m'", 'tag': '3', 'expected_tags': expected_tags},
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
    # insert_assert(exc_info.value.errors(include_url=False))
    assert exc_info.value.errors(include_url=False) == [
        {
            'type': 'union_tag_invalid',
            'loc': ('pet',),
            'msg': "Input tag 'None' found using 'pet_type' does not match any of the expected tags: 'cat', 'dog', 'lizard', 'reptile'",
            'input': {'pet_type': None},
            'ctx': {'discriminator': "'pet_type'", 'tag': 'None', 'expected_tags': "'cat', 'dog', 'lizard', 'reptile'"},
        }
    ]

    with pytest.raises(ValidationError) as exc_info:
        Pet.model_validate({'pet': {'pet_type': 'fox'}})
    # insert_assert(exc_info.value.errors(include_url=False))
    assert exc_info.value.errors(include_url=False) == [
        {
            'type': 'union_tag_invalid',
            'loc': ('pet',),
            'msg': "Input tag 'fox' found using 'pet_type' does not match any of the expected tags: 'cat', 'dog', 'lizard', 'reptile'",
            'input': {'pet_type': 'fox'},
            'ctx': {'discriminator': "'pet_type'", 'tag': 'fox', 'expected_tags': "'cat', 'dog', 'lizard', 'reptile'"},
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
    # insert_assert(exc_info.value.errors(include_url=False))
    assert exc_info.value.errors(include_url=False) == [
        {
            'type': 'union_tag_invalid',
            'loc': ('pet',),
            'msg': "Input tag 'reptile' found using 'pet_type' does not match any of the expected tags: 'cat', 'CAT', 'dog', 'DOG', 'lizard', 'LIZARD'",
            'input': {'pet_type': 'reptile'},
            'ctx': {
                'discriminator': "'pet_type'",
                'tag': 'reptile',
                'expected_tags': "'cat', 'CAT', 'dog', 'DOG', 'lizard', 'LIZARD'",
            },
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
    # insert_assert(exc_info.value.errors(include_url=False))
    assert exc_info.value.errors(include_url=False) == [
        {
            'type': 'union_tag_invalid',
            'loc': ('pet',),
            'msg': "Input tag 'Cat' found using 'pet_type' | 'typeOfPet' does not match any of the expected tags: 'cat', 'CAT', 'dog'",
            'input': {'typeOfPet': 'Cat'},
            'ctx': {'discriminator': "'pet_type' | 'typeOfPet'", 'tag': 'Cat', 'expected_tags': "'cat', 'CAT', 'dog'"},
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


def test_wrap_function_schema() -> None:
    cat_fields = {'kind': core_schema.typed_dict_field(core_schema.literal_schema(['cat']))}
    dog_fields = {'kind': core_schema.typed_dict_field(core_schema.literal_schema(['dog']))}
    cat = core_schema.with_info_wrap_validator_function(lambda x, y, z: None, core_schema.typed_dict_schema(cat_fields))
    dog = core_schema.typed_dict_schema(dog_fields)
    schema = core_schema.union_schema([cat, dog])

    assert apply_discriminator(schema, 'kind') == {
        'choices': {
            'cat': {
                'function': {
                    'type': 'with-info',
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
                [core_schema.with_info_plain_validator_function(lambda x, y: None), core_schema.int_schema()]
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
            core_schema.with_info_wrap_validator_function(lambda x, y, z: x, dog),
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
    # insert_assert(discriminated_schema)
    assert discriminated_schema == {
        'type': 'definitions',
        'schema': {
            'type': 'tagged-union',
            'choices': {
                'cat': {
                    'type': 'typed-dict',
                    'fields': {
                        'kind': {'type': 'typed-dict-field', 'schema': {'type': 'literal', 'expected': ['cat']}}
                    },
                },
                'DOG': {
                    'type': 'lax-or-strict',
                    'lax_schema': {
                        'type': 'typed-dict',
                        'fields': {
                            'kind': {'type': 'typed-dict-field', 'schema': {'type': 'literal', 'expected': ['DOG']}}
                        },
                    },
                    'strict_schema': {
                        'type': 'definitions',
                        'schema': {
                            'type': 'typed-dict',
                            'fields': {
                                'kind': {'type': 'typed-dict-field', 'schema': {'type': 'literal', 'expected': ['dog']}}
                            },
                        },
                        'definitions': [{'type': 'int', 'ref': 'my-int-definition'}],
                    },
                },
                'dog': {
                    'type': 'lax-or-strict',
                    'lax_schema': {
                        'type': 'typed-dict',
                        'fields': {
                            'kind': {'type': 'typed-dict-field', 'schema': {'type': 'literal', 'expected': ['DOG']}}
                        },
                    },
                    'strict_schema': {
                        'type': 'definitions',
                        'schema': {
                            'type': 'typed-dict',
                            'fields': {
                                'kind': {'type': 'typed-dict-field', 'schema': {'type': 'literal', 'expected': ['dog']}}
                            },
                        },
                        'definitions': [{'type': 'int', 'ref': 'my-int-definition'}],
                    },
                },
            },
            'discriminator': 'kind',
            'strict': False,
            'from_attributes': True,
        },
        'definitions': [{'type': 'str', 'ref': 'my-str-definition'}],
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
            core_schema.with_info_wrap_validator_function(
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

    # insert_assert(discriminated_schema)
    assert discriminated_schema == {
        'type': 'nullable',
        'schema': {
            'type': 'tagged-union',
            'choices': {
                'ant': {
                    'type': 'typed-dict',
                    'fields': {
                        'kind': {'type': 'typed-dict-field', 'schema': {'type': 'literal', 'expected': ['ant']}}
                    },
                },
                'cat': {
                    'type': 'function-wrap',
                    'function': {
                        'type': 'with-info',
                        'function': HasRepr(IsStr(regex=r'<function [a-z_]*\.<locals>\.<lambda> at 0x[0-9a-fA-F]+>')),
                    },
                    'schema': {
                        'type': 'nullable',
                        'schema': {
                            'type': 'union',
                            'choices': [
                                {
                                    'type': 'typed-dict',
                                    'fields': {
                                        'kind': {
                                            'type': 'typed-dict-field',
                                            'schema': {'type': 'literal', 'expected': ['cat']},
                                        }
                                    },
                                },
                                {
                                    'type': 'typed-dict',
                                    'fields': {
                                        'kind': {
                                            'type': 'typed-dict-field',
                                            'schema': {'type': 'literal', 'expected': ['dog']},
                                        }
                                    },
                                },
                            ],
                        },
                    },
                },
                'dog': {
                    'type': 'function-wrap',
                    'function': {
                        'type': 'with-info',
                        'function': HasRepr(IsStr(regex=r'<function [a-z_]*\.<locals>\.<lambda> at 0x[0-9a-fA-F]+>')),
                    },
                    'schema': {
                        'type': 'nullable',
                        'schema': {
                            'type': 'union',
                            'choices': [
                                {
                                    'type': 'typed-dict',
                                    'fields': {
                                        'kind': {
                                            'type': 'typed-dict-field',
                                            'schema': {'type': 'literal', 'expected': ['cat']},
                                        }
                                    },
                                },
                                {
                                    'type': 'typed-dict',
                                    'fields': {
                                        'kind': {
                                            'type': 'typed-dict-field',
                                            'schema': {'type': 'literal', 'expected': ['dog']},
                                        }
                                    },
                                },
                            ],
                        },
                    },
                },
            },
            'discriminator': 'kind',
            'strict': False,
            'from_attributes': True,
        },
    }


def test_union_in_submodel() -> None:
    class UnionModel1(BaseModel):
        type: Literal[1] = 1
        other: Literal['UnionModel1'] = 'UnionModel1'

    class UnionModel2(BaseModel):
        type: Literal[2] = 2
        other: Literal['UnionModel2'] = 'UnionModel2'

    UnionModel = Annotated[Union[UnionModel1, UnionModel2], Field(discriminator='type')]

    class SubModel1(BaseModel):
        union_model: UnionModel

    class SubModel2(BaseModel):
        union_model: UnionModel

    class TestModel(BaseModel):
        submodel: Union[SubModel1, SubModel2]

    m = TestModel.model_validate({'submodel': {'union_model': {'type': 1}}})
    assert isinstance(m.submodel, SubModel1)
    assert isinstance(m.submodel.union_model, UnionModel1)

    m = TestModel.model_validate({'submodel': {'union_model': {'type': 2}}})
    assert isinstance(m.submodel, SubModel1)
    assert isinstance(m.submodel.union_model, UnionModel2)

    with pytest.raises(ValidationError) as exc_info:
        TestModel.model_validate({'submodel': {'union_model': {'type': 1, 'other': 'UnionModel2'}}})

    # insert_assert(exc_info.value.errors(include_url=False))
    assert exc_info.value.errors(include_url=False) == [
        {
            'type': 'literal_error',
            'loc': ('submodel', 'SubModel1', 'union_model', 1, 'other'),
            'msg': "Input should be 'UnionModel1'",
            'input': 'UnionModel2',
            'ctx': {'expected': "'UnionModel1'"},
        },
        {
            'type': 'literal_error',
            'loc': ('submodel', 'SubModel2', 'union_model', 1, 'other'),
            'msg': "Input should be 'UnionModel1'",
            'input': 'UnionModel2',
            'ctx': {'expected': "'UnionModel1'"},
        },
    ]

    # insert_assert(TestModel.model_json_schema())
    assert TestModel.model_json_schema() == {
        '$defs': {
            'SubModel1': {
                'properties': {
                    'union_model': {
                        'discriminator': {
                            'mapping': {'1': '#/$defs/UnionModel1', '2': '#/$defs/UnionModel2'},
                            'propertyName': 'type',
                        },
                        'oneOf': [{'$ref': '#/$defs/UnionModel1'}, {'$ref': '#/$defs/UnionModel2'}],
                        'title': 'Union Model',
                    }
                },
                'required': ['union_model'],
                'title': 'SubModel1',
                'type': 'object',
            },
            'SubModel2': {
                'properties': {
                    'union_model': {
                        'discriminator': {
                            'mapping': {'1': '#/$defs/UnionModel1', '2': '#/$defs/UnionModel2'},
                            'propertyName': 'type',
                        },
                        'oneOf': [{'$ref': '#/$defs/UnionModel1'}, {'$ref': '#/$defs/UnionModel2'}],
                        'title': 'Union Model',
                    }
                },
                'required': ['union_model'],
                'title': 'SubModel2',
                'type': 'object',
            },
            'UnionModel1': {
                'properties': {
                    'type': {'const': 1, 'default': 1, 'title': 'Type'},
                    'other': {'const': 'UnionModel1', 'default': 'UnionModel1', 'title': 'Other'},
                },
                'title': 'UnionModel1',
                'type': 'object',
            },
            'UnionModel2': {
                'properties': {
                    'type': {'const': 2, 'default': 2, 'title': 'Type'},
                    'other': {'const': 'UnionModel2', 'default': 'UnionModel2', 'title': 'Other'},
                },
                'title': 'UnionModel2',
                'type': 'object',
            },
        },
        'properties': {
            'submodel': {'anyOf': [{'$ref': '#/$defs/SubModel1'}, {'$ref': '#/$defs/SubModel2'}], 'title': 'Submodel'}
        },
        'required': ['submodel'],
        'title': 'TestModel',
        'type': 'object',
    }


def test_function_after_discriminator():
    class CatModel(BaseModel):
        name: Literal['kitty', 'cat']

        @field_validator('name', mode='after')
        def replace_name(cls, v):
            return 'cat'

    class DogModel(BaseModel):
        name: Literal['puppy', 'dog']

        # comment out the 2 field validators and model will work!
        @field_validator('name', mode='after')
        def replace_name(cls, v):
            return 'dog'

    AllowedAnimal = Annotated[Union[CatModel, DogModel], Field(discriminator='name')]

    class Model(BaseModel):
        x: AllowedAnimal

    m = Model(x={'name': 'kitty'})
    assert m.x.name == 'cat'

    # Ensure a discriminated union is actually being used during validation
    with pytest.raises(ValidationError) as exc_info:
        Model(x={'name': 'invalid'})
    assert exc_info.value.errors(include_url=False) == [
        {
            'ctx': {'discriminator': "'name'", 'expected_tags': "'kitty', 'cat', 'puppy', 'dog'", 'tag': 'invalid'},
            'input': {'name': 'invalid'},
            'loc': ('x',),
            'msg': "Input tag 'invalid' found using 'name' does not match any of the "
            "expected tags: 'kitty', 'cat', 'puppy', 'dog'",
            'type': 'union_tag_invalid',
        }
    ]


def test_sequence_discriminated_union():
    class Cat(BaseModel):
        pet_type: Literal['cat']
        meows: int

    class Dog(BaseModel):
        pet_type: Literal['dog']
        barks: float

    class Lizard(BaseModel):
        pet_type: Literal['reptile', 'lizard']
        scales: bool

    Pet = Annotated[Union[Cat, Dog, Lizard], Field(discriminator='pet_type')]

    class Model(BaseModel):
        pet: Sequence[Pet]
        n: int

    assert Model.model_json_schema() == {
        '$defs': {
            'Cat': {
                'properties': {
                    'pet_type': {'const': 'cat', 'title': 'Pet Type'},
                    'meows': {'title': 'Meows', 'type': 'integer'},
                },
                'required': ['pet_type', 'meows'],
                'title': 'Cat',
                'type': 'object',
            },
            'Dog': {
                'properties': {
                    'pet_type': {'const': 'dog', 'title': 'Pet Type'},
                    'barks': {'title': 'Barks', 'type': 'number'},
                },
                'required': ['pet_type', 'barks'],
                'title': 'Dog',
                'type': 'object',
            },
            'Lizard': {
                'properties': {
                    'pet_type': {'enum': ['reptile', 'lizard'], 'title': 'Pet Type', 'type': 'string'},
                    'scales': {'title': 'Scales', 'type': 'boolean'},
                },
                'required': ['pet_type', 'scales'],
                'title': 'Lizard',
                'type': 'object',
            },
        },
        'properties': {
            'pet': {
                'items': {
                    'discriminator': {
                        'mapping': {
                            'cat': '#/$defs/Cat',
                            'dog': '#/$defs/Dog',
                            'lizard': '#/$defs/Lizard',
                            'reptile': '#/$defs/Lizard',
                        },
                        'propertyName': 'pet_type',
                    },
                    'oneOf': [{'$ref': '#/$defs/Cat'}, {'$ref': '#/$defs/Dog'}, {'$ref': '#/$defs/Lizard'}],
                },
                'title': 'Pet',
                'type': 'array',
            },
            'n': {'title': 'N', 'type': 'integer'},
        },
        'required': ['pet', 'n'],
        'title': 'Model',
        'type': 'object',
    }
