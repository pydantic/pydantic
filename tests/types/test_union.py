from abc import ABC, abstractmethod
from enum import IntEnum
from typing import Annotated, ClassVar, Literal
from uuid import UUID

import pytest
from typing_extensions import TypedDict

import pydantic
from pydantic import (
    AfterValidator,
    BaseModel,
    ConfigDict,
    Field,
    Strict,
    Tag,
    TypeAdapter,
    ValidationError,
)


def test_field_serializer_in_nested_union_called_only_twice():
    class MyModel(pydantic.BaseModel):
        a: int
        b: int

        field_a_serializer_calls: ClassVar[int] = 0

        @pydantic.field_serializer('a')
        def serialize_my_field(self, value: int) -> str:
            self.__class__.field_a_serializer_calls += 1
            return str(value)

    class Container(TypedDict):
        u: MyModel | int

    class Container2(TypedDict):
        u: Container | int

    # forcibly construct model with a False value
    value = MyModel.model_construct(a=1, b=False)
    assert value.b is False

    ta = pydantic.TypeAdapter(Container2 | int)
    ta.dump_json(Container2(u=Container(u=value)), warnings=False)

    # Historical implementations of pydantic would call the field serializer many times
    # as nested unions were individually attempted with each of strict and lax checking.
    #
    # 2 comes from:
    # - one attempt in strict mode, which fails because of `b=False` as a subclass
    # - one attempt in lax mode, which succeeds
    assert MyModel.field_a_serializer_calls == 2


def test_field_serializer_in_nested_tagged_union_called_only_twice():
    class MyModel(pydantic.BaseModel):
        type_: Literal['a'] = 'a'

        a: int
        b: int

        field_a_serializer_calls: ClassVar[int] = 0

        @pydantic.field_serializer('a')
        def serialize_my_field(self, value: int) -> str:
            self.__class__.field_a_serializer_calls += 1
            return str(value)

    class ModelB(pydantic.BaseModel):
        type_: Literal['b'] = 'b'

    class Container(pydantic.BaseModel):
        type_: Literal['a'] = 'a'
        u: MyModel | ModelB = pydantic.Field(..., discriminator='type_')

    class Container2(pydantic.BaseModel):
        u: Container | ModelB = pydantic.Field(..., discriminator='type_')

    # forcibly construct model with a False value
    value = MyModel.model_construct(a=1, b=False)
    assert value.b is False

    ta = pydantic.TypeAdapter(Container2 | int)
    ta.dump_json(Container2(u=Container(u=value)), warnings=False)

    # Historical implementations of pydantic would call the field serializer many times
    # as nested unions were individually attempted with each of strict and lax checking,
    # and the discriminators also incurred an extra attempt at each check level too.
    assert MyModel.field_a_serializer_calls == 2


def test_exclude_unset_in_nested_union():
    class Cat(pydantic.BaseModel):
        type: Literal['cat']
        color: str | None = None  # field with default

    class Dog(pydantic.BaseModel):
        type: Literal['dog']

    class Zoo(pydantic.BaseModel):
        animals: list[Cat | Dog]

    cat = Cat(type='cat')
    zoo = Zoo(animals=[cat])

    assert zoo.model_dump() == {'animals': [{'type': 'cat', 'color': None}]}
    assert cat.model_dump(exclude_unset=True) == {'type': 'cat'}
    assert zoo.model_dump(exclude_unset=True) == {'animals': [{'type': 'cat'}]}


def test_list_union_omit():
    OmitList = list[pydantic.OnErrorOmit[int] | pydantic.OnErrorOmit[bool]]
    ta = pydantic.TypeAdapter(OmitList)
    assert ta.validate_python([1, 'True', 'foo', '2', False, 'bar']) == [1, True, 2, False]


def test_list_union_omit_one_member():
    OmitList = list[pydantic.OnErrorOmit[int] | bool]
    ta = pydantic.TypeAdapter(OmitList)
    assert ta.validate_python([1, 'True', 'foo', '2', False, 'bar']) == [1, True, 2, False]


def test_typed_dict_union_omit():
    class TD(TypedDict):
        # arguably this should fail on schema build since `x` is a
        # required field, and setting the type to `OnErrorOmit`
        # effectively makes it optional.
        x: pydantic.OnErrorOmit[int] | pydantic.OnErrorOmit[bool]

    ta = pydantic.TypeAdapter(TD)
    assert ta.validate_python({'x': 1}) == {'x': 1}
    assert ta.validate_python({'x': 'True'}) == {'x': True}

    # test to document the behaviour that if all options in the union fail,
    # the field is omitted, even if it is required in the TypedDict.
    assert ta.validate_python({'x': 'foo'}) == {}


def test_default_union_types():
    class DefaultModel(BaseModel):
        v: int | bool | str

    # do it this way since `1 == True`
    assert repr(DefaultModel(v=True).v) == 'True'
    assert repr(DefaultModel(v=1).v) == '1'
    assert repr(DefaultModel(v='1').v) == "'1'"

    assert DefaultModel.model_json_schema() == {
        'title': 'DefaultModel',
        'type': 'object',
        'properties': {'v': {'title': 'V', 'anyOf': [{'type': t} for t in ('integer', 'boolean', 'string')]}},
        'required': ['v'],
    }


def test_default_union_types_left_to_right():
    class DefaultModel(BaseModel):
        v: Annotated[int | bool | str, Field(union_mode='left_to_right')]

    print(DefaultModel.__pydantic_core_schema__)

    # int will coerce everything in left-to-right mode
    assert repr(DefaultModel(v=True).v) == '1'
    assert repr(DefaultModel(v=1).v) == '1'
    assert repr(DefaultModel(v='1').v) == '1'

    assert DefaultModel.model_json_schema() == {
        'title': 'DefaultModel',
        'type': 'object',
        'properties': {'v': {'title': 'V', 'anyOf': [{'type': t} for t in ('integer', 'boolean', 'string')]}},
        'required': ['v'],
    }


def test_union_enum_int_left_to_right():
    class BinaryEnum(IntEnum):
        ZERO = 0
        ONE = 1

    # int will win over enum in this case
    assert TypeAdapter(BinaryEnum | int).validate_python(0) is not BinaryEnum.ZERO

    # in left to right mode, enum will validate successfully and take precedence
    assert (
        TypeAdapter(Annotated[BinaryEnum | int, Field(union_mode='left_to_right')]).validate_python(0)
        is BinaryEnum.ZERO
    )


def test_union_uuid_str_left_to_right():
    IdOrSlug = UUID | str

    # in smart mode JSON and python are currently validated differently in this
    # case, because in Python this is a str but in JSON a str is also a UUID
    assert TypeAdapter(IdOrSlug).validate_json('"f4fe10b4-e0c8-4232-ba26-4acd491c2414"') == UUID(
        'f4fe10b4-e0c8-4232-ba26-4acd491c2414'
    )
    assert (
        TypeAdapter(IdOrSlug).validate_python('f4fe10b4-e0c8-4232-ba26-4acd491c2414')
        == 'f4fe10b4-e0c8-4232-ba26-4acd491c2414'
    )

    IdOrSlugLTR = Annotated[UUID | str, Field(union_mode='left_to_right')]

    # in left to right mode both JSON and python are validated as UUID
    assert TypeAdapter(IdOrSlugLTR).validate_json('"f4fe10b4-e0c8-4232-ba26-4acd491c2414"') == UUID(
        'f4fe10b4-e0c8-4232-ba26-4acd491c2414'
    )
    assert TypeAdapter(IdOrSlugLTR).validate_python('f4fe10b4-e0c8-4232-ba26-4acd491c2414') == UUID(
        'f4fe10b4-e0c8-4232-ba26-4acd491c2414'
    )


def test_default_union_class():
    class A(BaseModel):
        x: str

    class B(BaseModel):
        x: str

    class Model(BaseModel):
        y: A | B

    assert isinstance(Model(y=A(x='a')).y, A)
    assert isinstance(Model(y=B(x='b')).y, B)


@pytest.mark.parametrize('max_length', [10, None])
def test_union_subclass(max_length: int | None):
    class MyStr(str): ...

    class Model(BaseModel):
        x: int | Annotated[str, Field(max_length=max_length)]

    v = Model(x=MyStr('1')).x
    assert type(v) is str
    assert v == '1'


def test_union_compound_types():
    class Model(BaseModel):
        values: dict[str, str] | list[str] | dict[str, list[str]]

    assert Model(values={'L': '1'}).model_dump() == {'values': {'L': '1'}}
    assert Model(values=['L1']).model_dump() == {'values': ['L1']}
    assert Model(values=('L1',)).model_dump() == {'values': ['L1']}
    assert Model(values={'x': ['pika']}) != {'values': {'x': ['pika']}}
    assert Model(values={'x': ('pika',)}).model_dump() == {'values': {'x': ['pika']}}
    with pytest.raises(ValidationError) as e:
        Model(values={'x': {'a': 'b'}})
    # insert_assert(e.value.errors(include_url=False))
    assert e.value.errors(include_url=False) == [
        {
            'type': 'string_type',
            'loc': ('values', 'dict[str,str]', 'x'),
            'msg': 'Input should be a valid string',
            'input': {'a': 'b'},
        },
        {
            'type': 'list_type',
            'loc': ('values', 'list[str]'),
            'msg': 'Input should be a valid list',
            'input': {'x': {'a': 'b'}},
        },
        {
            'type': 'list_type',
            'loc': ('values', 'dict[str,list[str]]', 'x'),
            'msg': 'Input should be a valid list',
            'input': {'a': 'b'},
        },
    ]


def test_smart_union_compounded_types_edge_case():
    class Model(BaseModel):
        x: list[str] | list[int]

    assert Model(x=[1, 2]).x == [1, 2]
    assert Model(x=['1', '2']).x == ['1', '2']
    assert Model(x=[1, '2']).x == [1, 2]


def test_union_typeddict():
    class Dict1(TypedDict):
        foo: str

    class Dict2(TypedDict):
        bar: str

    class M(BaseModel):
        d: Dict2 | Dict1

    assert M(d=dict(foo='baz')).d == {'foo': 'baz'}


def test_union_tags_in_errors():
    DoubledList = Annotated[list[int], AfterValidator(lambda x: x * 2)]
    StringsMap = dict[str, str]

    adapter = TypeAdapter(DoubledList | StringsMap)

    with pytest.raises(ValidationError) as exc_info:
        adapter.validate_python(['a'])

    # yuck
    assert '2 validation errors for union[function-after[<lambda>(), list[int]],dict[str,str]]' in str(exc_info)
    # the loc's are bad here:
    assert exc_info.value.errors(include_url=False) == [
        {
            'input': 'a',
            'loc': ('function-after[<lambda>(), list[int]]', 0),
            'msg': 'Input should be a valid integer, unable to parse string as an integer',
            'type': 'int_parsing',
        },
        {
            'input': ['a'],
            'loc': ('dict[str,str]',),
            'msg': 'Input should be a valid dictionary',
            'type': 'dict_type',
        },
    ]

    tag_adapter = TypeAdapter(Annotated[DoubledList, Tag('DoubledList')] | Annotated[StringsMap, Tag('StringsMap')])
    with pytest.raises(ValidationError) as exc_info:
        tag_adapter.validate_python(['a'])

    assert '2 validation errors for union[DoubledList,StringsMap]' in str(exc_info)  # nice
    # the loc's are good here:
    assert exc_info.value.errors(include_url=False) == [
        {
            'input': 'a',
            'loc': ('DoubledList', 0),
            'msg': 'Input should be a valid integer, unable to parse string as an integer',
            'type': 'int_parsing',
        },
        {
            'input': ['a'],
            'loc': ('StringsMap',),
            'msg': 'Input should be a valid dictionary',
            'type': 'dict_type',
        },
    ]


def test_union_respects_local_strict() -> None:
    class MyBaseModel(BaseModel):
        model_config = ConfigDict(strict=True)

    class Model(MyBaseModel):
        a: int | Annotated[tuple[int, int], Strict(False)] = Field(default=(1, 2))

    m = Model(a=[1, 2])
    assert m.a == (1, 2)


def test_union_abc() -> None:
    """https://github.com/pydantic/pydantic/issues/12230"""

    class ABC_1(BaseModel, ABC):
        @abstractmethod
        def do_something(self):
            pass

    class ABC_2(BaseModel, ABC):
        @abstractmethod
        def do_something_else(self):
            pass

    class A1(ABC_1):
        def do_something(self):
            print('Doing something in A1')

    class A2(ABC_2):
        def do_something_else(self):
            print('Doing something else in A2')

    class X(BaseModel):
        x: ABC_1 | ABC_2

    a1 = A1()
    a2 = A2()

    X(x=a1)
    X(x=a2)
