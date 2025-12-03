from typing import ClassVar, Literal, TypedDict

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
        u: MyModel | int

    class Container2(TypedDict):
        u: Container | int

    value = MyModel(a=1, b=False)
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

    ta = pydantic.TypeAdapter(Container2 | int)
    ta.dump_json(Container2(u=Container(u=MyModel.model_construct(a=1, b=False))), warnings=False)

    # Historical implementations of pydantic would call the field serializer many MANY times
    # as nested unions were individually attempted with each of strict and lax checking.
    #
    # 5 comes from:
    # - tagged discriminator in outer union at strict mode
    # - fall back to left to right in outer union at strict mode
    # - tagged discriminator in inner union at strict mode
    # - fall back to left to right in inner union still at strict mode
    # - tagged discriminator in outer union at lax mode, which calls tagged discriminator in inner union at lax mode, which finally succeeds
    assert MyModel.field_a_serializer_calls == 5
