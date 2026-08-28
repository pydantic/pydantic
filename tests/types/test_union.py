from typing import Any, ClassVar, Literal, Optional, Union

import pytest
from typing_extensions import TypedDict

import pydantic
from pydantic import BaseModel, ConfigDict, TypeAdapter, model_validator


def test_field_serializer_in_nested_union_called_only_twice():
    class MyModel(BaseModel):
        a: int
        b: int

        field_a_serializer_calls: ClassVar[int] = 0

        @pydantic.field_serializer('a')
        def serialize_my_field(self, value: int) -> str:
            self.__class__.field_a_serializer_calls += 1
            return str(value)

    class Container(TypedDict):
        u: Union[MyModel, int]

    class Container2(TypedDict):
        u: Union[Container, int]

    # forcibly construct model with a False value
    value = MyModel.model_construct(a=1, b=False)
    assert value.b is False

    ta = pydantic.TypeAdapter(Union[Container2, int])
    ta.dump_json(Container2(u=Container(u=value)), warnings=False)

    # Historical implementations of pydantic would call the field serializer many times
    # as nested unions were individually attempted with each of strict and lax checking.
    #
    # 2 comes from:
    # - one attempt in strict mode, which fails because of `b=False` as a subclass
    # - one attempt in lax mode, which succeeds
    assert MyModel.field_a_serializer_calls == 2


def test_field_serializer_in_nested_tagged_union_called_only_twice():
    class MyModel(BaseModel):
        type_: Literal['a'] = 'a'

        a: int
        b: int

        field_a_serializer_calls: ClassVar[int] = 0

        @pydantic.field_serializer('a')
        def serialize_my_field(self, value: int) -> str:
            self.__class__.field_a_serializer_calls += 1
            return str(value)

    class ModelB(BaseModel):
        type_: Literal['b'] = 'b'

    class Container(BaseModel):
        type_: Literal['a'] = 'a'
        u: Union[MyModel, ModelB] = pydantic.Field(..., discriminator='type_')

    class Container2(BaseModel):
        u: Union[Container, ModelB] = pydantic.Field(..., discriminator='type_')

    # forcibly construct model with a False value
    value = MyModel.model_construct(a=1, b=False)
    assert value.b is False

    ta = pydantic.TypeAdapter(Union[Container2, int])
    ta.dump_json(Container2(u=Container(u=value)), warnings=False)

    # Historical implementations of pydantic would call the field serializer many times
    # as nested unions were individually attempted with each of strict and lax checking,
    # and the discriminators also incurred an extra attempt at each check level too.
    assert MyModel.field_a_serializer_calls == 2


def test_exclude_unset_in_nested_union():
    class Cat(BaseModel):
        type: Literal['cat']
        color: Optional[str] = None  # field with default

    class Dog(BaseModel):
        type: Literal['dog']

    class Zoo(BaseModel):
        animals: list[Union[Cat, Dog]]

    cat = Cat(type='cat')
    zoo = Zoo(animals=[cat])

    assert zoo.model_dump() == {'animals': [{'type': 'cat', 'color': None}]}
    assert cat.model_dump(exclude_unset=True) == {'type': 'cat'}
    assert zoo.model_dump(exclude_unset=True) == {'animals': [{'type': 'cat'}]}


def test_list_union_omit():
    OmitList = list[Union[pydantic.OnErrorOmit[int], pydantic.OnErrorOmit[bool]]]
    ta = pydantic.TypeAdapter(OmitList)
    assert ta.validate_python([1, 'True', 'foo', '2', False, 'bar']) == [1, True, 2, False]


def test_list_union_omit_one_member():
    OmitList = list[Union[pydantic.OnErrorOmit[int], bool]]
    ta = pydantic.TypeAdapter(OmitList)
    assert ta.validate_python([1, 'True', 'foo', '2', False, 'bar']) == [1, True, 2, False]


def test_typed_dict_union_omit():
    class TD(TypedDict):
        # arguably this should fail on schema build since `x` is a
        # required field, and setting the type to `OnErrorOmit`
        # effectively makes it optional.
        x: Union[pydantic.OnErrorOmit[int], pydantic.OnErrorOmit[bool]]

    ta = pydantic.TypeAdapter(TD)
    assert ta.validate_python({'x': 1}) == {'x': 1}
    assert ta.validate_python({'x': 'True'}) == {'x': True}

    # test to document the behaviour that if all options in the union fail,
    # the field is omitted, even if it is required in the TypedDict.
    assert ta.validate_python({'x': 'foo'}) == {}


@pytest.mark.parametrize('extra', ['ignore', 'allow'])
@pytest.mark.parametrize('reverse_members', [False, True])
def test_smart_union_fields_set_count_consistent_between_json_and_python(
    extra: Literal['ignore', 'allow'], reverse_members: bool
) -> None:
    """https://github.com/pydantic/pydantic/issues/13729"""

    class Smaller(BaseModel):
        model_config = ConfigDict(extra=extra)

        a: int
        b: int

        @model_validator(mode='before')
        @classmethod
        def keep_input(cls, value: Any) -> Any:
            return value

    class Larger(BaseModel):
        a: int
        b: int
        c: int

    ta = TypeAdapter(Union[Larger, Smaller] if reverse_members else Union[Smaller, Larger])

    assert isinstance(ta.validate_python({'a': 1, 'b': 2, 'c': 3}), Larger)
    assert isinstance(ta.validate_json('{"a": 1, "b": 2, "c": 3}'), Larger)


@pytest.mark.parametrize('reverse_members', [False, True])
def test_smart_union_fields_set_count_ignores_extra(reverse_members: bool) -> None:
    """https://github.com/pydantic/pydantic/issues/13729"""

    class WithExtra(BaseModel):
        model_config = ConfigDict(extra='allow')

        a: int

    class Explicit(BaseModel):
        a: int
        b: int

    ta = TypeAdapter(Union[Explicit, WithExtra] if reverse_members else Union[WithExtra, Explicit])

    assert isinstance(ta.validate_python({'a': 1, 'b': 2}), Explicit)
    assert isinstance(ta.validate_json('{"a": 1, "b": 2}'), Explicit)
