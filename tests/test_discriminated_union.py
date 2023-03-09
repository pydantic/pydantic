import re
import sys
from enum import Enum, IntEnum
from typing import Generic, TypeVar, Union

import pytest
from typing_extensions import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field, ValidationError
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

    with pytest.raises(PydanticUserError, match="Field 'pet_type' of model 'Cat' needs to be a `Literal`"):

        class Model(BaseModel):
            pet: Union[Cat, Dog] = Field(..., discriminator='pet_type')
            number: int


@pytest.mark.xfail(reason='working on V2 - __root__')
def test_discriminated_union_root_same_discriminator():
    class BlackCat(BaseModel):
        pet_type: Literal['blackcat']

    class WhiteCat(BaseModel):
        pet_type: Literal['whitecat']

    class Cat(BaseModel):
        __root__: Union[BlackCat, WhiteCat]

    class Dog(BaseModel):
        pet_type: Literal['dog']

    with pytest.raises(PydanticUserError, match="Field 'pet_type' is not the same for all submodels of 'Cat'"):

        class Pet(BaseModel):
            __root__: Union[Cat, Dog] = Field(..., discriminator='pet_type')


@pytest.mark.xfail(reason='working on V2 - __root__')
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
        m: str

    class Model(BaseModel):
        pet: Annotated[Union[Cat, Dog, Lizard], Field(discriminator='pet_type')]
        number: int

    with pytest.raises(ValidationError) as exc_info:
        Model.model_validate({'pet': {'pet_typ': 'cat'}, 'number': 'x'})
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
        Model.model_validate({'pet': 'fish', 'number': 2})
    assert exc_info.value.errors() == [
        {
            'loc': ('pet',),
            'msg': "Discriminator 'pet_type' is missing in value",
            'type': 'value_error.discriminated_union.missing_discriminator',
            'ctx': {'discriminator_key': 'pet_type'},
        },
    ]

    with pytest.raises(ValidationError) as exc_info:
        Model.model_validate({'pet': {'pet_type': 'fish'}, 'number': 2})
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
        Model.model_validate({'pet': {'pet_type': 'lizard'}, 'number': 2})
    assert exc_info.value.errors() == [
        {'loc': ('pet', 'Lizard', 'l'), 'msg': 'field required', 'type': 'value_error.missing'},
    ]

    m = Model.model_validate({'pet': {'pet_type': 'lizard', 'l': 'pika'}, 'number': 2})
    assert isinstance(m.pet, Lizard)
    assert m.model_dump() == {'pet': {'pet_type': 'lizard', 'l': 'pika'}, 'number': 2}

    with pytest.raises(ValidationError) as exc_info:
        Model.model_validate({'pet': {'pet_type': 'cat', 'color': 'white'}, 'number': 2})
    assert exc_info.value.errors() == [
        {
            'loc': ('pet', 'Cat', '__root__', 'WhiteCat', 'white_infos'),
            'msg': 'field required',
            'type': 'value_error.missing',
        }
    ]
    m = Model.model_validate({'pet': {'pet_type': 'cat', 'color': 'white', 'white_infos': 'pika'}, 'number': 2})
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
        Model.model_validate({'pet': {'pet_typ': 'cat'}, 'number': 'x'})
    assert exc_info.value.errors() == [
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
    assert exc_info.value.errors() == [
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
    assert exc_info.value.errors() == [
        {'input': {'pet_type': 'dog'}, 'loc': ('pet', 'dog', 'dog_name'), 'msg': 'Field required', 'type': 'missing'}
    ]
    m = Model.model_validate({'pet': {'pet_type': 'dog', 'dog_name': 'milou'}, 'number': 2})
    assert isinstance(m.pet, Dog)

    with pytest.raises(ValidationError) as exc_info:
        Model.model_validate({'pet': {'pet_type': 'cat', 'color': 'red'}, 'number': 2})
    assert exc_info.value.errors() == [
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
    assert exc_info.value.errors() == [
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
    assert exc_info.value.errors() == [
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
    pytest.param(Enum, {'a': 1, 'b': 2}, marks=pytest.mark.xfail(reason='Plain Enum not yet supported')),
    pytest.param(Enum, {'a': 'v_a', 'b': 'v_b'}, marks=pytest.mark.xfail(reason='Plain Enum not yet supported')),
    (FooIntEnum, {'a': 1, 'b': 2}),
    (IntEnum, {'a': 1, 'b': 2}),
    (FooStrEnum, {'a': 'v_a', 'b': 'v_b'}),
]
if sys.version_info >= (3, 11):
    from enum import StrEnum

    ENUM_TEST_CASES.append((StrEnum, {'a': 'v_a', 'b': 'v_b'}))


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
    assert exc_info.value.errors() == [
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

    class Model(BaseModel):
        pet: Union[Cat, Dog] = Field(discriminator='pet_type')

    Model.model_validate({'pet': {'U': 'cat', 'c': 'my_cat'}})
    Model.model_validate({'pet': {'T': 'dog', 'd': 'my_dog'}})
    with pytest.raises(ValidationError) as exc_info:
        Model.model_validate({'pet': {'W': 'dog', 'd': 'my_dog'}})
    assert exc_info.value.errors() == [
        {
            'ctx': {'discriminator': "'pet_type' | 'U' | 'T'"},
            'input': {'W': 'dog', 'd': 'my_dog'},
            'loc': ('pet',),
            'msg': "Unable to extract tag using discriminator 'pet_type' | 'U' | 'T'",
            'type': 'union_tag_not_found',
        }
    ]


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

    # See https://github.com/pydantic/pydantic-core/issues/425 for why this is set weirdly; this is an unrelated issue
    # If/when the issue is fixed, the following line should replace the current title = 'Failure' line
    # title = 'Container[str]'
    title = 'Failure'

    with pytest.raises(ValidationError, match=f'{title}\nresult -> Success -> data') as exc_info:
        Container[str].model_validate({'result': {'type': 'Success'}})
    assert exc_info.value.errors() == [
        {'input': {'type': 'Success'}, 'loc': ('result', 'Success', 'data'), 'msg': 'Field required', 'type': 'missing'}
    ]

    # invalid types error
    with pytest.raises(ValidationError) as exc_info:
        Container[str].model_validate({'result': {'type': 'Success', 'data': 1}})
    assert exc_info.value.errors() == [
        {
            'input': 1,
            'loc': ('result', 'Success', 'data'),
            'msg': 'Input should be a valid string',
            'type': 'string_type',
        }
    ]

    assert Container[str].model_validate({'result': {'type': 'Success', 'data': '1'}}).result.data == '1'
