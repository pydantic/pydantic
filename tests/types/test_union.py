from typing import ClassVar, Literal, Union

import pytest
from typing_extensions import TypedDict

import pydantic


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
        u: Union[MyModel, ModelB] = pydantic.Field(..., discriminator='type_')

    class Container2(pydantic.BaseModel):
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


def test_list_union_omit():
    OmitList = list[Union[pydantic.OnErrorOmit[int], pydantic.OnErrorOmit[bool]]]
    with pytest.warns(UserWarning, match='^Using OnErrorOmit within a Union is not recommended'):
        ta = pydantic.TypeAdapter(OmitList)
    assert ta.validate_python([1, 'True', 'foo', '2', False, 'bar']) == [1, True, 2, False]


def test_list_union_omit_one_member():
    OmitList = list[Union[pydantic.OnErrorOmit[int], bool]]
    with pytest.warns(UserWarning, match='^Mixing OnErrorOmit schemas with non-omittable schemas'):
        ta = pydantic.TypeAdapter(OmitList)
    assert ta.validate_python([1, 'True', 'foo', '2', False, 'bar']) == [1, True, 2, False]


def test_typed_dict_union_omit():
    class TD(TypedDict):
        # arguably this should fail on schema build since `x` is a
        # required field, and setting the type to `OnErrorOmit`
        # effectively makes it optional.
        x: Union[pydantic.OnErrorOmit[int], pydantic.OnErrorOmit[bool]]

    with pytest.warns(UserWarning, match='^Using OnErrorOmit within a Union is not recommended'):
        ta = pydantic.TypeAdapter(TD)
    assert ta.validate_python({'x': 1}) == {'x': 1}
    assert ta.validate_python({'x': 'True'}) == {'x': True}

    # test to document the behaviour that if all options in the union fail,
    # the field is omitted, even if it is required in the TypedDict.
    assert ta.validate_python({'x': 'foo'}) == {}
