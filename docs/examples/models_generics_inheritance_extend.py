from typing import TypeVar, Generic
from pydantic.generics import GenericModel

TypeX = TypeVar('TypeX')
TypeY = TypeVar('TypeY')
TypeZ = TypeVar('TypeZ')


class BaseClass(GenericModel, Generic[TypeX, TypeY]):
    x: TypeX
    y: TypeY


class ChildClass(BaseClass[int, TypeY], Generic[TypeY, TypeZ]):
    z: TypeZ


# Replace TypeY by str
print(ChildClass[str, int](x=1, y='y', z=3))
