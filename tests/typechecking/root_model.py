from typing import Any

from typing_extensions import assert_type

from pydantic import BaseModel, RootModel, SerializationInfo, model_serializer

IntRootModel = RootModel[int]

int_root_model = IntRootModel(1)
bad_root_model = IntRootModel('1')  # type: ignore[arg-type]  # pyright: ignore[reportArgumentType]

assert_type(int_root_model.root, int)


class StrRootModel(RootModel[str]):
    pass


str_root_model = StrRootModel(root='a')

assert_type(str_root_model.root, str)


class ContextRoot(RootModel[str]):
    @model_serializer
    def serialize_root(self, info: SerializationInfo) -> str:
        return f'{info.context}:{self.root}'


class Unknown:
    pass


class Base(BaseModel):
    x: int


class Sub(Base):
    y: int


ContextRoot(root='value').model_dump(context='prefix')

RootModel[Any](root=Unknown()).model_dump(
    mode='json',
    fallback=lambda _: 'fallback',
)

RootModel[list[Base]](root=[Sub(x=1, y=2)]).model_dump(
    polymorphic_serialization=True,
)
